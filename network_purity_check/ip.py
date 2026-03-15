import ipaddress
import urllib.request
from collections import Counter
from typing import Dict, Tuple

IP_SOURCES = (
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://ipinfo.io/ip",
)


def _fetch_ip(url: str, timeout: float) -> str:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read(128).decode("utf-8", errors="ignore").strip()
    ipaddress.ip_address(body)
    return body


def detect_public_ip(timeout: float, verbose: bool = False) -> Tuple[str, Dict[str, str]]:
    responses: Dict[str, str] = {}
    for source in IP_SOURCES:
        try:
            responses[source] = _fetch_ip(source, timeout)
        except Exception as exc:  # noqa: BLE001
            if verbose:
                print(f"[debug] ip source failed: {source}, err={exc}")

    if not responses:
        raise RuntimeError("failed to detect public ip from all sources")

    counts = Counter(responses.values())
    majority_ip = counts.most_common(1)[0][0]
    return majority_ip, responses


def verify_ip_consistency(timeout: float, verbose: bool = False) -> Tuple[bool, Dict[str, str]]:
    _, responses = detect_public_ip(timeout=timeout, verbose=verbose)
    return len(set(responses.values())) <= 1, responses
