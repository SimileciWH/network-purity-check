import random
import socket
import struct
from dataclasses import dataclass

from .metadata import lookup_country_by_ip


@dataclass(slots=True)
class DNSResult:
    dns_ip: str = ""
    dns_country: str = ""
    dns_leak: bool = False


def _build_dns_query() -> bytes:
    txid = random.randint(0, 0xFFFF)
    flags = 0x0100
    qdcount = 1
    header = struct.pack("!HHHHHH", txid, flags, qdcount, 0, 0, 0)

    parts = "myip.opendns.com".split(".")
    qname = b"".join(bytes([len(p)]) + p.encode("ascii") for p in parts) + b"\x00"
    qtype = 1
    qclass = 1
    question = qname + struct.pack("!HH", qtype, qclass)
    return header + question


def _skip_name(msg: bytes, offset: int) -> int:
    while offset < len(msg):
        length = msg[offset]
        if length == 0:
            return offset + 1
        if (length & 0xC0) == 0xC0:
            return offset + 2
        offset += 1 + length
    return offset


def _query_opendns(timeout: float) -> str:
    query = _build_dns_query()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(query, ("resolver1.opendns.com", 53))
        data, _ = sock.recvfrom(512)

    if len(data) < 12:
        raise RuntimeError("dns response too short")

    qdcount = struct.unpack("!H", data[4:6])[0]
    ancount = struct.unpack("!H", data[6:8])[0]

    offset = 12
    for _ in range(qdcount):
        offset = _skip_name(data, offset)
        offset += 4

    for _ in range(ancount):
        offset = _skip_name(data, offset)
        if offset + 10 > len(data):
            break
        rtype, rclass, _ttl, rdlength = struct.unpack("!HHIH", data[offset : offset + 10])
        offset += 10
        if offset + rdlength > len(data):
            break
        rdata = data[offset : offset + rdlength]
        offset += rdlength

        if rtype == 1 and rclass == 1 and rdlength == 4:
            return socket.inet_ntoa(rdata)

    raise RuntimeError("A record not found from OpenDNS")


def detect_dns_leak(ip_country: str, timeout: float) -> DNSResult:
    dns_ip = _query_opendns(timeout)
    dns_country = lookup_country_by_ip(dns_ip, timeout)
    return DNSResult(
        dns_ip=dns_ip,
        dns_country=dns_country,
        dns_leak=bool(dns_country and ip_country and dns_country != ip_country),
    )
