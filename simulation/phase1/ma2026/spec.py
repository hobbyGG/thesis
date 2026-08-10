from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Ma2026ComplianceEntry:
    entry_id: str
    paper_source: str
    implementation_files: tuple[str, ...]
    status: str
    algorithm_invariant: str


MA2026_COMPLIANCE: Mapping[str, Ma2026ComplianceEntry] = {
    "ma2026_state_space_model": Ma2026ComplianceEntry(
        entry_id="ma2026_state_space_model",
        paper_source="Ma et al. 2026, Section 3.1 state-space model.",
        implementation_files=("simulation/phase1/ma2026/kalman.py",),
        status="implemented",
        algorithm_invariant="Use the paper LoS phase, phase-rate, and acceleration-aided state transition with radar phase measurement.",
    ),
    "ma2026_predictive_phase_correction": Ma2026ComplianceEntry(
        entry_id="ma2026_predictive_phase_correction",
        paper_source="Ma et al. 2026, Section 3.1 predictive phase correction.",
        implementation_files=("simulation/phase1/ma2026/kalman.py",),
        status="implemented",
        algorithm_invariant="Correct wrapped radar phase by selecting the integer 2*pi offset nearest to the predicted phase.",
    ),
    "ma2026_rangebin_candidate_adapter": Ma2026ComplianceEntry(
        entry_id="ma2026_rangebin_candidate_adapter",
        paper_source="Simulation adapter for applying the target-specific Ma 2026 method to synthetic range FFT outputs; Ma et al. 2026 selects validation targets from the distance spectrum rather than defining an angle-bin frontend.",
        implementation_files=("simulation/phase1/ma2026/rangebin.py", "simulation/phase1/ma2026/method.py"),
        status="adapter",
        algorithm_invariant="Enumerate Range FFT range-bin candidates in distance-spectrum peak order and pass the first candidate to the Ma 2026 target-specific Kalman stage; this adapter is not part of the paper's Section 3.1-3.3 algorithm and does not use beta-grid target selection.",
    ),
    "ma2026_q_energy_selection": Ma2026ComplianceEntry(
        entry_id="ma2026_q_energy_selection",
        paper_source="Ma et al. 2026, Section 3.2 Q energy selection.",
        implementation_files=("simulation/phase1/ma2026/config.py", "simulation/phase1/ma2026/kalman.py"),
        status="implemented",
        algorithm_invariant="Evaluate Q=10^j candidates and select the candidate with minimum corrected/unwrapped measurement phase z_corr energy from Eq. (16).",
    ),
    "ma2026_alpha_linear_fit": Ma2026ComplianceEntry(
        entry_id="ma2026_alpha_linear_fit",
        paper_source="Ma et al. 2026, Section 3.2, Eq. (18), Eq. (19) alpha linear fit.",
        implementation_files=("simulation/phase1/ma2026/alpha.py",),
        status="implemented",
        algorithm_invariant="Fit the radar-to-accelerometer phase scale as the paper alpha parameter by band-pass linear regression; the default experiment band is [0.5 Hz, 3 Hz], while scenario adapters may raise the upper cutoff to cover configured structural frequencies.",
    ),
    "ma2026_alpha_calibration_phase_adapter": Ma2026ComplianceEntry(
        entry_id="ma2026_alpha_calibration_phase_adapter",
        paper_source="Simulation wrapper detail: Ma et al. 2026 defines alpha calibration from radar-derived corrected/unwrapped phase, but does not prescribe how synthetic Range FFT adapter inputs should provide that calibration phase.",
        implementation_files=("simulation/phase1/ma2026/method.py",),
        status="adapter",
        algorithm_invariant="Use supplied corrected LoS phase for the Ma 2026 alpha fit when simulation truth provides it; otherwise fall back to ordinary wrapped-phase unwrapping as an input adapter. Do not generate the alpha-fit input by running an initial-alpha Kalman pass.",
    ),
    "ma2026_convergence_time": Ma2026ComplianceEntry(
        entry_id="ma2026_convergence_time",
        paper_source="Ma et al. 2026, Section 3.3 convergence time.",
        implementation_files=("simulation/phase1/ma2026/convergence.py",),
        status="implemented",
        algorithm_invariant="Compute the minimum convergence time from the steady-state Kalman-gain convolution coefficients.",
    ),
    "ma2026_target_input_boundary": Ma2026ComplianceEntry(
        entry_id="ma2026_target_input_boundary",
        paper_source="Ma et al. 2026 target-specific paper method; target selection is outside the paper algorithm.",
        implementation_files=("simulation/phase1/ma2026/rangebin.py", "simulation/phase1/ma2026/method.py"),
        status="adapter",
        algorithm_invariant="Preserve a target-specific paper method boundary; automatic candidates come from Range FFT range bins, not from Range-Angle or angle-bin selection.",
    ),
}


def compliance_by_id(entry_id: str) -> Ma2026ComplianceEntry:
    return MA2026_COMPLIANCE[entry_id]
