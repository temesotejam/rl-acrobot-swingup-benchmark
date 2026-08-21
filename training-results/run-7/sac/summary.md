# Acrobot Swing-up SAC training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `block_11_d0p000`
- Best difficulty: `0.000`
- Best final-stable rate: `8.3%`
- Best capture rate: `33.3%`
- Best stable dwell: `1.7%`
- Best goal-height dwell: `5.4%`
- Delivered final model capture rate: `50.0%`
- Delivered final model stable dwell: `2.8%`
- Delivered final model difficulty: `0.025`

## Downward-start evaluation

| Stage | Steps | Difficulty | Train time | Return | Capture | Capture time | Final stable | Stable dwell | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.000 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.258 Nm |
| warmup | 100,000 | 0.000 | 947.2s | 170.8 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.889 Nm |
| block_01_d0p000 | 125,000 | 0.000 | 1199.2s | 647.1 | 33.3% | 33.71s | 0.0% | 1.5% | 3.8% | 0.844 Nm |
| block_02_d0p000 | 150,000 | 0.000 | 1449.7s | 940.6 | 50.0% | 29.77s | 0.0% | 2.8% | 8.3% | 0.814 Nm |
| block_03_d0p100 | 175,000 | 0.100 | 1704.3s | 818.6 | 41.7% | 34.16s | 0.0% | 2.1% | 6.9% | 0.841 Nm |
| block_04_d0p100 | 200,000 | 0.100 | 1957.4s | 146.0 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.985 Nm |
| block_05_d0p000 | 225,000 | 0.000 | 2159.9s | 113.4 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.998 Nm |
| block_06_d0p000 | 250,000 | 0.000 | 2362.0s | 139.2 | 0.0% | - | 0.0% | 0.1% | 0.1% | 0.988 Nm |
| block_07_d0p000 | 275,000 | 0.000 | 2564.4s | 840.6 | 16.7% | 36.48s | 0.0% | 1.6% | 5.6% | 0.822 Nm |
| block_08_d0p000 | 300,000 | 0.000 | 2773.6s | 713.4 | 33.3% | 33.59s | 0.0% | 1.5% | 5.7% | 0.858 Nm |
| block_09_d0p000 | 325,000 | 0.000 | 3026.9s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_10_d0p000 | 350,000 | 0.000 | 3231.0s | 240.1 | 0.0% | - | 0.0% | 0.2% | 0.7% | 0.955 Nm |
| block_11_d0p000 | 375,000 | 0.000 | 3435.5s | 889.4 | 33.3% | 31.35s | 8.3% | 1.7% | 5.4% | 0.787 Nm |
| block_12_d0p000 | 400,000 | 0.000 | 3689.7s | 642.2 | 0.0% | - | 0.0% | 0.1% | 0.2% | 0.807 Nm |
| block_13_d0p000 | 425,000 | 0.000 | 3895.3s | 113.3 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.999 Nm |
| block_14_d0p000 | 450,000 | 0.000 | 4099.2s | 645.5 | 0.0% | - | 0.0% | 0.9% | 2.7% | 0.832 Nm |
| block_15_d0p000 | 475,000 | 0.000 | 4303.5s | 253.6 | 0.0% | - | 0.0% | 0.0% | 0.1% | 0.909 Nm |
| block_16_d0p000 | 500,000 | 0.000 | 4511.5s | 806.9 | 0.0% | - | 0.0% | 0.6% | 3.7% | 0.802 Nm |
| block_17_d0p000 | 525,000 | 0.000 | 4717.0s | 949.4 | 25.0% | 28.20s | 0.0% | 2.0% | 8.4% | 0.788 Nm |
| block_18_d0p000 | 550,000 | 0.000 | 4968.0s | 1060.4 | 33.3% | 32.66s | 0.0% | 2.5% | 10.8% | 0.810 Nm |
| block_19_d0p025 | 575,000 | 0.025 | 5220.9s | 1090.4 | 50.0% | 29.82s | 0.0% | 2.2% | 10.7% | 0.810 Nm |
| block_20_d0p025 | 600,000 | 0.025 | 5472.4s | 1024.0 | 50.0% | 33.59s | 0.0% | 2.8% | 9.8% | 0.809 Nm |
| final_model | 600,000 | 0.025 | 5472.4s | 1024.0 | 50.0% | 33.59s | 0.0% | 2.8% | 9.8% | 0.809 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Stable dwell is the fraction of the full episode satisfying the same height/velocity condition.
Final stable requires that condition for at least 80% of the final 2 s.
The `final_model` row is a fresh evaluation of the model actually saved as `models/final.zip` after any rollback.
Best checkpoint is selected lexicographically by final stability, capture rate, stable dwell, goal-height dwell, then return.
