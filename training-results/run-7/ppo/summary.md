# Acrobot Swing-up PPO training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `warmup`
- Best difficulty: `0.000`
- Best final-stable rate: `0.0%`
- Best capture rate: `0.0%`
- Best stable dwell: `0.3%`
- Best goal-height dwell: `7.5%`
- Delivered final model capture rate: `0.0%`
- Delivered final model stable dwell: `0.3%`
- Delivered final model difficulty: `0.000`

## Downward-start evaluation

| Stage | Steps | Difficulty | Train time | Return | Capture | Capture time | Final stable | Stable dwell | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.000 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.258 Nm |
| warmup | 100,000 | 0.000 | 29.8s | 863.5 | 0.0% | - | 0.0% | 0.3% | 7.5% | 0.833 Nm |
| block_01_d0p000 | 125,000 | 0.000 | 37.1s | 101.8 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.511 Nm |
| block_02_d0p000 | 150,000 | 0.000 | 44.5s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_03_d0p000 | 175,000 | 0.000 | 51.8s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_04_d0p000 | 200,000 | 0.000 | 59.1s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_05_d0p000 | 225,000 | 0.000 | 66.5s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_06_d0p000 | 250,000 | 0.000 | 73.8s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_07_d0p000 | 275,000 | 0.000 | 81.2s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_08_d0p000 | 300,000 | 0.000 | 88.5s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_09_d0p000 | 325,000 | 0.000 | 95.7s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_10_d0p000 | 350,000 | 0.000 | 103.0s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_11_d0p000 | 375,000 | 0.000 | 110.3s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_12_d0p000 | 400,000 | 0.000 | 117.5s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_13_d0p000 | 425,000 | 0.000 | 124.8s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_14_d0p000 | 450,000 | 0.000 | 132.0s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_15_d0p000 | 475,000 | 0.000 | 139.3s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_16_d0p000 | 500,000 | 0.000 | 146.6s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_17_d0p000 | 525,000 | 0.000 | 153.9s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_18_d0p000 | 550,000 | 0.000 | 161.2s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_19_d0p000 | 575,000 | 0.000 | 168.5s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| block_20_d0p000 | 600,000 | 0.000 | 175.8s | 100.5 | 0.0% | - | 0.0% | 0.0% | 0.0% | 0.036 Nm |
| final_model | 600,000 | 0.000 | 175.8s | 863.5 | 0.0% | - | 0.0% | 0.3% | 7.5% | 0.833 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Stable dwell is the fraction of the full episode satisfying the same height/velocity condition.
Final stable requires that condition for at least 80% of the final 2 s.
The `final_model` row is a fresh evaluation of the model actually saved as `models/final.zip` after any rollback.
Best checkpoint is selected lexicographically by final stability, capture rate, stable dwell, goal-height dwell, then return.
