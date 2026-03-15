from dataclasses import dataclass


@dataclass(slots=True)
class ScoreInput:
    asn_type: str
    fraud_score: int
    dns_leak: bool
    webrtc_leak: bool
    dns_check_ok: bool
    webrtc_check_ok: bool
    country_mismatch: bool
    ip_consistency: bool
    claude_supported: bool


def calculate_score(inp: ScoreInput) -> tuple[int, str]:
    score = 100
    if not inp.claude_supported:
        score -= 80
    if inp.asn_type == "datacenter":
        score -= 40
    elif inp.asn_type == "unknown":
        score -= 10

    if inp.fraud_score > 30:
        score -= 30
    elif inp.fraud_score > 0:
        score -= 10

    if inp.dns_leak:
        score -= 20
    if inp.webrtc_leak:
        score -= 10
    if not inp.dns_check_ok:
        score -= 20
    if not inp.webrtc_check_ok:
        score -= 10
    if inp.country_mismatch:
        score -= 35
    if not inp.ip_consistency:
        score -= 40

    score = max(0, score)
    if score >= 85:
        return score, "clean"
    if score >= 70:
        return score, "acceptable"
    return score, "risky"
