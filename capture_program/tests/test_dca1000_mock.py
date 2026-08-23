import struct

import pytest

import mmwavecapture.dca1000 as dca1000


class FakeSocket:
    def __init__(self, response_factory):
        self.response_factory = response_factory
        self.bound = None
        self.timeout = None
        self.sent = []
        self.recv_count = 0
        self.closed = False

    def bind(self, address):
        self.bound = address

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendto(self, payload, address):
        self.sent.append((payload, address))

    def recvfrom(self, _size):
        self.recv_count += 1
        return self.response_factory(self), ("192.168.33.180", 4096)

    def close(self):
        self.closed = True


def response_packet(command, status=0):
    return struct.pack(
        "<HHHH",
        dca1000.DCA1000MagicNumber.MAGIC_HEADER,
        command,
        status,
        dca1000.DCA1000MagicNumber.MAGIC_FOOTER,
    )


def response_for_last_command(fake_socket, status=0):
    command = struct.unpack("<H", fake_socket.sent[-1][0][2:4])[0]
    return response_packet(command, status)


def install_fake_sockets(monkeypatch, response_factory=response_for_last_command):
    sockets = []

    def socket_factory(*_args):
        sock = FakeSocket(response_factory)
        sockets.append(sock)
        return sock

    monkeypatch.setattr(dca1000.socket, "socket", socket_factory)
    return sockets


def test_custom_host_and_ports_are_applied_before_socket_bind(monkeypatch):
    sockets = install_fake_sockets(monkeypatch)

    dca = dca1000.DCA1000(
        host_ip="192.168.50.30",
        dca_ip="192.168.50.180",
        dca_config_port=5000,
        dca_data_port=5002,
    )

    assert [sock.bound for sock in sockets] == [
        ("192.168.50.30", 5000),
        ("192.168.50.30", 5002),
    ]
    assert dca.config.dca_ip == "192.168.50.180"


def test_command_packet_and_response_are_validated(monkeypatch):
    sockets = install_fake_sockets(monkeypatch)
    dca = dca1000.DCA1000()

    assert dca.start_record() is True

    payload, address = sockets[0].sent[-1]
    assert address == ("192.168.33.180", 4096)
    assert struct.unpack("<HHH", payload[:6]) == (
        dca1000.DCA1000MagicNumber.MAGIC_HEADER,
        dca1000.DCA1000Command.RECORD_START,
        0,
    )
    assert struct.unpack("<H", payload[-2:])[0] == (
        dca1000.DCA1000MagicNumber.MAGIC_FOOTER
    )


def test_malformed_command_response_raises_protocol_error(monkeypatch):
    install_fake_sockets(monkeypatch, lambda _socket: b"bad")
    dca = dca1000.DCA1000()

    with pytest.raises(dca1000.DCA1000ProtocolError, match="expected 8"):
        dca.system_connection()


def test_async_system_status_is_ignored_until_matching_response(monkeypatch):
    def async_then_matching(fake_socket):
        if fake_socket.recv_count == 1:
            return response_packet(
                dca1000.DCA1000Command.SYSTEM_ERROR_STATUS,
                status=1,
            )
        return response_for_last_command(fake_socket)

    sockets = install_fake_sockets(monkeypatch, async_then_matching)
    dca = dca1000.DCA1000()

    assert dca.stop_record() is True
    assert sockets[0].recv_count == 2


def test_unexpected_non_status_response_still_raises(monkeypatch):
    install_fake_sockets(
        monkeypatch,
        lambda _socket: response_packet(dca1000.DCA1000Command.READ_FPGA_VERSION),
    )
    dca = dca1000.DCA1000()

    with pytest.raises(dca1000.DCA1000ProtocolError, match="does not match"):
        dca.stop_record()


def test_requested_system_status_is_returned_without_being_ignored(monkeypatch):
    install_fake_sockets(
        monkeypatch,
        lambda _socket: response_packet(
            dca1000.DCA1000Command.SYSTEM_ERROR_STATUS,
            status=7,
        ),
    )
    dca = dca1000.DCA1000()

    assert dca.system_error_status() == 7


def test_close_is_idempotent(monkeypatch):
    sockets = install_fake_sockets(monkeypatch)
    dca = dca1000.DCA1000()

    dca.close()
    dca.close()

    assert all(sock.closed for sock in sockets)
