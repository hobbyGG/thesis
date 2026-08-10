from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="aoa_error_bootstrap",
        aoa_error_deg=0.0,
        target_snr_db=(22.0, 18.0, 15.0, 12.0, 9.0),
        target_amplitudes=(1.0, 1.0, 1.0, 1.0, 1.0),
        beta_update_start_s=0.3,
        beta_window_samples=80,
        beta_bootstrap_prior_weight=20.0,
        beta_update_reference_mode="loo_update_direct_ls",
    )
