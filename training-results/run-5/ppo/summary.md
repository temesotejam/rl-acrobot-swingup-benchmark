# Acrobot Swing-up PPO training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `block_10_mixed_downward`
- Best final-stable rate: `0.0%`
- Best capture rate: `0.0%`
- Best goal-height dwell: `6.4%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.258 Nm |
| warmup | 100,000 | 31.5s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_01_mixed_upper | 150,000 | 47.1s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_02_mixed_upper | 200,000 | 62.8s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_03_mixed_upper | 250,000 | 78.3s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_04_mixed_mid | 300,000 | 93.9s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_05_mixed_mid | 350,000 | 109.4s | 382.4 | 0.0% | - | 0.0% | 3.2% | 0.989 Nm |
| block_06_mixed_mid | 400,000 | 124.8s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_07_mixed_full | 450,000 | 140.0s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_08_mixed_full | 500,000 | 155.4s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_09_mixed_full | 550,000 | 171.0s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_10_mixed_downward | 600,000 | 186.3s | 690.8 | 0.0% | - | 0.0% | 6.4% | 0.963 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
Best checkpoint is selected lexicographically by final stability, capture rate, goal-height dwell, then return.
