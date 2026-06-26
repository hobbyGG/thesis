from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="aoa_error_bootstrap",
        aoa_error_deg=10.0,
        kappa_update_start_s=0.3,
        kappa_window_samples=80,
        kappa_bootstrap_prior_weight=0.0,
    )
