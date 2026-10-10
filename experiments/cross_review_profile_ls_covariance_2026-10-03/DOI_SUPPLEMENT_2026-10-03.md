# DOI supplement for the cross-review

Date: 2026-10-03  
Scope: original papers that bound the five assumptions in `AUDIT_NOTE.md`. This
file is additive; it does not change the algorithm or the design-only protocol.

Only the DOI entries below were checked against a publisher, IEEE, institutional
repository, or DOI metadata page during this review. A DOI is evidence for the
paper's method and assumptions; it is not evidence that the thesis estimator
achieves the paper's reported accuracy.

## Verified sources

| Assumption | Original source | DOI | What it supports here | Boundary for this thesis |
|---|---|---|---|---|
| Profile objective / off-grid identifiability | Y. Zhang, Z. Ye, X. Xu, N. Hu, “Off-grid DOA estimation using array covariance matrix and block-sparse Bayesian learning,” *Signal Processing*, 98 (2014), 197–201. [Publisher record](https://www.sciencedirect.com/science/article/pii/S0165168413004581) | `10.1016/j.sigpro.2013.11.022` | Explicit off-grid steering-vector model and covariance-domain estimation. | This is an off-grid sparse-Bayesian method, not evidence for the thesis profile-LS objective or its held-out behavior. |
| Profile objective / classical array limit | P. Stoica and A. Nehorai, “MUSIC, maximum likelihood, and Cramér–Rao bound,” *IEEE TASSP*, 37(5), 720–741 (1989). [IEEE record](https://ieeexplore.ieee.org/document/17564/) | `10.1109/29.17564` | Classical ML/MUSIC performance and resolution assumptions. | Does not validate the local geometry refinement implementation. |
| Coherent or near-coherent source bias | T.-J. Shan, M. Wax, T. Kailath, “On spatial smoothing for direction-of-arrival estimation of coherent signals,” *IEEE TASSP*, 33(4), 806–811 (1985). [IEEE record](https://ieeexplore.ieee.org/document/1164649/) | `10.1109/TASSP.1985.1164649` | Rank-deficiency mechanism for coherent sources and the spatial-smoothing remedy. | The same-range mechanism check does not yet test coherent/near-coherent robustness or identifiability limits. |
| Phase reference / beta and multi-sensor displacement | Z. Ma, J. Choi, L. Yang, H. Sohn, “Structural displacement estimation using accelerometer and FMCW millimeter wave radar,” *MSSP*, 182, 109582 (2023). [Institutional record](https://pure.kaist.ac.kr/en/publications/structural-displacement-estimation-using-accelerometer-and-fmcw-m/) | `10.1016/j.ymssp.2022.109582` | Prior use of a short calibration interval, environmental radar targets, and a direction-conversion factor with acceleration. | This is prior art and a boundary reference; it is not a baseline run or a claim that the thesis beta is absolutely correct. |
| Phase reference / range-angle phase tracking | J. Guo et al., “Measuring Micrometer-Level Vibrations With mmWave Radar,” *IEEE TMC*, 22(4), 2248–2261 (2023). [IEEE Computer Society record](https://www.computer.org/csdl/journal/tm/2023/04/09563210/1xvtheduFDa) | `10.1109/TMC.2021.3118349` | Range-angle processing, IQ geometry, and multi-signal micromotion measurement context. | Controlled mmVib evidence does not establish field accuracy, beta correctness, or the thesis shared-state estimator. |
| Same-range identifiability / angle separation | Y. Xiong et al., “Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View,” *Research*, 2021, 9787484. [Publisher record](https://spj.science.org/doi/10.34133/2021/9787484) | `10.34133/2021/9787484` | Range-angle joint micromotion tracking and explicit clutter/adjacent-angle mechanisms. | The thesis `same_range_merge_mechanism_v2` remains a bounded synthetic mechanism check; it does not inherit general resolution or coherent-source claims. |
| Correlated fusion / unknown cross-covariance | J. Ajgl et al., “Covariance Intersection fusion with element-wise partial knowledge of correlation,” *Automatica*, 141 (2022), 110168. [Publisher record](https://www.sciencedirect.com/science/article/abs/pii/S0005109822000127) | `10.1016/j.automatica.2022.110168` | Why unknown cross-correlation requires an explicit fusion rule and why diagonal weights alone are not full-covariance fusion. | This is not a result for the P3 route: current P3 records innovation correlation, not truth-error covariance, and has no full-GLS/coverage claim. |
| Reference-free displacement fusion | S. Cho et al., “Reference-Free Displacement Estimation of Bridges Using Kalman Filter-Based Multimetric Data Fusion,” *Journal of Sensors*, 2016, 3791856. [DOI-bearing record](https://www.airitilibrary.com/Article/Detail/P20160525003-201612-201703060005-201703060005-264-272-127) | `10.1155/2016/3791856` | Original reference-free acceleration/multimetric state-space fusion context. | It does not establish radar angle geometry, beta sensitivity, or the shared structural-state covariance model used here. |

## Pending or not directly matched

- A paper with a DOI that directly matches the thesis **complex profile-LS geometry
  objective** was not identified in the current local scan. The off-grid DOA paper
  above is an adjacent method and must be described as such.
- The local PDF titled “Acceleration-aided Kalman filtering for joint phase
  denoising and unwrapping in FMCW radar-based displacement monitoring” was not
  assigned a verified DOI in this pass; keep it as **DOI pending** until the
  publisher metadata is checked.
- No DOI is used here to justify a 0.01 mm claim, a field-accuracy claim, a causal
  fusion gain, or a strict held-out result. Those remain experiment questions.

## Minimal protocol implication

The literature supports keeping the next probe narrow: use calibration-only
frozen geometry/beta, apply only the pre-registered test angle offsets, and score
signed bias/RMSE after estimation. A later covariance probe must estimate and
report the declared cross-covariance and conditioning; it must not relabel P3's
innovation correlation as a truth-error covariance or a full GLS result.
