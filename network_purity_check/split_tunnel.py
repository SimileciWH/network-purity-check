import ipaddress
import re
import urllib.request

DOMESTIC_SOURCE = "https://myip.ipip.net"


_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def detect_domestic_egress_ip(timeout: float) -> str:
    req = urllib.request.Request(DOMESTIC_SOURCE, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        text = resp.read(512).decode("utf-8", errors="ignore")

    for candidate in _IP_RE.findall(text):
        try:
            ipaddress.ip_address(candidate)
            return candidate
        except ValueError:
            continue

    raise RuntimeError("failed to parse domestic egress ip")


def detect_split_tunnel(overseas_ip: str, timeout: float) -> tuple[bool, bool, str]:
    domestic_ip = detect_domestic_egress_ip(timeout=timeout)
    return domestic_ip != overseas_ip, True, domestic_ip
