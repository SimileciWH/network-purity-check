import json
from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class Report:
    ip: str
    country: str
    target: str
    claude_supported: bool
    asn: str
    asn_type: str
    fraud_score: int
    dns_country: str
    dns_check_ok: bool
    webrtc_leak: bool
    webrtc_check_ok: bool
    ip_consistency: bool
    split_tunnel: bool
    split_check_ok: bool
    domestic_egress_ip: str
    purity_score: int
    status: str
    debug: dict[str, str] = field(default_factory=dict)


_STATUS_MAP = {
    "clean": "CLEAN",
    "acceptable": "ACCEPTABLE",
    "risky": "RISKY",
}


def print_text(report: Report) -> None:
    print("Network Purity Report")
    print()
    print(f"Public IP: {report.ip}")
    print(f"Country: {report.country}")
    print(f"Target: {report.target}")
    print(f"Claude Supported: {str(report.claude_supported).lower()}")
    print(f"ASN: {report.asn}")
    print(f"ASN Type: {report.asn_type}")
    print(f"Fraud Score: {report.fraud_score}")
    print(f"DNS Country: {report.dns_country}")
    print(f"DNS Check OK: {str(report.dns_check_ok).lower()}")
    print(f"WebRTC Leak: {str(report.webrtc_leak).lower()}")
    print(f"WebRTC Check OK: {str(report.webrtc_check_ok).lower()}")
    print(f"IP Consistency: {str(report.ip_consistency).lower()}")
    print(f"Split Tunnel: {str(report.split_tunnel).lower()}")
    print(f"Split Check OK: {str(report.split_check_ok).lower()}")
    print(f"Domestic Egress IP: {report.domestic_egress_ip}")
    print()
    print(f"Purity Score: {report.purity_score}")
    print(f"Status: {_STATUS_MAP.get(report.status, 'RISKY')}")

    if report.debug:
        print()
        print("Debug:")
        for key in sorted(report.debug):
            print(f"- {key}: {report.debug[key]}")


def print_json(report: Report) -> None:
    data = asdict(report)
    if not data["debug"]:
        data.pop("debug", None)
    print(json.dumps(data, ensure_ascii=False, indent=1))
