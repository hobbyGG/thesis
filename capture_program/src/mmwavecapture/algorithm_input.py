"""Stable, algorithm-facing exports for IWR1843/DCA1000 captures.

The acquisition boundary owns all PCAP, DCA1000 packet, LVDS lane, I/Q, and
radar-layout handling.  Downstream algorithms only need :func:`load_algorithm_input`
and the documented NumPy axes.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import shutil
import struct
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Iterator, Mapping, Optional, Sequence, Tuple, Union

import numpy as np

from mmwavecapture.radar import RadarCoreConfig


SCHEMA_NAME = "mmwavecapture.algorithm-input"
SCHEMA_VERSION = 1
DEFAULT_OUTPUT_DIRECTORY = "algorithm_input"
MANIFEST_FILENAME = "manifest.json"


class AlgorithmInputError(RuntimeError):
    """Raised when a capture cannot satisfy the algorithm-input contract."""


class DCA1000IntegrityError(AlgorithmInputError):
    """Raised when DCA1000 packet loss, overlap, or corruption is detected."""


@dataclass(frozen=True)
class DCA1000PacketStats:
    packet_count: int
    duplicate_packet_count: int
    payload_bytes: int
    first_sequence_id: int
    last_sequence_id: int
    first_byte_count: int
    last_byte_count: int
    capture_order_monotonic: bool
    first_packet_epoch_s: float
    last_packet_epoch_s: float


@dataclass(frozen=True)
class AlgorithmCapture:
    """Arrays exposed to downstream processing under schema version 1.

    ``adc_cube`` has axes ``(frame, virtual_antenna, adc_sample)`` and can be
    passed directly to the Phase-1 range/angle frontend. ``chirp_cube`` keeps
    the lossless standardized axes
    ``(frame, chirp_loop, virtual_antenna, adc_sample)`` when exported.
    """

    adc_cube: np.ndarray
    frame_times_s: np.ndarray
    chirp_cube: Optional[np.ndarray]
    manifest: Mapping[str, Any]
    directory: pathlib.Path


@dataclass(frozen=True)
class _RawPacket:
    sequence_id: int
    byte_count: int
    data: bytes
    timestamp_s: float
    capture_index: int


def _pcap_records(path: pathlib.Path) -> Iterator[Tuple[int, float, bytes]]:
    magic_formats = {
        b"\xd4\xc3\xb2\xa1": ("<", 1_000_000.0),
        b"\xa1\xb2\xc3\xd4": (">", 1_000_000.0),
        b"\x4d\x3c\xb2\xa1": ("<", 1_000_000_000.0),
        b"\xa1\xb2\x3c\x4d": (">", 1_000_000_000.0),
    }

    with open(path, "rb") as pcap_file:
        global_header = pcap_file.read(24)
        if len(global_header) != 24:
            raise AlgorithmInputError(f"PCAP global header is truncated: {path}")
        try:
            endian, timestamp_divisor = magic_formats[global_header[:4]]
        except KeyError as exc:
            raise AlgorithmInputError(
                f"unsupported PCAP magic {global_header[:4].hex()}: {path}"
            ) from exc

        version_major, version_minor = struct.unpack_from(endian + "HH", global_header, 4)
        if (version_major, version_minor) != (2, 4):
            raise AlgorithmInputError(
                f"unsupported PCAP version {version_major}.{version_minor}: {path}"
            )
        link_type = struct.unpack_from(endian + "I", global_header, 20)[0]

        while True:
            packet_header = pcap_file.read(16)
            if not packet_header:
                return
            if len(packet_header) != 16:
                raise AlgorithmInputError(f"PCAP packet header is truncated: {path}")
            seconds, fraction, captured_length, _original_length = struct.unpack(
                endian + "IIII", packet_header
            )
            packet = pcap_file.read(captured_length)
            if len(packet) != captured_length:
                raise AlgorithmInputError(f"PCAP packet data is truncated: {path}")
            yield link_type, seconds + fraction / timestamp_divisor, packet


def _ipv4_offset(link_type: int, packet: bytes) -> Optional[int]:
    # DLT_EN10MB (Ethernet), including one or more VLAN tags.
    if link_type == 1:
        if len(packet) < 14:
            return None
        offset = 14
        ether_type = struct.unpack_from("!H", packet, 12)[0]
        while ether_type in (0x8100, 0x88A8, 0x9100):
            if len(packet) < offset + 4:
                return None
            ether_type = struct.unpack_from("!H", packet, offset + 2)[0]
            offset += 4
        return offset if ether_type == 0x0800 else None

    # DLT_LINUX_SLL and DLT_LINUX_SLL2 are useful when tcpdump targets a
    # Linux pseudo-interface instead of a physical Ethernet device.
    if link_type == 113:
        if len(packet) < 16 or struct.unpack_from("!H", packet, 14)[0] != 0x0800:
            return None
        return 16
    if link_type == 276:
        if len(packet) < 20 or struct.unpack_from("!H", packet, 0)[0] != 0x0800:
            return None
        return 20
    if link_type == 101:  # DLT_RAW
        return 0

    raise AlgorithmInputError(f"unsupported PCAP link type {link_type}")


def _udp_payload(link_type: int, packet: bytes) -> Optional[Tuple[int, int, bytes]]:
    ip_offset = _ipv4_offset(link_type, packet)
    if ip_offset is None or len(packet) < ip_offset + 20:
        return None
    version_ihl = packet[ip_offset]
    if version_ihl >> 4 != 4:
        return None
    ip_header_length = (version_ihl & 0x0F) * 4
    if ip_header_length < 20 or len(packet) < ip_offset + ip_header_length:
        raise AlgorithmInputError("malformed IPv4 header in PCAP")
    if packet[ip_offset + 9] != 17:
        return None

    fragment_field = struct.unpack_from("!H", packet, ip_offset + 6)[0]
    if fragment_field & 0x3FFF:
        return None

    udp_offset = ip_offset + ip_header_length
    if len(packet) < udp_offset + 8:
        raise AlgorithmInputError("truncated UDP header in PCAP")
    source_port, destination_port, udp_length, _checksum = struct.unpack_from(
        "!HHHH", packet, udp_offset
    )
    if udp_length < 8:
        raise AlgorithmInputError("invalid UDP length in PCAP")
    udp_end = udp_offset + udp_length
    if len(packet) < udp_end:
        raise AlgorithmInputError("truncated UDP payload in PCAP")
    return source_port, destination_port, packet[udp_offset + 8 : udp_end]


def read_dca1000_pcap(
    pcap_file: Union[str, pathlib.Path],
    data_port: int = 4098,
) -> Tuple[bytes, DCA1000PacketStats]:
    """Read and integrity-check the raw byte stream from a DCA1000 PCAP.

    Packets are reconstructed by the DCA byte counter. Capture-order packet
    reordering is accepted, while missing bytes, overlaps, conflicting
    duplicates, and sequence gaps fail closed.
    """

    path = pathlib.Path(pcap_file)
    if not path.is_file():
        raise FileNotFoundError(path)
    if not 0 < int(data_port) <= 65535:
        raise ValueError("data_port must be between 1 and 65535")

    packets = []
    for capture_index, (link_type, timestamp_s, packet) in enumerate(
        _pcap_records(path)
    ):
        udp = _udp_payload(link_type, packet)
        if udp is None:
            continue
        _source_port, destination_port, payload = udp
        if destination_port != data_port:
            continue
        if len(payload) < 10:
            raise DCA1000IntegrityError(
                f"DCA1000 data packet {capture_index} has a truncated 10-byte header"
            )
        sequence_id = struct.unpack_from("<I", payload, 0)[0]
        byte_count = int.from_bytes(payload[4:10], byteorder="little", signed=False)
        data = payload[10:]
        if not data:
            raise DCA1000IntegrityError(
                f"DCA1000 sequence {sequence_id} contains no LVDS payload"
            )
        packets.append(
            _RawPacket(
                sequence_id=sequence_id,
                byte_count=byte_count,
                data=data,
                timestamp_s=timestamp_s,
                capture_index=capture_index,
            )
        )

    if not packets:
        raise DCA1000IntegrityError(
            f"no DCA1000 UDP data packets for destination port {data_port}: {path}"
        )

    capture_order_monotonic = all(
        current.byte_count > previous.byte_count
        for previous, current in zip(packets, packets[1:])
    )
    ordered = sorted(packets, key=lambda packet: (packet.byte_count, packet.sequence_id))

    stream = bytearray()
    accepted = []
    duplicate_count = 0
    for packet in ordered:
        expected_offset = len(stream)
        if packet.byte_count < expected_offset:
            duplicate = next(
                (
                    prior
                    for prior in reversed(accepted)
                    if prior.byte_count == packet.byte_count
                ),
                None,
            )
            if duplicate is not None and duplicate.data == packet.data:
                duplicate_count += 1
                continue
            raise DCA1000IntegrityError(
                f"overlapping DCA1000 payload at byte {packet.byte_count}; "
                f"expected {expected_offset}"
            )
        if packet.byte_count > expected_offset:
            raise DCA1000IntegrityError(
                f"missing DCA1000 bytes [{expected_offset}, {packet.byte_count})"
            )

        if accepted:
            expected_sequence = (accepted[-1].sequence_id + 1) & 0xFFFFFFFF
            if packet.sequence_id != expected_sequence:
                raise DCA1000IntegrityError(
                    f"DCA1000 sequence gap: expected {expected_sequence}, "
                    f"received {packet.sequence_id}"
                )
        stream.extend(packet.data)
        accepted.append(packet)

    first = accepted[0]
    last = accepted[-1]
    stats = DCA1000PacketStats(
        packet_count=len(accepted),
        duplicate_packet_count=duplicate_count,
        payload_bytes=len(stream),
        first_sequence_id=first.sequence_id,
        last_sequence_id=last.sequence_id,
        first_byte_count=first.byte_count,
        last_byte_count=last.byte_count,
        capture_order_monotonic=capture_order_monotonic,
        first_packet_epoch_s=min(packet.timestamp_s for packet in accepted),
        last_packet_epoch_s=max(packet.timestamp_s for packet in accepted),
    )
    return bytes(stream), stats


def decode_two_lane_complex(
    raw_bytes: bytes,
    quadrature_in_lsb: bool = True,
) -> np.ndarray:
    """Decode IWR1843 two-lane LVDS words into ``complex64`` I+jQ samples."""

    if len(raw_bytes) % 8:
        raise AlgorithmInputError(
            "two-lane complex LVDS data must contain a multiple of 8 bytes"
        )
    words = np.frombuffer(raw_bytes, dtype="<i2")
    lanes = words.reshape(-1, 4)
    if quadrature_in_lsb:
        quadrature = lanes[:, 0:2].reshape(-1)
        in_phase = lanes[:, 2:4].reshape(-1)
    else:
        in_phase = lanes[:, 0:2].reshape(-1)
        quadrature = lanes[:, 2:4].reshape(-1)

    complex_samples = np.empty(in_phase.size, dtype=np.complex64)
    complex_samples.real = in_phase
    complex_samples.imag = quadrature
    return complex_samples


def _single_command(config: RadarCoreConfig, command: str) -> Sequence[str]:
    values = config.command_args(command)
    if len(values) != 1:
        raise AlgorithmInputError(
            f"radar config must contain exactly one `{command}` command"
        )
    return values[0]


def _chirp_tx_sequence(config: RadarCoreConfig) -> Tuple[int, ...]:
    frame_cfg = _single_command(config, "frameCfg")
    chirp_start = int(frame_cfg[0])
    chirp_end = int(frame_cfg[1])
    chirp_cfgs = config.command_args("chirpCfg")
    sequence = []
    for chirp_index in range(chirp_start, chirp_end + 1):
        matches = [
            args
            for args in chirp_cfgs
            if int(args[0]) <= chirp_index <= int(args[1])
        ]
        if len(matches) != 1:
            raise AlgorithmInputError(
                f"chirp index {chirp_index} must match exactly one chirpCfg"
            )
        tx_mask = int(matches[0][7])
        tx_indices = [index for index in range(32) if tx_mask & (1 << index)]
        if len(tx_indices) != 1:
            raise AlgorithmInputError(
                "algorithm export currently requires TDM-MIMO with exactly one "
                f"TX enabled per chirp; chirp {chirp_index} has mask {tx_mask}"
            )
        sequence.append(tx_indices[0])
    return tuple(sequence)


def _radar_layout(config: RadarCoreConfig, complex_count: int) -> Mapping[str, Any]:
    frame_cfg = _single_command(config, "frameCfg")
    channel_cfg = _single_command(config, "channelCfg")
    profile_cfg = _single_command(config, "profileCfg")
    adc_cfg = _single_command(config, "adcCfg")
    adcbuf_cfg = _single_command(config, "adcbufCfg")

    adc_bits_code = int(adc_cfg[0])
    adc_output_format = int(adc_cfg[1])
    if adc_bits_code != 2 or adc_output_format != 1:
        raise AlgorithmInputError(
            "algorithm export requires adcCfg 2 1 (16-bit complex ADC output)"
        )

    adc_buffer_output_format = int(adcbuf_cfg[1])
    sample_swap = int(adcbuf_cfg[2])
    channel_interleave = int(adcbuf_cfg[3])
    if adc_buffer_output_format != 0:
        raise AlgorithmInputError(
            "algorithm export requires adcbufCfg complex output format 0"
        )
    if sample_swap not in (0, 1):
        raise AlgorithmInputError("adcbufCfg sampleSwap must be 0 or 1")
    if channel_interleave != 1:
        raise AlgorithmInputError(
            "algorithm export currently requires non-interleaved RX channels "
            "(adcbufCfg channelInterleave=1)"
        )

    tx_mask = int(channel_cfg[1])
    rx_mask = int(channel_cfg[0])
    enabled_tx = tuple(index for index in range(32) if tx_mask & (1 << index))
    enabled_rx = tuple(index for index in range(32) if rx_mask & (1 << index))
    tx_sequence = _chirp_tx_sequence(config)
    if len(set(tx_sequence)) != len(tx_sequence) or set(tx_sequence) != set(enabled_tx):
        raise AlgorithmInputError(
            "each enabled TX must occur exactly once in the frame chirp sequence"
        )
    if not enabled_rx:
        raise AlgorithmInputError("radar config enables no RX antennas")

    loops = int(frame_cfg[2])
    frames = int(frame_cfg[3])
    samples = int(profile_cfg[9])
    values_per_frame = loops * len(tx_sequence) * len(enabled_rx) * samples
    if min(loops, samples, values_per_frame) <= 0:
        raise AlgorithmInputError("radar dimensions must be positive")
    if frames == 0:
        frames, remainder = divmod(complex_count, values_per_frame)
        if remainder:
            raise AlgorithmInputError(
                "infinite-frame radar config cannot infer a whole number of frames "
                f"from {complex_count} complex samples"
            )
    expected_complex = frames * values_per_frame
    if complex_count != expected_complex:
        raise AlgorithmInputError(
            f"capture has {complex_count} complex samples, but radar.cfg requires "
            f"{expected_complex} ({frames} frames)"
        )

    frame_period_s = float(frame_cfg[4]) / 1000.0
    adc_sample_rate_hz = float(profile_cfg[10]) * 1000.0
    frequency_slope_hz_per_s = float(profile_cfg[7]) * 1.0e12
    ramp_end_time_s = float(profile_cfg[4]) * 1.0e-6
    start_frequency_hz = float(profile_cfg[1]) * 1.0e9
    speed_of_light_mps = 299_792_458.0
    range_resolution_m = (
        speed_of_light_mps * adc_sample_rate_hz
        / (2.0 * abs(frequency_slope_hz_per_s) * samples)
    )

    virtual_channels = []
    for tx_index in tx_sequence:
        for rx_index in enabled_rx:
            virtual_channels.append(
                {
                    "index": len(virtual_channels),
                    "tx_index": tx_index,
                    "rx_index": rx_index,
                }
            )

    return {
        "frames": frames,
        "frame_period_s": frame_period_s,
        "frame_rate_hz": 1.0 / frame_period_s,
        "chirp_loops_per_frame": loops,
        "tx_chirps_per_loop": len(tx_sequence),
        "physical_chirps_per_frame": loops * len(tx_sequence),
        "tx_indices": list(enabled_tx),
        "tx_sequence": list(tx_sequence),
        "rx_indices": list(enabled_rx),
        "virtual_antennas": len(virtual_channels),
        "virtual_channels": virtual_channels,
        "adc_samples_per_chirp": samples,
        "adc_sample_rate_hz": adc_sample_rate_hz,
        "start_frequency_hz": start_frequency_hz,
        "frequency_slope_hz_per_s": frequency_slope_hz_per_s,
        "ramp_end_time_s": ramp_end_time_s,
        "range_resolution_m": range_resolution_m,
        "quadrature_in_lsb": bool(sample_swap),
    }


def _array_description(filename: str, array: np.ndarray, axes: Sequence[str]) -> dict:
    return {
        "file": filename,
        "dtype": array.dtype.name,
        "shape": list(array.shape),
        "axes": list(axes),
    }


def export_algorithm_input(
    pcap_file: Union[str, pathlib.Path],
    radar_config_file: Union[str, pathlib.Path],
    output_directory: Union[str, pathlib.Path],
    *,
    data_port: int = 4098,
    chirp_aggregation: str = "coherent_mean",
    save_chirp_cube: bool = True,
) -> pathlib.Path:
    """Create an atomic, versioned algorithm-input directory from a capture."""

    pcap_path = pathlib.Path(pcap_file)
    radar_path = pathlib.Path(radar_config_file)
    output_path = pathlib.Path(output_directory)
    if output_path.exists():
        raise FileExistsError(f"algorithm input directory already exists: {output_path}")
    if chirp_aggregation not in ("coherent_mean", "first"):
        raise ValueError("chirp_aggregation must be `coherent_mean` or `first`")

    raw_bytes, packet_stats = read_dca1000_pcap(pcap_path, data_port=data_port)
    config = RadarCoreConfig(radar_path)
    # IWR1843's configured sampleSwap determines which half of each two-lane
    # group is Q. Decode once to learn the count, then enforce the full layout.
    adcbuf_cfg = _single_command(config, "adcbufCfg")
    complex_samples = decode_two_lane_complex(
        raw_bytes,
        quadrature_in_lsb=bool(int(adcbuf_cfg[2])),
    )
    radar = _radar_layout(config, complex_samples.size)

    chirp_cube = complex_samples.reshape(
        radar["frames"],
        radar["chirp_loops_per_frame"],
        radar["virtual_antennas"],
        radar["adc_samples_per_chirp"],
    )
    if chirp_aggregation == "coherent_mean":
        adc_cube = np.mean(chirp_cube, axis=1).astype(np.complex64, copy=False)
    else:
        adc_cube = np.array(chirp_cube[:, 0, :, :], dtype=np.complex64, copy=True)
    frame_times_s = (
        np.arange(radar["frames"], dtype=np.float64) * radar["frame_period_s"]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.parent / f".{output_path.name}.tmp-{uuid.uuid4().hex}"
    temporary.mkdir(exist_ok=False)
    try:
        arrays = {}
        adc_filename = "adc_cube.npy"
        frame_times_filename = "frame_times_s.npy"
        np.save(temporary / adc_filename, adc_cube, allow_pickle=False)
        np.save(temporary / frame_times_filename, frame_times_s, allow_pickle=False)
        arrays["adc_cube"] = _array_description(
            adc_filename,
            adc_cube,
            ("frame", "virtual_antenna", "adc_sample"),
        )
        arrays["frame_times_s"] = _array_description(
            frame_times_filename,
            frame_times_s,
            ("frame",),
        )
        if save_chirp_cube:
            chirp_filename = "chirp_cube.npy"
            np.save(temporary / chirp_filename, chirp_cube, allow_pickle=False)
            arrays["chirp_cube"] = _array_description(
                chirp_filename,
                chirp_cube,
                ("frame", "chirp_loop", "virtual_antenna", "adc_sample"),
            )

        manifest = {
            "schema": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "created_at": datetime.datetime.now().astimezone().isoformat(),
            "source": {
                "pcap_file": f"../{pcap_path.name}",
                "pcap_size_bytes": pcap_path.stat().st_size,
                "radar_config_file": f"../{radar_path.name}",
                "radar_config_size_bytes": radar_path.stat().st_size,
                "dca_data_port": int(data_port),
            },
            "packet_integrity": {
                "complete": True,
                **asdict(packet_stats),
            },
            "radar": dict(radar),
            "processing": {
                "lvds_lanes": 2,
                "lvds_word_dtype": "int16_le",
                "complex_convention": "I+jQ",
                "two_lane_group_when_quadrature_in_lsb": ["Q0", "Q1", "I0", "I1"],
                "chirp_cube_layout": "TDM chirp order, then non-interleaved RX, then ADC sample",
                "frame_level_chirp_aggregation": chirp_aggregation,
            },
            "arrays": arrays,
        }
        (temporary / MANIFEST_FILENAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(output_path)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    return output_path / MANIFEST_FILENAME


def _resolve_algorithm_directory(path: Union[str, pathlib.Path]) -> pathlib.Path:
    candidate = pathlib.Path(path)
    if candidate.is_file() and candidate.name == MANIFEST_FILENAME:
        return candidate.parent
    if (candidate / MANIFEST_FILENAME).is_file():
        return candidate
    if (candidate / DEFAULT_OUTPUT_DIRECTORY / MANIFEST_FILENAME).is_file():
        return candidate / DEFAULT_OUTPUT_DIRECTORY

    matches = list(candidate.glob(f"*/{DEFAULT_OUTPUT_DIRECTORY}/{MANIFEST_FILENAME}"))
    if len(matches) == 1:
        return matches[0].parent
    if len(matches) > 1:
        raise AlgorithmInputError(
            f"multiple algorithm inputs found under {candidate}; select one hardware directory"
        )
    raise FileNotFoundError(
        f"cannot find {MANIFEST_FILENAME} or {DEFAULT_OUTPUT_DIRECTORY}/"
        f"{MANIFEST_FILENAME} under {candidate}"
    )


def _load_array(
    directory: pathlib.Path,
    name: str,
    description: Mapping[str, Any],
    mmap_mode: Optional[str],
) -> np.ndarray:
    filename = description.get("file")
    if not isinstance(filename, str):
        raise AlgorithmInputError(f"array `{name}` has no valid file name")
    base = directory.resolve()
    path = (directory / filename).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise AlgorithmInputError(f"array `{name}` escapes the package directory") from exc
    if not path.is_file():
        raise AlgorithmInputError(f"array `{name}` is missing: {path}")

    array = np.load(path, mmap_mode=mmap_mode, allow_pickle=False)
    expected_shape = tuple(description.get("shape", ()))
    expected_dtype = description.get("dtype")
    if array.shape != expected_shape:
        raise AlgorithmInputError(
            f"array `{name}` shape is {array.shape}, expected {expected_shape}"
        )
    if array.dtype.name != expected_dtype:
        raise AlgorithmInputError(
            f"array `{name}` dtype is {array.dtype.name}, expected {expected_dtype}"
        )
    return array


def load_algorithm_input(
    path: Union[str, pathlib.Path],
    *,
    mmap_mode: Optional[str] = "r",
) -> AlgorithmCapture:
    """Load only the stable schema; this function never parses PCAP/LVDS data."""

    directory = _resolve_algorithm_directory(path)
    manifest_path = directory / MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA_NAME:
        raise AlgorithmInputError(
            f"unsupported algorithm-input schema: {manifest.get('schema')!r}"
        )
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise AlgorithmInputError(
            f"unsupported schema version {manifest.get('schema_version')}; "
            f"reader supports {SCHEMA_VERSION}"
        )
    if manifest.get("packet_integrity", {}).get("complete") is not True:
        raise AlgorithmInputError("algorithm input is not marked packet-complete")

    arrays = manifest.get("arrays")
    if not isinstance(arrays, dict):
        raise AlgorithmInputError("manifest has no arrays table")
    for required in ("adc_cube", "frame_times_s"):
        if required not in arrays:
            raise AlgorithmInputError(f"manifest is missing required array `{required}`")
    expected_axes = {
        "adc_cube": ["frame", "virtual_antenna", "adc_sample"],
        "frame_times_s": ["frame"],
        "chirp_cube": [
            "frame",
            "chirp_loop",
            "virtual_antenna",
            "adc_sample",
        ],
    }
    for name, axes in expected_axes.items():
        if name not in arrays:
            continue
        if not isinstance(arrays[name], dict):
            raise AlgorithmInputError(f"array `{name}` description must be a table")
        if arrays[name].get("axes") != axes:
            raise AlgorithmInputError(
                f"array `{name}` axes are {arrays[name].get('axes')!r}, expected {axes!r}"
            )

    adc_cube = _load_array(directory, "adc_cube", arrays["adc_cube"], mmap_mode)
    frame_times_s = _load_array(
        directory, "frame_times_s", arrays["frame_times_s"], mmap_mode
    )
    chirp_cube = (
        _load_array(directory, "chirp_cube", arrays["chirp_cube"], mmap_mode)
        if "chirp_cube" in arrays
        else None
    )

    if adc_cube.ndim != 3 or adc_cube.dtype != np.dtype(np.complex64):
        raise AlgorithmInputError(
            "adc_cube must be complex64 with axes (frame, virtual_antenna, adc_sample)"
        )
    if frame_times_s.ndim != 1 or frame_times_s.dtype != np.dtype(np.float64):
        raise AlgorithmInputError("frame_times_s must be a float64 vector")
    if frame_times_s.shape[0] != adc_cube.shape[0]:
        raise AlgorithmInputError("frame_times_s length does not match adc_cube frames")
    if chirp_cube is not None:
        if chirp_cube.ndim != 4 or chirp_cube.dtype != np.dtype(np.complex64):
            raise AlgorithmInputError(
                "chirp_cube must be complex64 with axes "
                "(frame, chirp_loop, virtual_antenna, adc_sample)"
            )
        if (
            chirp_cube.shape[0] != adc_cube.shape[0]
            or chirp_cube.shape[2:] != adc_cube.shape[1:]
        ):
            raise AlgorithmInputError("chirp_cube axes do not match adc_cube")

    radar = manifest.get("radar")
    if not isinstance(radar, dict):
        raise AlgorithmInputError("manifest has no radar table")
    integer_fields = (
        "frames",
        "chirp_loops_per_frame",
        "virtual_antennas",
        "adc_samples_per_chirp",
    )
    try:
        dimensions = {name: int(radar[name]) for name in integer_fields}
    except (KeyError, TypeError, ValueError) as exc:
        raise AlgorithmInputError("manifest has invalid radar dimensions") from exc
    if any(value <= 0 for value in dimensions.values()):
        raise AlgorithmInputError("manifest radar dimensions must be positive")
    expected_adc_shape = (
        dimensions["frames"],
        dimensions["virtual_antennas"],
        dimensions["adc_samples_per_chirp"],
    )
    if adc_cube.shape != expected_adc_shape:
        raise AlgorithmInputError(
            f"adc_cube shape {adc_cube.shape} disagrees with radar {expected_adc_shape}"
        )
    if chirp_cube is not None:
        expected_chirp_shape = (
            dimensions["frames"],
            dimensions["chirp_loops_per_frame"],
            dimensions["virtual_antennas"],
            dimensions["adc_samples_per_chirp"],
        )
        if chirp_cube.shape != expected_chirp_shape:
            raise AlgorithmInputError(
                f"chirp_cube shape {chirp_cube.shape} disagrees with radar "
                f"{expected_chirp_shape}"
            )
    expected_payload_bytes = (
        dimensions["frames"]
        * dimensions["chirp_loops_per_frame"]
        * dimensions["virtual_antennas"]
        * dimensions["adc_samples_per_chirp"]
        * 4
    )
    if manifest["packet_integrity"].get("payload_bytes") != expected_payload_bytes:
        raise AlgorithmInputError(
            "packet payload byte count disagrees with the radar dimensions"
        )
    if not np.all(np.isfinite(frame_times_s)) or np.any(np.diff(frame_times_s) <= 0.0):
        raise AlgorithmInputError("frame_times_s must be finite and strictly increasing")

    return AlgorithmCapture(
        adc_cube=adc_cube,
        frame_times_s=frame_times_s,
        chirp_cube=chirp_cube,
        manifest=manifest,
        directory=directory,
    )
