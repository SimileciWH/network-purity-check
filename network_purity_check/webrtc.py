import ipaddress
import os
import random
import socket
import struct
from dataclasses import dataclass


@dataclass(slots=True)
class WebRTCResult:
    stun_public_ip: str = ""
    has_private_ip: bool = False
    webrtc_leak: bool = False


def _query_stun(timeout: float) -> str:
    message_type = 0x0001
    message_length = 0
    magic_cookie = 0x2112A442
    transaction_id = os.urandom(12)
    request = struct.pack("!HHI", message_type, message_length, magic_cookie) + transaction_id

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(request, ("stun.l.google.com", 19302))
        data, _ = sock.recvfrom(1024)

    if len(data) < 20:
        raise RuntimeError("stun response too short")

    cookie_bytes = struct.pack("!I", magic_cookie)
    offset = 20
    while offset + 4 <= len(data):
        attr_type, attr_len = struct.unpack("!HH", data[offset : offset + 4])
        start = offset + 4
        end = start + attr_len
        if end > len(data):
            break

        value = data[start:end]
        if attr_type == 0x0020 and attr_len >= 8:
            family = value[1]
            if family == 0x01 and attr_len >= 8:
                xip = bytearray(value[4:8])
                for i in range(4):
                    xip[i] ^= cookie_bytes[i]
                return str(ipaddress.IPv4Address(bytes(xip)))
            if family == 0x02 and attr_len >= 20:
                xip = bytearray(value[4:20])
                mask = cookie_bytes + transaction_id
                for i in range(16):
                    xip[i] ^= mask[i]
                return str(ipaddress.IPv6Address(bytes(xip)))

        offset = end + ((4 - (attr_len % 4)) % 4)

    raise RuntimeError("xor-mapped-address not found")


def _has_private_ip() -> bool:
    for family, _, _, _, sockaddr in socket.getaddrinfo(socket.gethostname(), None):
        if family == socket.AF_INET:
            ip = ipaddress.ip_address(sockaddr[0])
            if not ip.is_loopback and ip.is_private:
                return True
        if family == socket.AF_INET6:
            ip = ipaddress.ip_address(sockaddr[0])
            if not ip.is_loopback and ip.is_private:
                return True
    return False


def detect_webrtc_leak(timeout: float) -> WebRTCResult:
    stun_public_ip = _query_stun(timeout)
    has_private_ip = _has_private_ip()
    return WebRTCResult(
        stun_public_ip=stun_public_ip,
        has_private_ip=has_private_ip,
        webrtc_leak=has_private_ip,
    )
