import argparse
import os
import sys

from .asn import classify_asn
from .dns_check import DNSResult, detect_dns_leak
from .ip import detect_public_ip, verify_ip_consistency
from .metadata import fetch_ip_metadata
from .output import Report, print_json, print_text
from .policy import is_claude_supported_country
from .reputation import check_ip_reputation
from .scoring import ScoreInput, calculate_score
from .split_tunnel import detect_split_tunnel
from .webrtc import WebRTCResult, detect_webrtc_leak


def _format_map(data: dict[str, str]) -> str:
    return ",".join(f"{k}={v}" for k, v in data.items()) if data else ""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="network-purity-check")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="run network purity detection")
    run_parser.add_argument("--json", action="store_true", dest="json_out", help="output JSON")
    run_parser.add_argument("--verbose", action="store_true", help="print debug information")
    run_parser.add_argument("--timeout", type=float, default=5.0, help="API timeout in seconds")

    return parser


def run_command(json_out: bool, verbose: bool, timeout: float) -> int:
    if timeout <= 0:
        print("error: timeout must be > 0", file=sys.stderr)
        return 2

    ip, ip_sources = detect_public_ip(timeout=timeout, verbose=verbose)
    metadata = fetch_ip_metadata(ip=ip, timeout=timeout)

    asn_type = classify_asn(metadata.org)
    rep = check_ip_reputation(ip=ip, timeout=timeout, verbose=verbose)

    dns_check_ok = True
    try:
        dns_result = detect_dns_leak(ip_country=metadata.country, timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        dns_check_ok = False
        dns_result = DNSResult()
        if verbose:
            print(f"[debug] dns leak detection failed: {exc}")

    webrtc_check_ok = True
    try:
        webrtc_result = detect_webrtc_leak(timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        webrtc_check_ok = False
        webrtc_result = WebRTCResult()
        if verbose:
            print(f"[debug] webrtc detection failed: {exc}")

    try:
        ip_consistency, consistency_raw = verify_ip_consistency(timeout=timeout, verbose=False)
    except Exception as exc:  # noqa: BLE001
        ip_consistency, consistency_raw = False, {}
        if verbose:
            print(f"[debug] ip consistency check failed: {exc}")

    split_check_ok = True
    domestic_egress_ip = ""
    split_tunnel = False
    try:
        split_tunnel, split_check_ok, domestic_egress_ip = detect_split_tunnel(overseas_ip=ip, timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        split_check_ok = False
        if verbose:
            print(f"[debug] split tunnel detection failed: {exc}")

    country_mismatch = bool(dns_result.dns_country and metadata.country and dns_result.dns_country != metadata.country)
    claude_supported = is_claude_supported_country(metadata.country)

    score, status = calculate_score(
        ScoreInput(
            asn_type=asn_type,
            fraud_score=rep.fraud_score,
            dns_leak=dns_result.dns_leak,
            webrtc_leak=webrtc_result.webrtc_leak,
            dns_check_ok=dns_check_ok,
            webrtc_check_ok=webrtc_check_ok,
            country_mismatch=country_mismatch,
            ip_consistency=ip_consistency,
            claude_supported=claude_supported,
            split_tunnel=split_tunnel,
            split_check_ok=split_check_ok,
        )
    )

    report = Report(
        ip=ip,
        country=metadata.country,
        target="claude",
        claude_supported=claude_supported,
        asn=metadata.org,
        asn_type=asn_type,
        fraud_score=rep.fraud_score,
        dns_country=dns_result.dns_country,
        dns_check_ok=dns_check_ok,
        webrtc_leak=webrtc_result.webrtc_leak,
        webrtc_check_ok=webrtc_check_ok,
        ip_consistency=ip_consistency,
        split_tunnel=split_tunnel,
        split_check_ok=split_check_ok,
        domestic_egress_ip=domestic_egress_ip,
        purity_score=score,
        status=status,
    )

    if verbose:
        report.debug = {
            "ip_sources": _format_map(ip_sources),
            "consistency_ip": _format_map(consistency_raw),
            "stun_public_ip": webrtc_result.stun_public_ip,
            "dns_check_ok": str(dns_check_ok).lower(),
            "webrtc_check_ok": str(webrtc_check_ok).lower(),
            "split_check_ok": str(split_check_ok).lower(),
            "split_tunnel": str(split_tunnel).lower(),
            "domestic_egress_ip": domestic_egress_ip,
            "claude_supported": str(claude_supported).lower(),
            "allowed_countries": os.getenv("CLAUDE_ALLOWED_COUNTRIES", ""),
        }

    if json_out:
        print_json(report)
    else:
        print_text(report)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command != "run":
        parser.print_help()
        return 2

    try:
        return run_command(json_out=args.json_out, verbose=args.verbose, timeout=args.timeout)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
