# Acrobot Swing-up PPO training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `block_01_d0p000`
- Best difficulty: `0.000`
- Best final-stable rate: `0.0%`
- Best capture rate: `16.7%`
- Best goal-height dwell: `2.5%`
- Delivered final model capture rate: `8.3%`
- Delivered final model difficulty: `0.000`

## Downward-start evaluation

| Stage | Steps | Difficulty | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.000 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.258 Nm |
| warmup | 100,000 | 0.000 | 22.1s | 116.1 | 0.0% | - | 0.0% | 0.0% | 0.976 Nm |
| block_01_d0p000 | 125,000 | 0.000 | 27.6s | 591.9 | 16.7% | 33.34s | 0.0% | 2.5% | 0.765 Nm |
| block_02_d0p000 | 150,000 | 0.000 | 33.1s | 920.9 | 0.0% | - | 0.0% | 7.1% | 0.832 Nm |
| block_03_d0p000 | 175,000 | 0.000 | 38.6s | 895.3 | 8.3% | 29.64s | 0.0% | 7.6% | 0.861 Nm |
| block_04_d0p000 | 200,000 | 0.000 | 44.2s | 933.5 | 8.3% | 23.38s | 0.0% | 7.3% | 0.941 Nm |
| block_05_d0p050 | 225,000 | 0.050 | 49.7s | 306.6 | 8.3% | 25.56s | 0.0% | 2.6% | 0.981 Nm |
| block_06_d0p050 | 250,000 | 0.050 | 55.2s | 714.1 | 8.3% | 24.02s | 0.0% | 5.2% | 0.967 Nm |
| block_07_d0p050 | 275,000 | 0.050 | 60.7s | 968.5 | 8.3% | 19.38s | 0.0% | 8.5% | 0.952 Nm |
| block_08_d0p050 | 300,000 | 0.050 | 66.3s | 900.1 | 8.3% | 22.18s | 0.0% | 8.7% | 0.943 Nm |
| block_09_d0p100 | 325,000 | 0.100 | 71.8s | 1017.1 | 8.3% | 19.30s | 0.0% | 10.5% | 0.954 Nm |
| block_10_d0p100 | 350,000 | 0.100 | 77.3s | 1018.9 | 0.0% | - | 0.0% | 11.1% | 0.965 Nm |
| block_11_d0p000 | 375,000 | 0.000 | 82.8s | 895.3 | 8.3% | 29.64s | 0.0% | 7.6% | 0.861 Nm |
| block_12_d0p000 | 400,000 | 0.000 | 88.3s | 933.5 | 8.3% | 23.38s | 0.0% | 7.3% | 0.941 Nm |
| block_13_d0p025 | 425,000 | 0.025 | 93.8s | 306.6 | 8.3% | 25.56s | 0.0% | 2.6% | 0.981 Nm |
| block_14_d0p025 | 450,000 | 0.025 | 99.3s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_15_d0p000 | 475,000 | 0.000 | 104.8s | 895.3 | 8.3% | 29.64s | 0.0% | 7.6% | 0.861 Nm |
| block_16_d0p000 | 500,000 | 0.000 | 110.3s | 933.5 | 8.3% | 23.38s | 0.0% | 7.3% | 0.941 Nm |
| block_17_d0p025 | 525,000 | 0.025 | 115.8s | 306.6 | 8.3% | 25.56s | 0.0% | 2.6% | 0.981 Nm |
| block_18_d0p025 | 550,000 | 0.025 | 121.3s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_19_d0p000 | 575,000 | 0.000 | 126.8s | 895.3 | 8.3% | 29.64s | 0.0% | 7.6% | 0.861 Nm |
| block_20_d0p000 | 600,000 | 0.000 | 132.3s | 933.5 | 8.3% | 23.38s | 0.0% | 7.3% | 0.941 Nm |
| final_model | 600,000 | 0.000 | 132.3s | 933.5 | 8.3% | 23.38s | 0.0% | 7.3% | 0.941 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
The `final_model` row is a fresh evaluation of the model actually saved as `models/final.zip` after any rollback.
Best checkpoint is selected lexicographically by final stability, capture rate, goal-height dwell, then return.
