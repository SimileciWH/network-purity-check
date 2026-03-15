import os

DEFAULT_BLOCKED_COUNTRIES = {
    "BY",
    "CN",
    "CU",
    "IR",
    "KP",
    "RU",
    "SY",
}


def _parse_country_set(raw: str) -> set[str]:
    out: set[str] = set()
    for token in raw.split(","):
        code = token.strip().upper()
        if code:
            out.add(code)
    return out


def is_claude_supported_country(country: str) -> bool:
    code = (country or "").strip().upper()
    if not code:
        return False

    allowed_raw = os.getenv("CLAUDE_ALLOWED_COUNTRIES", "").strip()
    if allowed_raw:
        return code in _parse_country_set(allowed_raw)

    return code not in DEFAULT_BLOCKED_COUNTRIES
