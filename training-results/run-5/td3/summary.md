# Acrobot Swing-up TD3 training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `block_04_mixed_mid`
- Best final-stable rate: `0.0%`
- Best capture rate: `25.0%`
- Best goal-height dwell: `8.6%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.258 Nm |
| warmup | 100,000 | 411.8s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_01_mixed_upper | 150,000 | 630.5s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_02_mixed_upper | 200,000 | 850.9s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_03_mixed_upper | 250,000 | 1086.0s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_04_mixed_mid | 300,000 | 1327.5s | 617.9 | 25.0% | 24.77s | 0.0% | 8.6% | 0.966 Nm |
| block_05_mixed_mid | 350,000 | 1568.0s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| block_06_mixed_upper | 400,000 | 1817.7s | 271.1 | 0.0% | - | 0.0% | 2.0% | 0.988 Nm |
| block_07_mixed_upper | 450,000 | 2069.7s | 271.1 | 0.0% | - | 0.0% | 2.0% | 0.988 Nm |
| block_08_mixed_upper | 500,000 | 2317.2s | 271.1 | 0.0% | - | 0.0% | 2.0% | 0.988 Nm |
| block_09_mixed_upper | 550,000 | 2564.5s | 271.1 | 0.0% | - | 0.0% | 2.0% | 0.988 Nm |
| block_10_mixed_upper | 600,000 | 2800.7s | 271.1 | 0.0% | - | 0.0% | 2.0% | 0.988 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
Best checkpoint is selected lexicographically by final stability, capture rate, goal-height dwell, then return.
