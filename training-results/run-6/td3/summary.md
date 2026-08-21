# Acrobot Swing-up TD3 training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `block_09_d0p200`
- Best difficulty: `0.200`
- Best final-stable rate: `0.0%`
- Best capture rate: `50.0%`
- Best goal-height dwell: `15.7%`
- Delivered final model capture rate: `50.0%`
- Delivered final model difficulty: `0.200`

## Downward-start evaluation

| Stage | Steps | Difficulty | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.000 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.258 Nm |
| warmup | 100,000 | 0.000 | 589.9s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_01_d0p000 | 125,000 | 0.000 | 750.6s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_02_d0p000 | 150,000 | 0.000 | 913.0s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_03_d0p000 | 175,000 | 0.000 | 1076.4s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_04_d0p100 | 200,000 | 0.100 | 1239.6s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_05_d0p100 | 225,000 | 0.100 | 1402.8s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_06_d0p100 | 250,000 | 0.100 | 1566.1s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_07_d0p200 | 275,000 | 0.200 | 1730.2s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_08_d0p200 | 300,000 | 0.200 | 1894.0s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_09_d0p200 | 325,000 | 0.200 | 2057.7s | 1039.5 | 50.0% | 27.42s | 0.0% | 15.7% | 0.935 Nm |
| block_10_d0p200 | 350,000 | 0.200 | 2220.6s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_11_d0p200 | 375,000 | 0.200 | 2384.4s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_12_d0p200 | 400,000 | 0.200 | 2547.6s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_13_d0p200 | 425,000 | 0.200 | 2713.4s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_14_d0p200 | 450,000 | 0.200 | 2878.1s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_15_d0p200 | 475,000 | 0.200 | 3043.1s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_16_d0p200 | 500,000 | 0.200 | 3207.8s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_17_d0p200 | 525,000 | 0.200 | 3372.4s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_18_d0p200 | 550,000 | 0.200 | 3535.8s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_19_d0p200 | 575,000 | 0.200 | 3699.1s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_20_d0p200 | 600,000 | 0.200 | 3864.0s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| final_model | 600,000 | 0.200 | 3864.0s | 1039.5 | 50.0% | 27.42s | 0.0% | 15.7% | 0.935 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
The `final_model` row is a fresh evaluation of the model actually saved as `models/final.zip` after any rollback.
Best checkpoint is selected lexicographically by final stability, capture rate, goal-height dwell, then return.
