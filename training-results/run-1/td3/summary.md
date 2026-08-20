# Acrobot Swing-up TD3 training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `50_percent`
- Best final-stable rate: `0.0%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 53.4 | 0.0% | - | 0.0% | 0.0% | 0.259 Nm |
| 25_percent | 150,000 | 720.2s | 325.9 | 0.0% | - | 0.0% | 3.4% | 0.953 Nm |
| 50_percent | 300,000 | 1492.0s | 362.7 | 25.0% | 18.81s | 0.0% | 4.0% | 0.953 Nm |
| 75_percent | 450,000 | 2269.3s | 57.2 | 0.0% | - | 0.0% | 0.0% | 0.998 Nm |
| 100_percent | 600,000 | 3049.3s | 53.2 | 0.0% | - | 0.0% | 0.0% | 0.971 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
