import ipaddress
import re
import urllib.request

DOMESTIC_SOURCES = (
    "https://myip.ipip.net",
    "https://2023.ip138.com/",
    "https://ip.cn/api/index?ip=&type=0",
)


_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def _extract_ip(text: str) -> str:
    for candidate in _IP_RE.findall(text):
        try:
            ipaddress.ip_address(candidate)
            return candidate
        except ValueError:
            continue
    raise RuntimeError("failed to parse domestic egress ip")


def _fetch_from_source(source: str, timeout: float) -> str:
    req = urllib.request.Request(
        source,
        headers={"User-Agent": "network-purity-check/0.1"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        text = resp.read(1024).decode("utf-8", errors="ignore")
    return _extract_ip(text)


def detect_domestic_egress_ip(timeout: float) -> tuple[str, str]:
    errors: list[str] = []
    for source in DOMESTIC_SOURCES:
        for _ in range(2):
            try:
                return _fetch_from_source(source=source, timeout=timeout), source
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{source}: {exc}")
                continue
    raise RuntimeError("; ".join(errors))


def detect_split_tunnel(overseas_ip: str, timeout: float) -> tuple[bool, bool, str, str]:
    domestic_ip, source = detect_domestic_egress_ip(timeout=timeout)
    return domestic_ip != overseas_ip, True, domestic_ip, source
