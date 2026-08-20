# Acrobot Swing-up SAC training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `block_01_mixed_upper`
- Best final-stable rate: `0.0%`
- Best capture rate: `58.3%`
- Best goal-height dwell: `12.5%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.258 Nm |
| warmup | 100,000 | 887.8s | 844.3 | 8.3% | 33.58s | 0.0% | 6.2% | 0.770 Nm |
| block_01_mixed_upper | 150,000 | 1379.0s | 1076.1 | 58.3% | 30.75s | 0.0% | 12.5% | 0.812 Nm |
| block_02_mixed_full | 200,000 | 1865.7s | 138.6 | 0.0% | - | 0.0% | 0.0% | 0.971 Nm |
| block_03_mixed_upper | 250,000 | 2357.0s | 1060.5 | 50.0% | 32.21s | 0.0% | 12.3% | 0.820 Nm |
| block_04_mixed_full | 300,000 | 2842.1s | 244.5 | 8.3% | 33.12s | 0.0% | 1.3% | 0.939 Nm |
| block_05_mixed_upper | 350,000 | 3325.5s | 1060.5 | 50.0% | 32.21s | 0.0% | 12.3% | 0.820 Nm |
| block_06_mixed_full | 400,000 | 3797.9s | 244.5 | 8.3% | 33.12s | 0.0% | 1.3% | 0.939 Nm |
| block_07_mixed_upper | 450,000 | 4285.7s | 1060.5 | 50.0% | 32.21s | 0.0% | 12.3% | 0.820 Nm |
| block_08_mixed_full | 500,000 | 4772.9s | 244.5 | 8.3% | 33.12s | 0.0% | 1.3% | 0.939 Nm |
| block_09_mixed_upper | 550,000 | 5259.8s | 1060.5 | 50.0% | 32.21s | 0.0% | 12.3% | 0.820 Nm |
| block_10_mixed_full | 600,000 | 5747.3s | 244.5 | 8.3% | 33.12s | 0.0% | 1.3% | 0.939 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
Best checkpoint is selected lexicographically by final stability, capture rate, goal-height dwell, then return.
