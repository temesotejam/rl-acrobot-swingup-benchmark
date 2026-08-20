# Acrobot Swing-up TD3 training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `warmup`
- Best final-stable rate: `0.0%`
- Best capture rate: `0.0%`
- Best goal-height dwell: `0.0%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.258 Nm |
| warmup | 100,000 | 599.8s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_01_mixed_upper | 150,000 | 927.1s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_02_mixed_upper | 200,000 | 1259.8s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_03_mixed_upper | 250,000 | 1594.9s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_04_mixed_full | 300,000 | 1928.0s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_05_mixed_full | 350,000 | 2261.9s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_06_mixed_full | 400,000 | 2598.3s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_07_mixed_downward | 450,000 | 2933.0s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_08_mixed_downward | 500,000 | 3270.5s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_09_mixed_downward | 550,000 | 3615.6s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_10_mixed_downward | 600,000 | 3959.3s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
Best checkpoint is selected lexicographically by final stability, capture rate, goal-height dwell, then return.
