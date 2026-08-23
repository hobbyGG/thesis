import json
from pathlib import Path
import struct

import numpy as np
import pytest

from mmwavecapture.algorithm_input import (
    AlgorithmInputError,
    DCA1000IntegrityError,
    decode_two_lane_complex,
    export_algorithm_input,
    load_algorithm_input,
    read_dca1000_pcap,
)


PCAP_FIXTURE = "tests/pcaps/test_one_frame.pcap"


def write_matching_radar_config(path):
    path.write_text(
        "\n".join(
            [
                "channelCfg 15 5 0",
                "adcCfg 2 1",
                "adcbufCfg -1 0 1 1 1",
                "profileCfg 0 77 429 7 57.14 0 0 70 1 256 5209 0 0 30",
                "chirpCfg 0 0 0 0 0 0 0 1",
                "chirpCfg 1 1 0 0 0 0 0 4",
                "frameCfg 0 1 2 1 100 1 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def corrupt_second_data_packet_byte_count(source, destination):
    content = bytearray(source.read_bytes())
    offset = 24
    data_packets = 0
    while offset < len(content):
        _seconds, _fraction, captured_length, _original_length = struct.unpack_from(
            "<IIII", content, offset
        )
        packet_offset = offset + 16
        packet = memoryview(content)[packet_offset : packet_offset + captured_length]
        ip_offset = 14
        ip_header_length = (packet[ip_offset] & 0x0F) * 4
        udp_offset = ip_offset + ip_header_length
        destination_port = struct.unpack_from("!H", packet, udp_offset + 2)[0]
        if destination_port == 4098:
            data_packets += 1
            if data_packets == 2:
                payload_offset = packet_offset + udp_offset + 8
                byte_count = int.from_bytes(
                    content[payload_offset + 4 : payload_offset + 10], "little"
                )
                content[payload_offset + 4 : payload_offset + 10] = (
                    byte_count + 8
                ).to_bytes(6, "little")
                destination.write_bytes(content)
                return
        offset = packet_offset + captured_length
    raise AssertionError("fixture contains fewer than two DCA data packets")


def test_two_lane_decoder_matches_legacy_parser_fixture():
    raw_bytes, stats = read_dca1000_pcap(PCAP_FIXTURE)
    signal = decode_two_lane_complex(raw_bytes, quadrature_in_lsb=True)

    assert stats.packet_count == 12
    assert stats.payload_bytes == 16384
    assert signal.shape == (4096,)
    expected = {
        4065: 223 + 120j,
        3293: -90 - 615j,
        415: -88 + 193j,
        1255: 366 - 21j,
        671: -55 + 205j,
        1736: -127 - 238j,
        3474: 268 - 48j,
        2394: 745 - 301j,
        1262: 582 + 30j,
    }
    for index, value in expected.items():
        assert signal[index] == value


def test_export_and_reader_publish_lossless_and_direct_algorithm_cubes(tmp_path):
    config_path = tmp_path / "radar.cfg"
    write_matching_radar_config(config_path)
    output_path = tmp_path / "algorithm_input"

    manifest_path = export_algorithm_input(
        PCAP_FIXTURE,
        config_path,
        output_path,
    )
    capture = load_algorithm_input(output_path)
    raw_bytes, _stats = read_dca1000_pcap(PCAP_FIXTURE)
    signal = decode_two_lane_complex(raw_bytes)

    assert manifest_path == output_path / "manifest.json"
    assert capture.chirp_cube is not None
    assert capture.chirp_cube.shape == (1, 2, 8, 256)
    assert capture.adc_cube.shape == (1, 8, 256)
    assert capture.frame_times_s.tolist() == [0.0]
    np.testing.assert_array_equal(capture.chirp_cube.reshape(-1), signal)
    np.testing.assert_allclose(
        capture.adc_cube,
        np.mean(capture.chirp_cube, axis=1),
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == "mmwavecapture.algorithm-input"
    assert manifest["schema_version"] == 1
    assert manifest["packet_integrity"]["complete"] is True
    assert manifest["radar"]["tx_sequence"] == [0, 2]
    assert manifest["arrays"]["chirp_cube"]["axes"] == [
        "frame",
        "chirp_loop",
        "virtual_antenna",
        "adc_sample",
    ]
    assert manifest["arrays"]["adc_cube"]["axes"] == [
        "frame",
        "virtual_antenna",
        "adc_sample",
    ]


def test_reader_can_resolve_capture_or_hardware_directory(tmp_path):
    hardware_directory = tmp_path / "capture_00000" / "iwr1843"
    hardware_directory.mkdir(parents=True)
    config_path = hardware_directory / "radar.cfg"
    write_matching_radar_config(config_path)
    export_algorithm_input(
        PCAP_FIXTURE,
        config_path,
        hardware_directory / "algorithm_input",
        save_chirp_cube=False,
    )

    from_hardware = load_algorithm_input(hardware_directory)
    from_capture = load_algorithm_input(tmp_path / "capture_00000")
    assert from_hardware.chirp_cube is None
    np.testing.assert_array_equal(from_capture.adc_cube, from_hardware.adc_cube)


def test_packet_gap_fails_closed(tmp_path):
    corrupted = tmp_path / "missing_bytes.pcap"
    corrupt_second_data_packet_byte_count(
        source=Path(PCAP_FIXTURE),
        destination=corrupted,
    )

    with pytest.raises(DCA1000IntegrityError, match="missing DCA1000 bytes"):
        read_dca1000_pcap(corrupted)


def test_export_rejects_existing_package(tmp_path):
    config_path = tmp_path / "radar.cfg"
    write_matching_radar_config(config_path)
    output_path = tmp_path / "algorithm_input"
    output_path.mkdir()

    with pytest.raises(FileExistsError, match="already exists"):
        export_algorithm_input(PCAP_FIXTURE, config_path, output_path)


def test_reader_rejects_unknown_schema_version(tmp_path):
    package = tmp_path / "algorithm_input"
    package.mkdir()
    (package / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "mmwavecapture.algorithm-input",
                "schema_version": 999,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(AlgorithmInputError, match="unsupported schema version"):
        load_algorithm_input(package)
