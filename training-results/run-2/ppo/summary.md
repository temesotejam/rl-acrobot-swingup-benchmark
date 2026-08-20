# Acrobot Swing-up PPO training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `75_percent`
- Best final-stable rate: `0.0%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 53.4 | 0.0% | - | 0.0% | 0.0% | 0.259 Nm |
| 25_percent | 150,000 | 46.0s | 52.6 | 0.0% | - | 0.0% | 0.0% | 0.104 Nm |
| 50_percent | 300,000 | 91.8s | 365.8 | 8.3% | 19.98s | 0.0% | 4.7% | 0.956 Nm |
| 75_percent | 450,000 | 137.5s | 389.7 | 8.3% | 17.94s | 0.0% | 5.9% | 0.965 Nm |
| 100_percent | 600,000 | 183.0s | 368.4 | 8.3% | 18.48s | 0.0% | 4.1% | 0.966 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
