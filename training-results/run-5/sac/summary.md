# Acrobot Swing-up SAC training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `block_01_mixed_upper`
- Best final-stable rate: `0.0%`
- Best capture rate: `50.0%`
- Best goal-height dwell: `9.6%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.258 Nm |
| warmup | 100,000 | 938.7s | 123.3 | 0.0% | - | 0.0% | 0.0% | 0.408 Nm |
| block_01_mixed_upper | 150,000 | 1446.5s | 990.3 | 50.0% | 31.76s | 0.0% | 9.6% | 0.800 Nm |
| block_02_mixed_upper | 200,000 | 1955.1s | 572.9 | 25.0% | 34.87s | 0.0% | 4.9% | 0.895 Nm |
| block_03_mixed_mid | 250,000 | 2468.1s | 331.2 | 8.3% | 36.28s | 0.0% | 2.3% | 0.945 Nm |
| block_04_mixed_upper | 300,000 | 2975.6s | 1146.5 | 41.7% | 25.39s | 0.0% | 13.5% | 0.812 Nm |
| block_05_mixed_upper | 350,000 | 3481.0s | 113.8 | 0.0% | - | 0.0% | 0.0% | 0.997 Nm |
| block_06_mixed_upper | 400,000 | 3985.8s | 1146.5 | 41.7% | 25.39s | 0.0% | 13.5% | 0.812 Nm |
| block_07_mixed_upper | 450,000 | 4503.2s | 113.8 | 0.0% | - | 0.0% | 0.0% | 0.997 Nm |
| block_08_mixed_upper | 500,000 | 5020.3s | 1146.5 | 41.7% | 25.39s | 0.0% | 13.5% | 0.812 Nm |
| block_09_mixed_upper | 550,000 | 5530.3s | 113.8 | 0.0% | - | 0.0% | 0.0% | 0.997 Nm |
| block_10_mixed_upper | 600,000 | 6040.3s | 1146.5 | 41.7% | 25.39s | 0.0% | 13.5% | 0.812 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
Best checkpoint is selected lexicographically by final stability, capture rate, goal-height dwell, then return.
