from __future__ import annotations
import json, tempfile, hashlib, sys
from pathlib import Path
import numpy as np
ROOT=Path("/Users/umep/thesis")
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/"spatial_recovery_rebuilt_validation_2026-10-03"))
import rebuild_validation as rv
from spatial_recovery_rebuilt.calibration_only import calibration_only_wrapper as cw
from algorithm.io import load_capture_package
from algorithm.config import AlgorithmConfig
from algorithm.kalman import run_fixed_beta_kalman
from algorithm.types import RadarInput
from algorithm.frontend import TargetData
OUT=ROOT/"experiments/cross_review_profile_ls_covariance_2026-10-03/pilot_frozen_beta_angle_v1_seed20261001_low_motion_0p005mm"
OUT.mkdir(parents=True,exist_ok=False)
seed=20261001; stratum="low_motion_0p005mm"; rms=0.005; deltas=[0.0,-1.0,1.0]
def sha_obj(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def run_delta(capture,geometry,selected,initial_r,scores,delta,accel,radar_rate,truth_package):
    angles=np.asarray(geometry.angle_deg,float)+delta; beta=1.0/np.abs(np.cos(np.deg2rad(angles)))
    n=angles.size; tg=TargetData(np.zeros((n,200),complex),np.zeros((n,200)),np.zeros((n,200),bool),angles,beta,np.asarray(geometry.range_bins),np.asarray(geometry.angle_bins),np.asarray(geometry.range_m))
    test_tg=cw._test_targets_from_frozen_geometry(capture,tg)
    rt=np.asarray(capture.radar_time_ns[cw.CALIBRATION_FRAMES:cw.RADAR_FRAMES],dtype=np.int64)
    radar=RadarInput(test_tg.measured_beta,test_tg.wrapped_phase_rad,test_tg.available_mask,np.asarray(selected,int),np.asarray(initial_r,float),np.asarray(scores,float),{"angle_deg":test_tg.angle_deg,"range_bins":test_tg.range_bins,"angle_bins":test_tg.angle_bins,"range_m":test_tg.range_m,"radar_time_ns":rt,"radar_mode":"frame_calibration_only","frame_period_s":float(np.median(np.diff(rt))*1e-9),"geometry_source":"frames_0_199_frozen","delta_theta_deg":delta})
    result=run_fixed_beta_kalman(radar,accel,AlgorithmConfig(sample_rate_hz=float(radar_rate)))
    truth=cw._reference_and_test_truth(truth_package,rt); q=np.asarray(result.q_hat_m,float); finite=np.isfinite(q); err=q[finite]-truth[finite]
    return {"delta_theta_deg":delta,"finite_test_coverage":float(np.mean(finite)),"signed_bias_m":float(np.mean(err)) if err.size else None,"test_rmse_m":float(np.sqrt(np.mean(err*err))) if err.size else None,"target_count":int(radar.selected_indices.size),"output_samples":int(q.size),"beta_min":float(np.min(beta)),"beta_max":float(np.max(beta))}
with tempfile.TemporaryDirectory(prefix="pilot-angle-v1-") as td:
    pkg=Path(td)/"capture"; realized=rv._write_scratch_package(pkg,stratum_name=stratum,requested_rms_mm=rms,seed=seed); contract=rv.verify_package(pkg); guards=rv.freeze_guards(pkg); frozen=rv.verify_frozen_test(pkg,guards)
    with tempfile.TemporaryDirectory(prefix="pilot-estimator-") as et:
        ep=Path(et)/"capture"; cw._copy_estimator_package(pkg,ep); cap=load_capture_package(ep); geometry,selected,initial_r,scores,detection=cw._calibration_geometry(cap); radar0,accel,_,rate=cw.build_calibration_only_inputs(cap)
        geom_record={"range_bins":np.asarray(geometry.range_bins,int).tolist(),"angle_bins":np.asarray(geometry.angle_bins,int).tolist(),"angle_deg":np.asarray(geometry.angle_deg,float).tolist(),"measured_beta":np.asarray(geometry.measured_beta,float).tolist(),"selected_indices":np.asarray(selected,int).tolist()}
        rows=[run_delta(cap,geometry,selected,initial_r,scores,d,accel,rate,pkg) for d in deltas]
        audit={"truth_present_in_estimator":(ep/"truth").exists(),"paper_response_metadata_present":(ep/"paper_response_metadata.json").exists(),"q_proxy_used_by_estimator":False}
    report={"schema":"thesis.frozen_beta_angle_sensitivity_pilot.v1","status":"completed","seed":seed,"stratum":stratum,"requested_q_true_rms_mm":rms,"input_source":"paper_bridge_simulation.package_builder via rebuild_validation.py","calibration_frames":[0,199],"test_frames":[200,399],"estimator_truth_free_audit":audit,"package_contract":contract,"frozen_test_guard":frozen,"frozen_geometry":geom_record,"frozen_geometry_hash":sha_obj(geom_record),"rows":rows,"truth_role":"post_run_scoring_only","claims":"descriptive frozen-beta angle sensitivity; synthetic pilot only","matrix_expanded":False}
(OUT/"pilot_report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
(OUT/"protocol.json").write_text(json.dumps({"experiment":"calibration_only_frozen_beta_angle_sensitivity_v1_pilot","seed":seed,"stratum":stratum,"delta_theta_deg":deltas,"calibration_frames":[0,199],"test_frames":[200,399],"truth_role":"post_run_scoring_only","raw_arrays_retained":False},indent=2,ensure_ascii=False)+"\n")
md="# Frozen beta/angle sensitivity v1 pilot\n\n"
md+="Seed %s, stratum %s, requested RMS %s mm; one synthetic capture package, calibration frames 0-199, test frames 200-399.\n\n" % (seed,stratum,rms)
md+="Estimator copy removed truth/ and paper_response_metadata.json; truth was used only after estimation for scoring. Geometry, target selection, and base beta came from calibration frames only. Test projection used frozen geometry with declared angle offsets 0, -1, +1 degrees.\n\n"
md+="| delta theta (deg) | finite coverage | signed bias (mm) | RMSE (mm) | targets |\n|---:|---:|---:|---:|---:|\n"
for r in rows: md+="| %+.1f | %.6f | %.9f | %.9f | %d |\n" % (r["delta_theta_deg"],r["finite_test_coverage"],r["signed_bias_m"]*1e3,r["test_rmse_m"]*1e3,r["target_count"])
md+="\nThis is a bounded synthetic sensitivity pilot. It does not reproduce the cloud profile-LS artifact, establish field accuracy, or authorize the 40-seed matrix.\n"
(OUT/"PILOT_REPORT.md").write_text(md)
print(json.dumps({"output":str(OUT),"rows":rows},indent=2))

