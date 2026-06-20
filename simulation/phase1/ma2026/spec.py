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
    "ma2026_q_energy_selection": Ma2026ComplianceEntry(
        entry_id="ma2026_q_energy_selection",
        paper_source="Ma et al. 2026, Section 3.2 Q energy selection.",
        implementation_files=("simulation/phase1/ma2026/config.py", "simulation/phase1/ma2026/kalman.py"),
        status="implemented",
        algorithm_invariant="Evaluate the paper Q candidates and select the candidate with minimum corrected-phase energy.",
    ),
    "ma2026_alpha_linear_fit": Ma2026ComplianceEntry(
        entry_id="ma2026_alpha_linear_fit",
        paper_source="Ma et al. 2026, Section 3.2, Eq. (18), Eq. (19) alpha linear fit.",
        implementation_files=("simulation/phase1/ma2026/alpha.py",),
        status="implemented",
        algorithm_invariant="Fit the radar-to-accelerometer displacement scale as the paper alpha parameter by linear regression.",
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
        implementation_files=("simulation/phase1/ma2026/rangebin.py", "simulation/phase1/ma2026/calibration.py"),
        status="adapter",
        algorithm_invariant="Preserve a target-specific paper method boundary; range-bin automatic selection is a simulation adapter.",
    ),
}


def compliance_by_id(entry_id: str) -> Ma2026ComplianceEntry:
    return MA2026_COMPLIANCE[entry_id]
