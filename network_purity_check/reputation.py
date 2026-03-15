import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass(slots=True)
class ReputationResult:
    fraud_score: int = 0
    proxy: bool = False
    vpn: bool = False
    tor: bool = False


def _to_int(value) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes"}
    return False


def check_ip_reputation(ip: str, timeout: float, verbose: bool = False) -> ReputationResult:
    api_key = os.getenv("APIVOID_API_KEY", "").strip()
    if not api_key:
        if verbose:
            print("[debug] APIVOID_API_KEY is not set, fallback fraud_score=0")
        return ReputationResult(fraud_score=0)

    params = urllib.parse.urlencode({"key": api_key, "ip": ip})
    url = f"https://endpoint.apivoid.com/iprep/v1/pay-as-you-go/?{params}"

    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8", errors="ignore"))

    report = (((payload.get("data") or {}).get("report")) or {})
    blacklists = report.get("blacklists") or {}
    detections = _to_int(blacklists.get("detections"))

    fraud_score = min(detections * 8, 100)
    return ReputationResult(
        fraud_score=fraud_score,
        proxy=_to_bool(report.get("is_proxy")),
        vpn=_to_bool(report.get("is_vpn")),
        tor=_to_bool(report.get("is_tor")),
    )
