# Acrobot Swing-up TD3 training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `block_11_d0p300`
- Best difficulty: `0.300`
- Best final-stable rate: `0.0%`
- Best capture rate: `25.0%`
- Best stable dwell: `1.2%`
- Best goal-height dwell: `13.7%`
- Delivered final model capture rate: `25.0%`
- Delivered final model stable dwell: `0.7%`
- Delivered final model difficulty: `0.300`

## Downward-start evaluation

| Stage | Steps | Difficulty | Train time | Return | Capture | Capture time | Final stable | Stable dwell | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.000 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.258 Nm |
| warmup | 100,000 | 0.000 | 326.0s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_01_d0p000 | 125,000 | 0.000 | 411.1s | 115.0 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.945 Nm |
| block_02_d0p000 | 150,000 | 0.000 | 496.8s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_03_d0p000 | 175,000 | 0.000 | 583.1s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_04_d0p100 | 200,000 | 0.100 | 669.0s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_05_d0p100 | 225,000 | 0.100 | 754.3s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_06_d0p100 | 250,000 | 0.100 | 840.0s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_07_d0p200 | 275,000 | 0.200 | 925.2s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_08_d0p200 | 300,000 | 0.200 | 1010.5s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_09_d0p200 | 325,000 | 0.200 | 1096.8s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_10_d0p300 | 350,000 | 0.300 | 1183.3s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_11_d0p300 | 375,000 | 0.300 | 1269.2s | 1164.0 | 25.0% | 23.21s | 0.0% | 1.2% | 13.7% | 0.925 Nm |
| block_12_d0p300 | 400,000 | 0.300 | 1354.5s | 1041.2 | 16.7% | 33.17s | 0.0% | 1.1% | 9.7% | 0.921 Nm |
| block_13_d0p400 | 425,000 | 0.400 | 1439.6s | 1031.8 | 8.3% | 21.40s | 0.0% | 0.5% | 9.7% | 0.923 Nm |
| block_14_d0p300 | 450,000 | 0.300 | 1509.2s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_15_d0p300 | 475,000 | 0.300 | 1578.8s | 1008.0 | 8.3% | 30.44s | 0.0% | 0.5% | 10.3% | 0.922 Nm |
| block_16_d0p300 | 500,000 | 0.300 | 1648.5s | 1081.5 | 8.3% | 21.74s | 0.0% | 0.4% | 11.2% | 0.920 Nm |
| block_17_d0p300 | 525,000 | 0.300 | 1719.0s | 957.6 | 16.7% | 32.49s | 0.0% | 1.0% | 8.7% | 0.939 Nm |
| block_18_d0p300 | 550,000 | 0.300 | 1804.1s | 950.8 | 8.3% | 25.74s | 0.0% | 0.9% | 8.4% | 0.931 Nm |
| block_19_d0p300 | 575,000 | 0.300 | 1873.5s | 1026.5 | 8.3% | 23.08s | 0.0% | 0.4% | 10.2% | 0.931 Nm |
| block_20_d0p300 | 600,000 | 0.300 | 1943.5s | 1113.3 | 25.0% | 19.69s | 0.0% | 0.7% | 11.5% | 0.919 Nm |
| final_model | 600,000 | 0.300 | 1943.5s | 1113.3 | 25.0% | 19.69s | 0.0% | 0.7% | 11.5% | 0.919 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Stable dwell is the fraction of the full episode satisfying the same height/velocity condition.
Final stable requires that condition for at least 80% of the final 2 s.
The `final_model` row is a fresh evaluation of the model actually saved as `models/final.zip` after any rollback.
Best checkpoint is selected lexicographically by final stability, capture rate, stable dwell, goal-height dwell, then return.
