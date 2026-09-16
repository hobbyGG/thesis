# AoA super-resolution validation

| scenario | method | AoA RMSE (deg) | AoA bias (deg) | RMSE/CRLB | beta rel err | disp RMSE (mm) | disp RMSE 0.1-10Hz (mm) | branch err rate | sel order | rejected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| same_range_far_angles | oracle | nan | nan | nan | nan | 0 | 0 | 0 |  |  |
| same_range_far_angles | fft | 6.392 | 4.97 | nan | 0.01473 | 0.03131 | 0.01606 | 0 |  |  |
| same_range_far_angles | local_music_ml | 2.696 | 1.187 | nan | 0.03482 | 0.04582 | 0.03667 | 0 |  |  |
| same_range_far_angles | fbss | 2.696 | 1.187 | nan | 0.03482 | 0.04582 | 0.03667 | 0 |  |  |
| same_range_far_angles | selfcal_crlb | 16.21 | 14.34 | 194.5 | 0.1105 | 0.02389 | 0.01219 | 0.085 | 3 3 3 | 0 0 0 |
| coherent_same_range | oracle | nan | nan | nan | 0 | 0 | 0 | 0 |  |  |
| coherent_same_range | fft | 11.81 | 2.379 | nan | 0.1315 | 0.02875 | 0.01647 | 0 |  |  |
| coherent_same_range | local_music_ml | 1.577 | 0.01516 | nan | 0.01376 | 0.01554 | 0.00588 | 0 |  |  |
| coherent_same_range | fbss | 1.577 | 0.01516 | nan | 0.01376 | 0.01554 | 0.00588 | 0 |  |  |
| coherent_same_range | selfcal_crlb | 0.1171 | -0.0043 | 107.7 | 0.001019 | 0.01444 | 0.005234 | 0 | 2 2 | 0 0 |
| array_mismatch | oracle | nan | nan | nan | nan | 0 | 0 | 0 |  |  |
| array_mismatch | fft | 2.611 | 0.05926 | nan | 0.01524 | 0.02581 | 0.009938 | 0 |  |  |
| array_mismatch | local_music_ml | 0.7239 | 0.3681 | nan | 0.0003598 | 0.0255 | 0.009437 | 0 |  |  |
| array_mismatch | fbss | 0.7073 | 0.3606 | nan | 0.0003598 | 0.0255 | 0.009437 | 0 |  |  |
| array_mismatch | selfcal_crlb | 0.02686 | 0.01946 | 2.082 | 9.328e-05 | 0.02566 | 0.009432 | 0 | 1 1 1 1 1 1 1 | 0 0 0 1 1 1 1 |
| target_snr_drop | oracle | nan | nan | nan | nan | 0 | 0 | 0 |  |  |
| target_snr_drop | fft | 2.37 | -0.5802 | nan | 0.01524 | 0.05911 | 0.02988 | 0.0005 |  |  |
| target_snr_drop | local_music_ml | 0.05734 | -0.0311 | nan | 0.0001369 | 0.0581 | 0.02917 | 0 |  |  |
| target_snr_drop | fbss | 0.05734 | -0.0311 | nan | 0.0001369 | 0.0581 | 0.02917 | 0 |  |  |
| target_snr_drop | selfcal_crlb | 0.01365 | 0.0001199 | 1.327 | 0.000137 | 0.05655 | 0.02809 | 0 | 1 1 1 1 1 1 1 | 0 0 0 1 1 1 1 |

## Beta relative error by theta band

| scenario | method | 0-30 | 30-55 | 55-90 |
| --- | --- | --- | --- | --- |
| same_range_far_angles | oracle | nan | nan | nan |
| same_range_far_angles | fft | 0.01244 | 0.01703 | nan |
| same_range_far_angles | local_music_ml | 0.0002321 | 0.06942 | nan |
| same_range_far_angles | fbss | 0.000232 | 0.06941 | nan |
| same_range_far_angles | selfcal_crlb | 0.07775 | 0.1432 | nan |
| coherent_same_range | oracle | 0 | 0 | nan |
| coherent_same_range | fft | 0.04334 | 0.2197 | nan |
| coherent_same_range | local_music_ml | 0.009459 | 0.01807 | nan |
| coherent_same_range | fbss | 0.009459 | 0.01807 | nan |
| coherent_same_range | selfcal_crlb | 0.0007184 | 0.001319 | nan |
| array_mismatch | oracle | nan | nan | nan |
| array_mismatch | fft | 0.005236 | 0.01524 | 0.1298 |
| array_mismatch | local_music_ml | 6.044e-05 | 0.0003598 | 0.04433 |
| array_mismatch | fbss | 6.044e-05 | 0.0003598 | 0.04327 |
| array_mismatch | selfcal_crlb | 6.239e-05 | 0.0003648 | 0.001282 |
| target_snr_drop | oracle | nan | nan | nan |
| target_snr_drop | fft | 0.005236 | 0.01524 | 0.1035 |
| target_snr_drop | local_music_ml | 1.3e-05 | 0.0001369 | 0.003401 |
| target_snr_drop | fbss | 1.3e-05 | 0.0001369 | 0.003401 |
| target_snr_drop | selfcal_crlb | 1.305e-05 | 0.000137 | 0.0006911 |
