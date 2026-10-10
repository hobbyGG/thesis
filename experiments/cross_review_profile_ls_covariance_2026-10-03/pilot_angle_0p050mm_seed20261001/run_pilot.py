"""Three fixed routes, local MUSIC-seeded geometry; no cloud reproduction."""
import hashlib
import json
import sys
import tempfile
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / 'spatial_recovery_rebuilt_validation_2026-10-03')]
import rebuild_validation as rv
from spatial_recovery_rebuilt.calibration_only import calibration_only_wrapper as cw
from algorithm.io import load_capture_package
from algorithm.config import AlgorithmConfig
from algorithm.kalman import run_fixed_beta_kalman, _cold_start_count
from algorithm.types import RadarInput

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, value):
    with (OUT / name).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')

config = AlgorithmConfig(sample_rate_hz=100.0)
protocol = dict(seed=20261001, stratum='low_motion_0p050mm', requested_rms_mm=0.05,
    deltas_deg=[0, -1, 1], calibration_frames=[0, 199], test_frames=[200, 399],
    change='both steering and beta; fixed range bins and selected identities',
    beta_only_not_run='would hold complex IQ observations fixed and change only conversion scale',
    reference='post-run truth mean on same first test cold-start indices as estimator; no fitted alignment',
    legacy_reference='also report prior full-record elapsed <= 0.20s reference for comparison',
    cold_start='unchanged retained estimator: test-prefix phase bias and residual R; NOT strict calibration-only initialization',
    config=asdict(config), scoring_after_all_routes=True, raw_arrays_retained=False,
    input='local scratch 1Hz sine generator with package_builder exports, NOT A20 physical response or cloud 400-402')
write('protocol.json', protocol)
sources = sorted(set([str(Path(__file__).relative_to(ROOT)),
    'experiments/cross_review_profile_ls_covariance_2026-10-03/pilot_frozen_beta_angle_v1_seed20261001_low_motion_0p005mm/run_pilot.py',
    'spatial_recovery_rebuilt_validation_2026-10-03/rebuild_validation.py',
    'spatial_recovery_rebuilt/calibration_only/calibration_only_wrapper.py'] +
    [str(p.relative_to(ROOT)) for folder in ['algorithm', 'paper_bridge_simulation'] for p in (ROOT/folder).glob('*.py')]))
manifest = dict(command=f'python3 {Path(__file__).relative_to(ROOT)}', python=sys.version,
    numpy=np.__version__, sources={s:digest(ROOT/s) for s in sources})
write('manifest.json', manifest)

with tempfile.TemporaryDirectory(prefix='angle050-') as temporary:
    package = Path(temporary)/'generated'
    rv._write_scratch_package(package, stratum_name=protocol['stratum'], requested_rms_mm=0.05, seed=20261001)
    contract = rv.verify_package(package)
    guards = rv.freeze_guards(package)
    guard_test = rv.verify_frozen_test(package, guards)
    assert guard_test['passed'] and all(contract.values())
    ep = Path(temporary)/'estimator'
    cw._copy_estimator_package(package, ep)
    assert not (ep/'truth').exists() and not (ep/'paper_response_metadata.json').exists()
    capture = load_capture_package(ep)
    assert capture.truth_displacement_m is None and capture.truth_time_ns is None
    input_hashes = {str(p.relative_to(ep)):digest(p) for p in ep.rglob('*') if p.is_file()}
    geometry, selected, initial_r, scores, detection = cw._calibration_geometry(capture)
    def record(g, sel, r, sc):
        return dict(angle_deg=g.angle_deg.tolist(), beta=g.measured_beta.tolist(),
            range_bins=g.range_bins.tolist(), selected=sel.tolist(), initial_r=r.tolist(), scores=sc.tolist())
    frozen = record(geometry, selected, initial_r, scores)
    frozen_hash = hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()
    # Fence test is geometry only, not another displacement estimator route.
    changed_adc = capture.adc_cube.copy()
    changed_adc[200:] *= 10j
    altered = replace(capture, adc_cube=changed_adc)
    g2, s2, r2, sc2, _ = cw._calibration_geometry(altered)
    assert record(g2,s2,r2,sc2) == frozen
    rt = capture.radar_time_ns[200:400]
    accel = cw._test_acceleration(capture, rt)
    outputs = []
    for delta in protocol['deltas_deg']:
        angle = geometry.angle_deg + delta
        beta = 1 / np.abs(np.cos(np.deg2rad(angle)))
        perturbed = replace(geometry, angle_deg=angle, measured_beta=beta)
        target = cw._test_targets_from_frozen_geometry(capture, perturbed)
        radar = RadarInput(beta, target.wrapped_phase_rad, target.available_mask,
            selected.copy(), initial_r.copy(), scores.copy(),
            {'radar_time_ns':rt, 'frame_period_s':float(np.median(np.diff(rt))*1e-9)})
        result = run_fixed_beta_kalman(radar, accel, config)
        assert np.isfinite(result.q_hat_m).all()
        outputs.append((delta, beta, result.q_hat_m.copy(), _cold_start_count(radar, config, 200)))
    # Only now load truth for scoring; no truth-derived offset touches estimates.
    truth = np.load(package/'truth/displacement_m.npy', allow_pickle=False)
    tt = np.load(package/'truth/time_ns.npy', allow_pickle=False)
    test_truth = np.interp(rt.astype(float), tt.astype(float), truth)
    old_truth = cw._reference_and_test_truth(package, rt)
    rows=[]
    for delta, beta, q, count in outputs:
        matched = test_truth - np.mean(test_truth[:count])
        error = q - matched
        rows.append(dict(delta_deg=delta, beta=beta.tolist(),
            projection_relative_error=(beta/geometry.measured_beta-1).tolist(),
            q_hat_rms_mm=float(np.sqrt(np.mean(q*q))*1000),
            truth_physical_rms_mm=float(np.sqrt(np.mean(test_truth**2))*1000),
            truth_matched_reference_rms_mm=float(np.sqrt(np.mean(matched**2))*1000),
            matched_reference_rmse_mm=float(np.sqrt(np.mean(error**2))*1000),
            signed_bias_mm=float(np.mean(error)*1000),
            legacy_reference_rmse_mm=float(np.sqrt(np.mean((q-old_truth)**2))*1000),
            reference_delta_matched_minus_legacy_mm=float(np.mean(matched-old_truth)*1000),
            cold_start_count=count, finite_coverage=float(np.isfinite(q).mean())))
    assert all(digest(ROOT/s)==h for s,h in manifest['sources'].items())
    report=dict(protocol=protocol, geometry=frozen, geometry_hash=frozen_hash,
        input_sha256=input_hashes, guards=guards, guard_test=guard_test, contract=contract,
        truth_free=True, geometry_test_perturbation_invariant=True, rows=rows,
        limitation='Combined steering/beta sensitivity with test-prefix cold start; not beta-only or strict held-out initialization; finite coverage is not uncertainty coverage.')
    write('report.json',report)
    print(json.dumps(dict(geometry=frozen, rows=rows),indent=2))
