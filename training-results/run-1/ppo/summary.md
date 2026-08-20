# Acrobot Swing-up PPO training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `75_percent`
- Best final-stable rate: `0.0%`

## Downward-start evaluation

| Stage | Steps | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.0s | 53.4 | 0.0% | - | 0.0% | 0.0% | 0.259 Nm |
| 25_percent | 150,000 | 44.6s | 352.0 | 8.3% | 17.86s | 0.0% | 3.2% | 0.956 Nm |
| 50_percent | 300,000 | 88.7s | 310.3 | 0.0% | - | 0.0% | 2.1% | 0.930 Nm |
| 75_percent | 450,000 | 132.3s | 382.0 | 8.3% | 17.98s | 0.0% | 5.4% | 0.962 Nm |
| 100_percent | 600,000 | 175.7s | 355.1 | 0.0% | - | 0.0% | 2.8% | 0.965 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
