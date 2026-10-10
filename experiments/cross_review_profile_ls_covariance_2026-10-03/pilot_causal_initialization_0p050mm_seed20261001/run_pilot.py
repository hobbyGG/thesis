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
    deltas_deg=[0], calibration_frames=[0, 199], test_frames=[200, 399],
    change='initialization only: retained 20-sample residual warmup versus first-sample bias, prior R=9 and P0=diag(25,400); unchanged causal posterior R adaptation',
    beta_only_not_run='would hold complex IQ observations fixed and change only conversion scale',
    reference='q0 is first test output; compare q_hat-q_hat[0] to truth-truth[0]; additionally preserve original warmup mean-reference score',
    legacy_reference='also report prior full-record elapsed <= 0.20s reference for comparison',
    cold_start='unchanged retained estimator: test-prefix phase bias and residual R; NOT strict calibration-only initialization',
    config=asdict(config), scoring_after_all_routes=True, raw_arrays_retained=False,
    input='local scratch 1Hz sine generator with package_builder exports, NOT A20 physical response or cloud 400-402')
protocol['routes']=['warmup20_retrospective_offline_comparator','causal_first_sample']; protocol['causal_config']=asdict(replace(config,cold_start_duration_s=0.0,cold_start_r_mode='fixed')); protocol['warmup_latency_s']=0.19; protocol['no_retroactive_online_output']=True
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
    target = cw._test_targets_from_frozen_geometry(capture, geometry)
    radar = RadarInput(geometry.measured_beta.copy(), target.wrapped_phase_rad,
        target.available_mask, selected.copy(), initial_r.copy(), scores.copy(),
        {'radar_time_ns':rt, 'frame_period_s':float(np.median(np.diff(rt))*1e-9)})
    assert target.available_mask[selected,0].all()
    causal_config = replace(config, cold_start_duration_s=0.0, cold_start_r_mode='fixed')
    prior_radar = replace(radar, initial_r=np.full(initial_r.shape, config.initial_measurement_variance))
    from algorithm.kalman import _cold_start_statistics
    cb, cr = _cold_start_statistics(prior_radar, causal_config)
    assert np.allclose(cb[selected], target.wrapped_phase_rad[selected,0])
    assert np.all(cr == 9.0)
    warm = run_fixed_beta_kalman(radar, accel, config)
    causal = run_fixed_beta_kalman(prior_radar, accel, causal_config)
    # Causal fence: future radar samples cannot affect earlier displacement.
    future_phase = radar.wrapped_phase_rad.copy()
    future_phase[:,100:] += 0.8
    future_result = run_fixed_beta_kalman(replace(prior_radar, wrapped_phase_rad=future_phase), accel, causal_config)
    assert np.array_equal(causal.q_hat_m[:100], future_result.q_hat_m[:100])
    # Scoring only after both routes and fence complete.
    truth = np.load(package/'truth/displacement_m.npy', allow_pickle=False)
    tt = np.load(package/'truth/time_ns.npy', allow_pickle=False)
    tq = np.interp(rt.astype(float),tt.astype(float),truth)
    ref_first = tq-tq[0]
    ref_mean = tq-np.mean(tq[:20])
    old_truth = cw._reference_and_test_truth(package,rt)
    rows=[]
    for name,result in [('warmup20_retrospective_offline_comparator',warm),('causal_first_sample',causal)]:
        q=result.q_hat_m
        assert np.isfinite(q).all()
        first_q=q-q[0]
        err=first_q-ref_first
        rows.append(dict(route=name,full_first_reference_rmse_mm=float(np.sqrt(np.mean(err**2))*1000),
            full_bias_mm=float(np.mean(err)*1000),q_first_reference_rms_mm=float(np.sqrt(np.mean(first_q**2))*1000),
            original_warmup_mean_reference_rmse_mm=float(np.sqrt(np.mean((q-ref_mean)**2))*1000) if name.startswith('warmup') else None,
            legacy_reference_rmse_mm=float(np.sqrt(np.mean((q-old_truth)**2))*1000) if name.startswith('warmup') else None,
            initial_output_m=float(q[0]),finite_coverage=float(np.isfinite(q).mean()),scored_samples=len(q),
            latency_s=0.19 if name.startswith('warmup') else 0.0,
            online_retrospective_outputs_allowed=False,
            initial_r=result.extra['initial_r'].tolist()))
    previous=json.loads((ROOT/'experiments/cross_review_profile_ls_covariance_2026-10-03/pilot_angle_0p050mm_seed20261001/report.json').read_text())
    assert input_hashes==previous['input_sha256']
    assert frozen==previous['geometry']
    assert all(digest(ROOT/s)==h for s,h in manifest['sources'].items())
    write('report.json',dict(rows=rows,geometry=frozen,source_input_sha256=input_hashes,
        exact_input_hash_match_to_previous_pilot=True,truth_free=True,geometry_fence_passed=True,
        future_radar_prefix_invariance_passed=True,contract=contract,guards=guard_test,
        config_shared_Q_P0_ADXL=True,prior_R=9.0,prior_P0=[25.0,400.0],
        coldstart_counts=[20,1],reference='first test sample for both outputs and truth; post-run only',
        limitation='Warmup route is explicitly retrospective offline comparator, not online output. Causal route retains posterior adaptive R. Geometry still needs 200 calibration frames. One synthetic seed cannot establish general superiority or absolute displacement accuracy.'))
    print(json.dumps(rows,indent=2))
