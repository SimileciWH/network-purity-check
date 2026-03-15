import json
import urllib.request
from dataclasses import dataclass


@dataclass(slots=True)
class IPInfo:
    ip: str = ""
    country: str = ""
    region: str = ""
    city: str = ""
    org: str = ""


def fetch_ip_metadata(ip: str, timeout: float) -> IPInfo:
    url = f"https://ipinfo.io/{ip}/json"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="ignore"))

    return IPInfo(
        ip=data.get("ip", ""),
        country=data.get("country", ""),
        region=data.get("region", ""),
        city=data.get("city", ""),
        org=data.get("org", ""),
    )


def lookup_country_by_ip(ip: str, timeout: float) -> str:
    url = f"https://ipinfo.io/{ip}/country"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(16).decode("utf-8", errors="ignore").strip().upper()
