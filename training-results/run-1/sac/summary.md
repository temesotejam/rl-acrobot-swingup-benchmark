# Acrobot Swing-up SAC training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `50_percent`
- Best final-stable rate: `0.0%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 53.4 | 0.0% | - | 0.0% | 0.0% | 0.259 Nm |
| 25_percent | 150,000 | 1146.2s | 58.0 | 0.0% | - | 0.0% | 0.0% | 0.987 Nm |
| 50_percent | 300,000 | 2367.3s | 289.6 | 0.0% | - | 0.0% | 0.6% | 0.863 Nm |
| 75_percent | 450,000 | 3593.6s | 55.8 | 0.0% | - | 0.0% | 0.0% | 0.971 Nm |
| 100_percent | 600,000 | 4799.4s | 52.4 | 0.0% | - | 0.0% | 0.0% | 0.846 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
