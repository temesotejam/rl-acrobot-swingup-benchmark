# Acrobot Swing-up TD3 training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `50_percent`
- Best final-stable rate: `0.0%`
- Best capture rate: `0.0%`
- Best goal-height dwell: `0.0%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.258 Nm |
| 25_percent | 150,000 | 913.7s | 109.7 | 0.0% | - | 0.0% | 0.0% | 0.991 Nm |
| 50_percent | 300,000 | 1893.7s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| 75_percent | 450,000 | 2880.7s | 112.5 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| 100_percent | 600,000 | 3867.5s | 108.0 | 0.0% | - | 0.0% | 0.0% | 0.991 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
Best checkpoint is selected lexicographically by final stability, capture rate, goal-height dwell, then return.
