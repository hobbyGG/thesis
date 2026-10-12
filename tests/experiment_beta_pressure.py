"""Three focused beta stress tests on the retained A20 capture/algorithm path.

Run with numpy, scipy and matplotlib installed. No estimator reads scene truth.
The three beta histories use the SAME causal IQ phases and structural Kalman.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from algorithm.config import AlgorithmConfig
from algorithm.io import build_algorithm_inputs, load_capture_package
from algorithm.kalman import run_fixed_beta_kalman
from paper_bridge_simulation import package_builder as pb


EVENTS = ((0.5, 1.3), (6.3, 7.1), (12.1, 12.9))
SEEDS = (2026, 2027, 2028)
ANGLE_OFFSETS = (-3.0, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.0)
HP_HZ, LP_HZ = 3.0, 100.0
EXCITATION_M = 5.0e-6
EXCITATION_DURATION_S = 0.10
REG_ADXL_FRACTION = 0.25
METHODS = ("aoa", "adxl", "regularized")


def lfilter(b, a, x):
    """Small causal IIR filter for this offline experiment (last axis)."""
    values = np.asarray(x, dtype=float)
    original_shape = values.shape
    values = values.reshape((-1, original_shape[-1]))
    b = np.asarray(b, dtype=float) / float(a[0])
    a = np.asarray(a, dtype=float) / float(a[0])
    output = np.zeros_like(values)
    for k in range(values.shape[-1]):
        output[:, k] = b[0] * values[:, k]
        for j in range(1, min(k + 1, b.size)):
            output[:, k] += b[j] * values[:, k - j]
        for j in range(1, min(k + 1, a.size)):
            output[:, k] -= a[j] * output[:, k - j]
    return output.reshape(original_shape)


def matched_filtered_displacement(los_m, accel_mps2, sample_rate):
    """Causal matched transfer functions; no FFT of the complete record.

    H_r(s) = [s/(s+w_h)]^3 [w_l/(s+w_l)]^2
    H_a(s) = [1/(s+w_h)]^2 [s/(s+w_h)] [w_l/(s+w_l)]^2.
    Thus H_a(s) a(s) = H_r(s) q(s) for a=q'', up to sampling error.
    """
    k = 2.0 * sample_rate
    wh, wl = 2.0 * np.pi * HP_HZ, 2.0 * np.pi * LP_HZ
    hp_b, hp_a = np.array([k, -k]) / (k + wh), [1.0, (wh - k) / (wh + k)]
    int_b = np.ones(2) / (k + wh)
    lp_b, lp_a = np.array([wl, wl]) / (k + wl), [1.0, (wl - k) / (wl + k)]
    x = np.asarray(los_m, float).copy()
    y = np.asarray(accel_mps2, float).copy()
    for _ in range(3):
        x = lfilter(hp_b, hp_a, x, axis=-1)
    for _ in range(2):
        y = lfilter(int_b, hp_a, y)
    y = lfilter(hp_b, hp_a, y)
    for _ in range(2):
        x = lfilter(lp_b, lp_a, x, axis=-1)
        y = lfilter(lp_b, lp_a, y)
    return x, y


def match_beta(capture, radar, los_m, rate):
    """Prefix-only LS sums. AoA supplies the start value until excitation exists."""
    t0 = int(capture.adxl_time_ns[0])
    rt = (radar.extra["radar_time_ns"] - t0) * 1.0e-9
    at = (capture.adxl_time_ns - t0) * 1.0e-9
    manifest = json.loads((capture.root / "adxl355/algorithm_input/manifest.json").read_text())
    delay = float(manifest["capture"]["group_delay_ns"]) * 1.0e-9
    # A full native sample period of latency ensures both interpolation ends
    # are already received. Both sides refer to t-latency-group_delay.
    latency = float(np.max(np.diff(at)))
    a = np.interp(rt - latency, at, capture.adxl_acceleration_mps2[:, 0])
    r = np.asarray([np.interp(rt - latency - delay, rt, row) for row in los_m])
    x, y = matched_filtered_displacement(r, a, rate)
    usable = np.abs(y) >= EXCITATION_M
    n = np.cumsum(usable)
    sxx = np.cumsum(x * x * usable, axis=1)
    sxy = np.cumsum(x * y[None, :] * usable, axis=1)
    raw = np.divide(sxy, sxx, out=np.zeros_like(sxy), where=sxx > 1.0e-24)
    ready = (n[None, :] >= int(np.ceil(EXCITATION_DURATION_S * rate))) & (sxx > 1.0e-24)
    # Negative scale contradicts the chosen downward positive LOS model.
    # Keep AoA for an unobservable/invalid match, and report how often it occurs.
    ready &= np.isfinite(raw) & (raw > 0.0)
    return raw, ready, x, y


def run_beta_history(radar, acceleration, config, los, beta):
    """The retained common Kalman equation, replacing only fixed beta by beta[k]."""
    samples = los.shape[1]
    x = np.zeros(2)
    p = np.diag([config.initial_state_variance, config.initial_rate_variance])
    r = np.clip(radar.initial_r.copy(), config.min_measurement_variance, config.max_measurement_variance)
    q = np.zeros(samples)
    pre = acceleration.preintegration
    dt0 = float(radar.extra["sample_period_s"])
    scale = config.wavelength_m() / (4.0 * np.pi)
    for k in range(samples):
        dt = dt0
        if k:
            dt = pre.duration_s[k - 1]
            a = np.array([[1.0, dt], [0.0, 1.0]])
            process = np.array([[dt**3 / 3.0, dt**2 / 2.0], [dt**2 / 2.0, dt]])
            x = a @ x + np.array([pre.delta_q_m[k - 1], pre.delta_v_mps[k - 1]]) / scale
            p = a @ p @ a.T + config.process_noise_intensity * process
        ids = radar.selected_indices
        ids = ids[radar.available_mask[ids, k] & np.isfinite(los[ids, k])]
        if ids.size:
            y = beta[ids, k] * los[ids, k]
            precision = 1.0 / np.maximum(r[ids], config.min_measurement_variance)
            z = np.sum(precision * y) / np.sum(precision)
            variance = 1.0 / np.sum(precision)
            gain = p[:, 0] / (p[0, 0] + variance)
            x = x + gain * (z - x[0])
            p = (np.eye(2) - np.outer(gain, [1.0, 0.0])) @ p
            rho = config.adaptive_r_forgetting ** (dt / dt0)
            r[ids] = np.clip(rho * r[ids] + (1.0 - rho) * ((y - x[0])**2 + p[0, 0]),
                             config.min_measurement_variance, config.max_measurement_variance)
        q[k] = x[0] * scale
    return q


def configure_package(root, seed, angles, snr_db):
    """Perturb parameters of the SAME A20 generator, preserving its package boundary."""
    keys = ("TARGET_ANGLES_DEG", "TARGET_RANGES_M", "TARGET_RANGE_BINS", "TARGET_X_M",
            "TARGET_AMPLITUDES", "RECEIVER_NOISE_STD", "STATIC_SCATTERERS")
    saved = {key: getattr(pb, key) for key in keys}
    angles = np.asarray(angles, float)
    try:
        pb.TARGET_ANGLES_DEG = angles
        pb.TARGET_X_M = pb.GUIDEWAY_TO_GROUND_HEIGHT_M * np.tan(np.deg2rad(angles))
        pb.TARGET_RANGES_M = pb.GUIDEWAY_TO_GROUND_HEIGHT_M / np.cos(np.deg2rad(angles))
        pb.TARGET_RANGE_BINS = np.rint(pb.TARGET_RANGES_M / pb.RANGE_RESOLUTION_M).astype(int)
        if snr_db is not None:
            # Set nominal per-target SNR at the Hamming range FFT, BEFORE
            # loop averaging and DBF. Keep ADC values far below saturation.
            pb.RECEIVER_NOISE_STD = 0.002
            n = np.arange(pb.ADC_SAMPLES)
            w = np.hamming(pb.ADC_SAMPLES)
            frac = pb.TARGET_RANGES_M / pb.RANGE_RESOLUTION_M - pb.TARGET_RANGE_BINS
            gain = np.abs(np.exp(2j * np.pi * frac[:, None] * n / n.size) @ w)
            noise_power = 2.0 * pb.RECEIVER_NOISE_STD**2 * np.sum(w * w)
            pb.TARGET_AMPLITUDES = np.sqrt(noise_power * 10.0**(snr_db / 10.0)) / gain
            pb.TARGET_AMPLITUDES *= (pb.TARGET_RANGES_M / pb.TARGET_REFERENCE_RANGE_M)**2
            relative = float(np.mean(pb.TARGET_AMPLITUDES / saved["TARGET_AMPLITUDES"]))
            pb.STATIC_SCATTERERS = tuple(dict(s, amplitude=s["amplitude"] * relative)
                                         for s in saved["STATIC_SCATTERERS"])
        pb.generate(root, seed=seed)
    finally:
        for key, value in saved.items():
            setattr(pb, key, value)


def measure_range_snr(capture, source):
    """Measured Hamming range-bin signal/noise powers; truth never enters processing."""
    ch = capture.chirp_cube
    w = np.hamming(ch.shape[-1])
    summed = np.zeros(ch.shape[-1])
    count = 0
    for start in range(0, ch.shape[0], 128):
        block = ch[start:start + 128]
        p = np.abs(np.fft.fft(block * w, axis=-1))**2
        summed += p.sum(axis=(0, 1, 2))
        count += int(np.prod(p.shape[:-1]))
    power = summed / count
    excluded = np.zeros(power.size, bool)
    ranges = list(source["target_ranges_m"]) + list(np.asarray(source["target_ranges_m"]) + 0.08)
    ranges += [s["range_m"] for s in source["scene"]["static_scatterers"]]
    for distance in ranges:
        k = round(distance / capture.frontend.range_resolution_m)
        excluded[max(0, k - 4):min(power.size, k + 5)] = True
    floor = float(np.mean(power[~excluded]))
    peaks = np.asarray(source["target_range_bins"], int)
    snr = 10.0 * np.log10(np.maximum(power[peaks] - floor, 1e-30) / floor)
    return snr.tolist()


def event_rmse(error, time):
    return [float(np.sqrt(np.mean(error[(time >= a) & (time <= b)]**2)) * 1.0e6)
            for a, b in EVENTS]


def evaluate(root, group, level, seed, output):
    capture = load_capture_package(root)
    # Make the truth-free input boundary explicit; retain truth only for scoring below.
    radar, acceleration, targets, rate = build_algorithm_inputs(
        replace(capture, truth_displacement_m=None, truth_time_ns=None))
    m = capture.radar_metadata
    fc = m["start_frequency_hz"] + m["chirp_slope_hz_per_s"] * (
        m["adc_start_time_s"] + (capture.frontend.num_adc_samples - 1) / (2.0 * m["adc_sample_rate_hz"]))
    config = AlgorithmConfig(sample_rate_hz=rate, carrier_frequency_hz=fc)
    retained = run_fixed_beta_kalman(radar, acceleration, config)
    los = retained.los_corrected_phase_rad
    scale = config.wavelength_m() / (4.0 * np.pi)
    raw_beta, ready, filtered_r, filtered_a = match_beta(capture, radar, los * scale, rate)
    baseline_beta = np.broadcast_to(radar.measured_beta[:, None], los.shape)
    baseline = run_beta_history(radar, acceleration, config, los, baseline_beta)
    np.testing.assert_allclose(baseline, retained.q_hat_m, rtol=0, atol=1.0e-12)
    # Truncating incoming arrays must not change the fitted prefix.
    cut = int(round(rate * 1.1))
    cut_radar = replace(radar, extra=dict(radar.extra, radar_time_ns=radar.extra["radar_time_ns"][:cut]))
    rb, rd, _, _ = match_beta(capture, cut_radar, los[:, :cut] * scale, rate)
    np.testing.assert_allclose(raw_beta[:, :cut], rb, rtol=0, atol=1.0e-12)
    np.testing.assert_array_equal(ready[:, :cut], rd)

    source = json.loads((root / "radar/algorithm_input/manifest.json").read_text())["source"]
    snr = measure_range_snr(capture, source)
    time_ns = np.asarray(radar.extra["radar_time_ns"], np.int64)
    # Absolute simulation elapsed times include the coherent-aperture offset.
    time = (time_ns - int(capture.truth_time_ns[0])) * 1.0e-9
    truth = np.interp(time_ns, capture.truth_time_ns, capture.truth_displacement_m)
    truth -= np.mean(truth[time < 0.2])
    diagnostic_beta = None
    if group != "close":
        scene_r = np.asarray(source["target_ranges_m"])
        scene_a = np.asarray(source["target_angles_deg"])
        match = np.argmin(np.abs(targets.range_m[:, None] - scene_r[None, :]), axis=1)
        if len(set(match.tolist())) == len(match) and np.all(np.abs(targets.range_m - scene_r[match]) < 0.07):
            diagnostic_beta = 1.0 / np.cos(np.deg2rad(scene_a[match]))
    reference = None if diagnostic_beta is None else run_beta_history(
        radar, acceleration, config, los, np.broadcast_to(diagnostic_beta[:, None], los.shape))
    offsets = ANGLE_OFFSETS if group == "angle" else (0.0,)
    rows = []
    saved = dict(time_s=time, truth_m=truth, los_rad=los, beta_match=raw_beta,
                 beta_ready=ready, filtered_r_m=filtered_r, filtered_a_m=filtered_a,
                 target_range_m=targets.range_m, target_angle_deg=targets.angle_deg,
                 baseline_m=baseline)
    if reference is not None:
        saved["true_beta_reference_m"] = reference
    for offset in offsets:
        prior = 1.0 / np.maximum(np.abs(np.cos(np.deg2rad(targets.angle_deg + offset))), 1.0e-6)
        aoa = np.broadcast_to(prior[:, None], los.shape)
        matched = np.where(ready, raw_beta, aoa)
        regularized = (1.0 - REG_ADXL_FRACTION) * aoa + REG_ADXL_FRACTION * matched
        for method, beta in zip(METHODS, (aoa, matched, regularized)):
            q = run_beta_history(radar, acceleration, config, los, beta)
            rows.append(dict(group=group, level=float(offset if group == "angle" else level),
                             seed=seed, method=method, event_rmse_um=event_rmse(q - truth, time),
                             beta_only_event_rmse_um=None if reference is None else event_rmse(q - reference, time),
                             all_rmse_um=float(np.sqrt(np.mean((q - truth)**2)) * 1.0e6),
                             beta_end=beta[:, -1].tolist()))
            saved[f"q_{offset:+g}_{method}"] = q
    name = f"{group}_{level:g}_seed{seed}"
    np.savez_compressed(output / f"{name}.npz", **saved)
    result = dict(name=name, group=group, level=level, seed=seed, package=str(root),
                  detected_angles_deg=targets.angle_deg.tolist(), detected_ranges_m=targets.range_m.tolist(),
                  true_angles_deg=source["target_angles_deg"], true_ranges_m=source["target_ranges_m"],
                  measured_range_fft_snr_db=snr, beta_match_end=raw_beta[:, -1].tolist(),
                  beta_first_ready_s=[float(time[np.flatnonzero(row)[0]]) if np.any(row) else None for row in ready],
                  beta_end_ready=ready[:, -1].tolist(), beta_truth_mapping=diagnostic_beta.tolist() if diagnostic_beta is not None else None,
                  retained_equation_and_prefix_checks=True, rows=rows)
    (output / f"{name}.json").write_text(json.dumps(result, indent=2) + "\n")
    print(name, "targets", len(targets.angle_deg), "SNR", np.round(snr, 1).tolist(), flush=True)
    for row in rows:
        if row["level"] in (0.0, 2.0, 3.0) or group != "angle":
            print(row["level"], row["method"], "events", np.round(row["event_rmse_um"], 2).tolist(), flush=True)
    return result


def aggregate(output):
    cases = [json.loads(p.read_text()) for p in sorted(output.glob("*_seed*.json"))]
    rows = [row for case in cases for row in case["rows"]]
    summary = []
    keys = sorted({(r["group"], r["level"], r["method"]) for r in rows})
    for group, level, method in keys:
        matches = [r for r in rows if (r["group"], r["level"], r["method"]) == (group, level, method)]
        e = np.asarray([r["event_rmse_um"] for r in matches])
        b = [r["beta_only_event_rmse_um"] for r in matches if r["beta_only_event_rmse_um"] is not None]
        summary.append(dict(group=group, level=level, method=method, seeds=len(matches),
                            event_median_um=np.median(e, axis=0).tolist(), max_event_um=float(np.max(e)),
                            pooled_event_rmse_um=float(np.sqrt(np.mean(e**2))),
                            total_pass_events=int(np.sum(e < 10.0)), total_events=int(e.size),
                            beta_pooled_event_rmse_um=None if not b else float(np.sqrt(np.mean(np.asarray(b)**2))),
                            beta_pass_events=None if not b else int(np.sum(np.asarray(b) < 10.0)),
                            beta_max_event_um=None if not b else float(np.max(b))))
    report = dict(protocol=json.loads((output / "protocol.json").read_text()), summary=summary, cases=cases)
    (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--packages", type=Path, required=True)
    parser.add_argument("--seed", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--group", choices=("all", "angle", "snr", "close"), default="all")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.packages.mkdir(parents=True, exist_ok=True)
    protocol = dict(seeds=list(SEEDS), event_intervals_s=EVENTS, angle_offsets_deg=ANGLE_OFFSETS,
                    nominal_range_fft_snr_db=[20, 15, 10], beta_hp_hz=HP_HZ, beta_lp_hz=LP_HZ,
                    excitation_threshold_m=EXCITATION_M, excitation_duration_s=EXCITATION_DURATION_S,
                    regularization_adxl_fraction=REG_ADXL_FRACTION,
                    regularization="lambda=3*Sxx; 75% AoA prior + 25% matched beta; fixed before final runs",
                    estimator="prefix-only causal matched filters and LS; startup uses AoA; all three events scored",
                    fusion="retained single common structural Kalman; equal algorithm for all beta methods",
                    snr_semantics="measured signal/noise power after Hamming range FFT, before four-loop average and DBF",
                    beta_only_semantics="paired output difference vs true-beta run; only where detected points map uniquely; not total-RMSE subtraction",
                    merged_beta_semantics="no unique true beta assigned to coherent mixtures; report total displacement RMSE",
                    generation="same A20 response, N=4, 884.850823 Hz frame stream, ADXL 2 kHz; all scenes at 10 m vertical separation",
                    close_angles_deg=[[3, 9, 15, 20, 21], [3, 9, 15, 20, 20.3], [19.4, 19.7, 20, 20.3, 20.6]],
                    no_future_data="no whole-record FFT or zero-phase filter in beta fit; prefix equality checked",
                    software=dict(numpy=np.__version__))
    (args.output / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    for seed in args.seed:
        if args.group in ("all", "angle"):
            root = args.packages / f"angle_0_seed{seed}"
            if not root.exists():
                configure_package(root, seed, (3, 9, 15, 21, 25), None)
            evaluate(root, "angle", 0, seed, args.output)
        if args.group in ("all", "snr"):
            for snr in (20, 15, 10):
                root = args.packages / f"snr_{snr}_seed{seed}"
                if not root.exists():
                    configure_package(root, seed, (3, 9, 15, 21, 25), snr)
                evaluate(root, "snr", snr, seed, args.output)
        if args.group in ("all", "close"):
            for level, angles in enumerate(protocol["close_angles_deg"], 1):
                root = args.packages / f"close_{level}_seed{seed}"
                if not root.exists():
                    configure_package(root, seed, angles, None)
                evaluate(root, "close", level, seed, args.output)
    aggregate(args.output)


if __name__ == "__main__":
    main()
