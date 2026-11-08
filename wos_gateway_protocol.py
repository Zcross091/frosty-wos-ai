"""
❄️ Whiteout Survival Gateway Protocol & Network Telemetry Engine
Reverse-Engineered Architecture (REA) for Century Games Game Gateways,
Socket Packet Framing, and iLiveData Real-Time Messaging Infrastructure.
"""

import struct
import socket
import time
import asyncio
import logging
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger("WosGatewayProtocol")

# --- Known Whiteout Survival Gateways ---
DEFAULT_GATEWAYS = [
    {
        "id": "cf_edge",
        "name": "Cloudflare Edge Gateway",
        "host": "gof-login-formal-cf.centurygame.com",
        "port": 30101,
        "protocol": "TCP",
        "provider": "Cloudflare Edge",
        "region": "Global (Low Latency)",
        "priority": 1,
    },
    {
        "id": "akamai_cdn",
        "name": "Akamai CDN Gateway",
        "host": "gof-login-formal-aka.centurygame.com",
        "port": 30101,
        "protocol": "TCP",
        "provider": "Akamai CDN",
        "region": "Global / APAC",
        "priority": 2,
    },
    {
        "id": "ilivedata_rtm",
        "name": "iLiveData Chat Frontgate",
        "host": "rtm-intl-frontgate.ilivedata.com",
        "port": 13321,
        "protocol": "TCP/TLS",
        "provider": "iLiveData",
        "region": "World/Alliance Chat Push",
        "priority": 3,
    },
    {
        "id": "ilivedata_ga",
        "name": "iLiveData Accelerated Frontgate",
        "host": "ga-rtm-intl-frontgate.ilivedata.com",
        "port": 13321,
        "protocol": "TCP/TLS",
        "provider": "iLiveData",
        "region": "Western/EU RTM Relay",
        "priority": 4,
    },
    {
        "id": "cgc_web_auth",
        "name": "Century Games Web Auth",
        "host": "auth.centurygame.com",
        "port": 443,
        "protocol": "HTTPS",
        "provider": "Century Games",
        "region": "Portal Authentication",
        "priority": 5,
    },
]

# --- Protocol Constants & Opcodes ---
OPCODE_PING = bytes([0x55, 0x02])
OPCODE_PONG = bytes([0x55, 0x02])
OPCODE_ALLIANCE_BROADCAST = bytes([0x1d, 0x01])
OPCODE_ALLIANCE_HELP_QUERY = bytes([0x5d, 0x02])
OPCODE_QUICK_HELP = bytes([0x1d, 0x02])

# Standard raw ping packet: Length (4 bytes) + Opcode 0x5502 + 0x0000
RAW_PING_PACKET = bytes([0x00, 0x04, 0x55, 0x02, 0x00, 0x00])
# Expected pong payload sub-cmd
RAW_PONG_SUB = bytes([0x00, 0x01])


@dataclass
class GatewayHealthResult:
    id: str
    name: str
    host: str
    port: int
    provider: str
    region: str
    online: bool
    latency_ms: float
    error: Optional[str] = None


class WosPacketCodec:
    """
    Binary packet encoder and decoder for Whiteout Survival's 2-byte Big-Endian
    length-prefixed TCP socket stream.
    """

    @staticmethod
    def encode_frame(opcode: bytes, payload: bytes = b"", seq: Optional[int] = None) -> bytes:
        """
        Encodes a packet into: [2-byte Length BE] + [2-byte Opcode] + [Payload]
        Total length in header = len(opcode) + len(payload)
        """
        data = bytearray(opcode)
        if seq is not None:
            # Monotonic even sequence byte
            data.append(seq & 0xFE)
        data.extend(payload)

        length = len(data)
        header = struct.pack(">H", length)
        return header + data

    @staticmethod
    def decode_frame(buffer: bytes) -> Optional[Tuple[int, bytes, bytes, int]]:
        """
        Decodes a frame from raw buffer.
        Returns: (frame_length, opcode, payload, total_bytes_consumed) or None if incomplete.
        """
        if len(buffer) < 2:
            return None

        (frame_len,) = struct.unpack(">H", buffer[:2])
        total_packet_len = frame_len + 2

        if len(buffer) < total_packet_len:
            return None  # Incomplete frame, await more bytes

        opcode = buffer[2:4] if frame_len >= 2 else b""
        payload = buffer[4:total_packet_len] if frame_len > 2 else b""
        return frame_len, opcode, payload, total_packet_len

    @staticmethod
    def next_client_sequence(server_seq: int) -> int:
        """
        Computes the strictly monotonic even sequence byte:
        clientSeq = (serverSeq + 2) & 0xFE
        """
        return (server_seq + 2) & 0xFE


async def probe_gateway_endpoint(gateway: Dict[str, Any], timeout: float = 3.5) -> GatewayHealthResult:
    """
    Probes an individual Whiteout Survival gateway for TCP handshake latency and reachability.
    """
    host = gateway["host"]
    port = gateway["port"]
    gid = gateway["id"]
    name = gateway["name"]
    provider = gateway.get("provider", "Century Games")
    region = gateway.get("region", "Global")

    t0 = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        latency = (time.perf_counter() - t0) * 1000.0
        writer.close()
        await writer.wait_closed()

        return GatewayHealthResult(
            id=gid,
            name=name,
            host=host,
            port=port,
            provider=provider,
            region=region,
            online=True,
            latency_ms=round(latency, 1),
            error=None
        )
    except asyncio.TimeoutError:
        return GatewayHealthResult(
            id=gid,
            name=name,
            host=host,
            port=port,
            provider=provider,
            region=region,
            online=False,
            latency_ms=0.0,
            error="Connection timed out"
        )
    except Exception as e:
        return GatewayHealthResult(
            id=gid,
            name=name,
            host=host,
            port=port,
            provider=provider,
            region=region,
            online=False,
            latency_ms=0.0,
            error=str(e)
        )


async def probe_all_gateways(timeout: float = 3.5) -> List[GatewayHealthResult]:
    """
    Concurrently probes all primary Whiteout Survival game gateways, chat frontgates,
    and auth endpoints.
    """
    tasks = [probe_gateway_endpoint(gw, timeout=timeout) for gw in DEFAULT_GATEWAYS]
    results = await asyncio.gather(*tasks)
    # Sort: online first, then by latency
    return sorted(results, key=lambda r: (not r.online, r.latency_ms))
