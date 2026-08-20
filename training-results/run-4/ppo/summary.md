# Acrobot Swing-up PPO training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `block_09_mixed_downward`
- Best final-stable rate: `0.0%`
- Best capture rate: `16.7%`
- Best goal-height dwell: `10.2%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.258 Nm |
| warmup | 100,000 | 31.2s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_01_mixed_upper | 150,000 | 47.2s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_02_mixed_upper | 200,000 | 62.7s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_03_mixed_upper | 250,000 | 78.1s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_04_mixed_full | 300,000 | 93.4s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_05_mixed_full | 350,000 | 108.8s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_06_mixed_full | 400,000 | 124.3s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_07_mixed_downward | 450,000 | 139.8s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_08_mixed_downward | 500,000 | 155.1s | 900.8 | 0.0% | - | 0.0% | 8.8% | 0.933 Nm |
| block_09_mixed_downward | 550,000 | 170.4s | 975.0 | 16.7% | 27.09s | 0.0% | 10.2% | 0.940 Nm |
| block_10_mixed_downward | 600,000 | 185.7s | 1045.3 | 16.7% | 19.10s | 0.0% | 9.8% | 0.967 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
Best checkpoint is selected lexicographically by final stability, capture rate, goal-height dwell, then return.
