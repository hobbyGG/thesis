# Conservative selector smoke protocol

Run one new seed (`213`) over the six frozen v2 scenes. This supplements the
seed-212 selector smoke and leaves the v2 12-seed record unchanged.

The selector input is calibration IQ plus fixed constants only. The frozen
decision order is:

1. no peak: abstain;
2. one peak: choose merge;
3. two peaks: compute angular span and cosine-projection gap;
4. if span `<30°` or projection gap `<0.05`, abstain;
5. otherwise, if steering condition `≤20`, choose split-LS;
6. otherwise abstain;
7. any selected-route amplitude or finite-output failure: abstain without
   fallback.

Truth is opened only after selection and route estimation for post-run scoring.
Report selected coverage, abstention reasons, selected RMSE, and independent
merge/split RMSE on the identical 128-frame test window. Record high-error
acceptance (`RMSE > 0.01 mm`) as a diagnostic that never enters routing.

The rule is based on calibration feature separability in the existing v2
compact record. It is a conservative development guard, not a universal
threshold or a claim of coherent-source identifiability.

