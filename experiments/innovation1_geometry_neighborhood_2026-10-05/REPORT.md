# Geometry-neighborhood selector holdout: bounded seed set

This independent run uses one seed per geometry cell and the frozen selector from seed213. It does not modify corrected v2, seed212, or seed213.

- Cells: **9**; semantic rows: **37**
- Selected accepted: **13/37 (35.1%)**
- Selected rejected: **24/37**
- Accepted with post-run RMSE > 0.01 mm: **5/13**
- Truth is used only after route selection for scoring; no fallback is allowed.

## Per-cell action and output

| Cell | Seed | Requested span/gap | Rows | Actions | Accepted RMSE mm |
|---|---:|---:|---:|---|---:|
| `span24_gap005` | 3000 | 24.0° / 0.05 | 4 | balanced_pair=abstain(ambiguous_narrow_peak_span); unequal_pair=split_ls; opposed_phase_pair=abstain(ambiguous_narrow_peak_span); coincident_cancel_control=split_ls(test_amplitude_guard) | 0.011405 |
| `span28_gap005` | 3001 | 28.0° / 0.05 | 4 | balanced_pair=split_ls; unequal_pair=split_ls; opposed_phase_pair=abstain(ambiguous_narrow_peak_span); coincident_cancel_control=abstain(ambiguous_projection_gap) | 0.012834, 0.010405 |
| `span30_gap005` | 3002 | 30.0° / 0.05 | 4 | balanced_pair=split_ls; unequal_pair=split_ls; opposed_phase_pair=abstain(ambiguous_narrow_peak_span); coincident_cancel_control=split_ls(test_amplitude_guard) | 0.005519, 0.004438 |
| `span32_gap005` | 3003 | 32.0° / 0.05 | 4 | balanced_pair=split_ls; unequal_pair=split_ls; opposed_phase_pair=abstain(ambiguous_narrow_peak_span); coincident_cancel_control=split_ls(test_amplitude_guard) | 0.004193, 0.003304 |
| `span36_gap005` | 3004 | 36.0° / 0.05 | 4 | balanced_pair=split_ls; unequal_pair=split_ls; opposed_phase_pair=abstain(ambiguous_projection_gap); coincident_cancel_control=abstain(ambiguous_projection_gap) | 0.001205, 0.001442 |
| `span30_gap000` | 3005 | 30.0° / 0.0 | 5 | balanced_pair=abstain(ambiguous_projection_gap); unequal_pair=abstain(ambiguous_projection_gap); opposed_phase_pair=abstain(ambiguous_narrow_peak_span); coincident_cancel_control=split_ls(test_amplitude_guard); symmetric_control=abstain(ambiguous_projection_gap) | — |
| `span30_gap002` | 3006 | 30.0° / 0.02 | 4 | balanced_pair=abstain(ambiguous_projection_gap); unequal_pair=abstain(ambiguous_projection_gap); opposed_phase_pair=abstain(ambiguous_narrow_peak_span); coincident_cancel_control=abstain(ambiguous_projection_gap) | — |
| `span30_gap008` | 3007 | 30.0° / 0.08 | 4 | balanced_pair=split_ls; unequal_pair=split_ls; opposed_phase_pair=abstain(ambiguous_narrow_peak_span); coincident_cancel_control=abstain(ambiguous_narrow_peak_span) | 0.010356, 0.008325 |
| `span30_gap012` | 3008 | 30.0° / 0.12 | 4 | balanced_pair=split_ls; unequal_pair=split_ls; opposed_phase_pair=abstain(ambiguous_narrow_peak_span); coincident_cancel_control=abstain(ambiguous_narrow_peak_span) | 0.011291, 0.009605 |

## Rejected rows and counterfactual diagnostics

| Cell | Semantic | Reason | Merge RMSE mm | Split-LS RMSE mm |
|---|---|---|---:|---:|
| `span24_gap005` | `balanced_pair` | `ambiguous_narrow_peak_span` | 0.010087 | 0.011807 |
| `span24_gap005` | `opposed_phase_pair` | `ambiguous_narrow_peak_span` | 0.002883 | 0.003621 |
| `span24_gap005` | `coincident_cancel_control` | `test_amplitude_guard` | guard reject | guard reject |
| `span28_gap005` | `opposed_phase_pair` | `ambiguous_narrow_peak_span` | 0.011906 | 0.010552 |
| `span28_gap005` | `coincident_cancel_control` | `ambiguous_projection_gap` | guard reject | guard reject |
| `span30_gap005` | `opposed_phase_pair` | `ambiguous_narrow_peak_span` | 0.007866 | 0.007080 |
| `span30_gap005` | `coincident_cancel_control` | `test_amplitude_guard` | guard reject | guard reject |
| `span32_gap005` | `opposed_phase_pair` | `ambiguous_narrow_peak_span` | 0.006150 | 0.009116 |
| `span32_gap005` | `coincident_cancel_control` | `test_amplitude_guard` | guard reject | guard reject |
| `span36_gap005` | `opposed_phase_pair` | `ambiguous_projection_gap` | 0.009276 | 0.001491 |
| `span36_gap005` | `coincident_cancel_control` | `ambiguous_projection_gap` | guard reject | guard reject |
| `span30_gap000` | `balanced_pair` | `ambiguous_projection_gap` | 0.005759 | 0.005909 |
| `span30_gap000` | `unequal_pair` | `ambiguous_projection_gap` | 0.004145 | 0.004886 |
| `span30_gap000` | `opposed_phase_pair` | `ambiguous_narrow_peak_span` | 0.008137 | 0.007768 |
| `span30_gap000` | `coincident_cancel_control` | `test_amplitude_guard` | guard reject | guard reject |
| `span30_gap000` | `symmetric_control` | `ambiguous_projection_gap` | 0.005759 | 0.005909 |
| `span30_gap002` | `balanced_pair` | `ambiguous_projection_gap` | 0.006144 | 0.007845 |
| `span30_gap002` | `unequal_pair` | `ambiguous_projection_gap` | 0.004972 | 0.006912 |
| `span30_gap002` | `opposed_phase_pair` | `ambiguous_narrow_peak_span` | 0.009063 | 0.008259 |
| `span30_gap002` | `coincident_cancel_control` | `ambiguous_projection_gap` | guard reject | guard reject |
| `span30_gap008` | `opposed_phase_pair` | `ambiguous_narrow_peak_span` | 0.009523 | 0.011866 |
| `span30_gap008` | `coincident_cancel_control` | `ambiguous_narrow_peak_span` | guard reject | guard reject |
| `span30_gap012` | `opposed_phase_pair` | `ambiguous_narrow_peak_span` | 0.010373 | 0.012394 |
| `span30_gap012` | `coincident_cancel_control` | `ambiguous_narrow_peak_span` | guard reject | guard reject |

## Boundary reading

Projection-gap sweep at requested span 30° was directionally monotonic for the balanced and unequal pair rows: gaps 0 and 0.02 abstained, while 0.08 and 0.12 selected split-LS. The zero-gap cell also abstained for the explicit symmetric-control row.

The span sweep at requested projection gap 0.05 was less stable. The opposed-phase rows abstained throughout, but the balanced row changed from abstain at 24° to split at 28° and above. The unequal 24° row selected split because the detected grid peaks were about 30.25° apart, then accepted RMSE `0.011405 mm`; this is a calibration quantization false acceptance. Several accepted rows near the boundary also exceeded 0.01 mm.

The selector therefore has a useful conservative direction near the two frozen thresholds, but the span feature is not monotonic in the requested physical geometry after peak quantization. The holdout supports keeping abstention and recording detected span/projection gap; it does not support a universal threshold or a completed first-innovation validation.

## Minimum next step

Freeze the detected-feature rule and add a small paired perturbation that records both requested and realized geometry. Include threshold-adjacent spans with repeated phase/amplitude semantics, and predeclare false-accept and false-abstain counts. A noise-only seed expansion is insufficient for this boundary.
