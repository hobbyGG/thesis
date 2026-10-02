#!/usr/bin/env python3
"""Direct offline array-IQ mechanism experiment; see pre-run PROTOCOL.md."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks

ROOT = Path(__file__).resolve().parent
LAMBDA_MM, FS, N, M, CAL = 4.0, 100.0, 256, 8, 128
NOISE_SIGMA = 10**(-35/20)/np.sqrt(2)
GRID = np.arange(-60, 60.001, 0.25)
POS = np.arange(M)-(M-1)/2
CASES = {
    'close_benign': ([25,29],[1,.8],[.15,-.30]),
    'separated_benign': ([-10,45],[1,.8],[.15,-.30]),
    'separated_unequal': ([-10,45],[1,.5],[.15,-.30]),
    'close_destructive': ([25,29],[1,1],[0,np.pi]),
    'coincident_cancel': ([27,27],[1,1],[0,np.pi]),
    'symmetric_control': ([-25,25],[1,.8],[.15,-.30]),
}
MODES = ['range_only','merge','split_ls']

def steering(angles):
    return np.exp(1j*np.pi*POS[:,None]*np.sin(np.deg2rad(np.atleast_1d(angles)))[None,:])

DICT = steering(GRID)

def generate(case_name,seed):
    """Truth/data generation only. Fixed additive noise in every scene."""
    angles,amps,phases=CASES[case_name]
    rng=np.random.default_rng(seed)
    p=rng.uniform(-np.pi,np.pi)
    t=np.arange(N)/FS
    q=.8*np.sin(2*np.pi*3*t+p)+.2*np.sin(2*np.pi*5*t+.43-.2*p)
    c=np.cos(np.deg2rad(angles))
    sources=np.array(amps)[None,:]*np.exp(1j*(np.array(phases)[None,:]+4*np.pi/LAMBDA_MM*q[:,None]*c[None,:]))
    z=sources@steering(angles).T
    z+=NOISE_SIGMA*(rng.standard_normal(z.shape)+1j*rng.standard_normal(z.shape))
    return z,q

def geometry(cal_iq):
    # Data is time x sensors. R = E[x x^H], NOT E[conj(x) x^T].
    R=cal_iq.T@cal_iq.conj()/len(cal_iq)
    power=np.maximum(np.einsum('mg,mn,ng->g',DICT.conj(),R,DICT).real/M**2,0)
    peaks,_=find_peaks(power,distance=48,prominence=max(power.max()*.01,1e-15))
    order=peaks[np.argsort(power[peaks])[::-1]]
    if not len(order): return [],power
    keep=[int(i) for i in order if power[i]>=.18*power[order[0]]][:2]
    return GRID[keep].tolist(),power

def estimator(iq,mode):
    """No truth, scene angles, phases or amplitudes accepted by this API."""
    cal=iq[:CAL]; test=iq[CAL:]
    angles,power=geometry(cal)
    out={'mode':mode,'angles_deg':angles,'covered':False,'failure':None}
    if not angles:
        return dict(out,failure='no_calibration_angle_peak'),None
    if mode=='split_ls':
        if len(angles)<2:
            return dict(out,failure='fewer_than_two_calibration_angle_peaks'),None
        A=steering(angles)
        cond=float(np.linalg.cond(A))
        out['steering_condition']=cond
        if cond>20:
            return dict(out,failure='ill_conditioned_split'),None
        # Extraction is Y = X (A^+)^T; Y rows are time, columns are sources.
        E=np.linalg.pinv(A).T
        used=np.array(angles)
    elif mode=='merge':
        E=steering([angles[0]]).conj()/M
        used=np.array([angles[0]])
    elif mode=='range_only':
        E=np.zeros((M,1),complex);E[0,0]=1
        used=np.array([angles[0]])
    else: raise ValueError(mode)
    ycal=cal@E; y=test@E
    gains=np.linalg.norm(E,axis=0)
    floor=5*NOISE_SIGMA*gains
    amp=np.abs(y)
    out['min_test_abs']=amp.min(axis=0).tolist()
    out['noise_gain']=gains.tolist()
    out['amplitude_floor']=floor.tolist()
    if np.any(amp.min(axis=0)<floor):
        return dict(out,failure='test_amplitude_guard'),None
    c=np.cos(np.deg2rad(used))
    if np.any(c<=.05):
        return dict(out,failure='geometry_guard'),None
    phase=np.unwrap(np.angle(y*np.conj(y[0,:])[None,:]),axis=0)
    qs=phase*LAMBDA_MM/(4*np.pi*c[None,:])
    weights=np.mean(np.abs(ycal)**2,axis=0)
    weights=weights/weights.sum()
    qhat=qs@weights
    out['weights']=weights.tolist()
    out['covered']=bool(np.all(np.isfinite(qhat)))
    if not out['covered']:out['failure']='nonfinite'
    return out,qhat

def score(out,qhat,truth):
    # Simulation truth arrives only after the estimator returns.
    out=dict(out)
    if not out['covered']:
        out.update(rmse_mm=None,max_abs_error_mm=None,corr=None,success_0p01mm=False)
        return out
    ref=truth[CAL:]-truth[CAL]
    err=qhat-ref
    out.update(rmse_mm=float(np.sqrt(np.mean(err**2))),max_abs_error_mm=float(np.max(np.abs(err))),
               corr=float(np.corrcoef(ref,qhat)[0,1]),success_0p01mm=bool(np.sqrt(np.mean(err**2))<.01))
    return out

def unit_checks():
    theta=25.
    t=np.arange(N)/FS;q=.3*np.sin(2*np.pi*3*t)
    x=np.exp(1j*4*np.pi/LAMBDA_MM*q*np.cos(np.deg2rad(theta)))[:,None]@steering([theta]).T
    angles,power=geometry(x[:CAL])
    assert angles[0]==theta,(theta,angles)
    direct=np.mean(np.abs(x[:CAL]@DICT.conj()/M)**2,axis=0)
    covdiff=float(np.max(np.abs(direct-power)))
    assert covdiff<1e-12,covdiff
    r,qhat=estimator(x,'merge')
    rmse=float(np.sqrt(np.mean((qhat-(q[CAL:]-q[CAL]))**2)))
    assert r['covered'] and rmse<1e-12,(r,rmse)
    cancel=x+np.exp(1j*np.pi)*x
    assert np.max(np.abs(cancel))<1e-12
    return {'positive_angle_check_deg':angles[0],'covariance_vs_direct_max_abs':covdiff,
            'single_source_noiseless_rmse_mm':rmse,'identical_opposite_max_abs':float(np.abs(cancel).max())}

def summarize(rows):
    summaries={}
    for case in CASES:
        rr=[r for r in rows if r['case']==case]
        summaries[case]={}
        for mode in MODES:
            ss=[r['routes'][mode] for r in rr]
            vals=[s['rmse_mm'] for s in ss if s['covered']]
            summaries[case][mode]={'n':len(ss),'coverage':sum(s['covered'] for s in ss)/len(ss),
                'covered':len(vals),'success_0p01mm_all_trials':sum(s['success_0p01mm'] for s in ss)/len(ss),
                'median_rmse_mm':float(np.median(vals)) if vals else None,
                'p90_rmse_mm':float(np.quantile(vals,.9)) if vals else None,
                'max_rmse_mm':max(vals) if vals else None,
                'failure_counts':{reason:sum(s['failure']==reason for s in ss) for reason in sorted({s['failure'] for s in ss if s['failure']})}}
        paired=[r for r in rr if r['routes']['merge']['covered'] and r['routes']['split_ls']['covered']]
        summaries[case]['paired_split_vs_merge']={'n':len(paired),
            'split_wins':sum(r['routes']['split_ls']['rmse_mm']<r['routes']['merge']['rmse_mm'] for r in paired),
            'median_split_minus_merge_rmse_mm':float(np.median([r['routes']['split_ls']['rmse_mm']-r['routes']['merge']['rmse_mm'] for r in paired])) if paired else None}
    return summaries

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',nargs='+',type=int,default=[100]);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();checks=unit_checks()
    rows=[]
    for seed in args.seeds:
        for name in CASES:
            x,truth=generate(name,seed)
            routes={}
            for mode in MODES:
                result,estimate=estimator(x,mode)
                routes[mode]=score(result,estimate,truth)
            rows.append({'case':name,'seed':seed,'routes':routes})
    payload={'protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest(),
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope':'Simplified same-range ULA IQ mechanism; development study, not full radar or real-data validation',
        'constants':{'lambda_mm':LAMBDA_MM,'fs_hz':FS,'samples':N,'sensors':M,'cal_samples':CAL,'noise_sigma':NOISE_SIGMA},
        'cases':CASES,'seeds':args.seeds,'unit_checks':checks,'summary':summarize(rows),'rows':rows}
    args.out.write_text(json.dumps(payload,indent=2,sort_keys=True))
    print(json.dumps({'unit_checks':checks,'summary':payload['summary']},indent=2))
if __name__=='__main__':main()
