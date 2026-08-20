# Acrobot Swing-up SAC training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `50_percent`
- Best final-stable rate: `0.0%`
- Best capture rate: `41.7%`
- Best goal-height dwell: `11.1%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.258 Nm |
| 25_percent | 150,000 | 1446.6s | 803.7 | 16.7% | 32.88s | 0.0% | 5.1% | 0.770 Nm |
| 50_percent | 300,000 | 2998.3s | 974.1 | 41.7% | 32.80s | 0.0% | 11.1% | 0.792 Nm |
| 75_percent | 450,000 | 4517.8s | 138.1 | 0.0% | - | 0.0% | 0.0% | 0.734 Nm |
| 100_percent | 600,000 | 6111.6s | 115.3 | 0.0% | - | 0.0% | 0.0% | 0.335 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
Best checkpoint is selected lexicographically by final stability, capture rate, goal-height dwell, then return.
