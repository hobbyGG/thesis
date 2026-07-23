import socket
import struct
import threading

import netifaces
import pytest

import mmwavecapture.dca1000 as dca1000


def unused_udp_port(host):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((host, 0))
        return sock.getsockname()[1]
    finally:
        sock.close()


def non_loopback_ipv4():
    for interface in netifaces.interfaces():
        for address in netifaces.ifaddresses(interface).get(netifaces.AF_INET, []):
            ip = address.get("addr")
            if ip and not ip.startswith("127."):
                return ip
    pytest.skip("no non-loopback IPv4 address is available for UDP integration test")


def test_dca_command_round_trip_over_real_loopback_udp():
    host_ip = "127.0.0.1"
    dca_ip = non_loopback_ipv4()
    config_port = unused_udp_port(dca_ip)
    data_port = unused_udp_port(host_ip)
    ready = threading.Event()
    server_errors = []

    def fake_dca_server():
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.settimeout(2)
        try:
            server.bind((dca_ip, config_port))
            ready.set()
            request, client = server.recvfrom(1024)
            header, command, payload_length = struct.unpack("<HHH", request[:6])
            assert header == dca1000.DCA1000MagicNumber.MAGIC_HEADER
            assert command == dca1000.DCA1000Command.SYSTEM_CONNECTION
            assert payload_length == 0
            assert struct.unpack("<H", request[-2:])[0] == (
                dca1000.DCA1000MagicNumber.MAGIC_FOOTER
            )
            response = struct.pack(
                "<HHHH",
                dca1000.DCA1000MagicNumber.MAGIC_HEADER,
                command,
                0,
                dca1000.DCA1000MagicNumber.MAGIC_FOOTER,
            )
            server.sendto(response, client)
        except BaseException as exc:
            server_errors.append(exc)
            ready.set()
        finally:
            server.close()

    thread = threading.Thread(target=fake_dca_server, daemon=True)
    thread.start()
    assert ready.wait(timeout=2)

    dca = dca1000.DCA1000(
        host_ip=host_ip,
        dca_ip=dca_ip,
        dca_config_port=config_port,
        dca_data_port=data_port,
    )
    try:
        assert dca.system_connection() is True
    finally:
        dca.close()
    thread.join(timeout=2)

    assert not thread.is_alive()
    assert server_errors == []
