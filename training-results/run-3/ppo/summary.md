# Acrobot Swing-up PPO training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `75_percent`
- Best final-stable rate: `0.0%`
- Best capture rate: `16.7%`
- Best goal-height dwell: `9.1%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.258 Nm |
| 25_percent | 150,000 | 40.7s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| 50_percent | 300,000 | 81.3s | 113.1 | 0.0% | - | 0.0% | 0.0% | 0.999 Nm |
| 75_percent | 450,000 | 122.2s | 891.7 | 16.7% | 20.87s | 0.0% | 9.1% | 0.980 Nm |
| 100_percent | 600,000 | 162.2s | 991.8 | 0.0% | - | 0.0% | 8.1% | 0.973 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
Best checkpoint is selected lexicographically by final stability, capture rate, goal-height dwell, then return.
