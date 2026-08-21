# Acrobot Swing-up SAC training result

- Preset: `normal`
- Seed: `42`
- Best checkpoint: `block_12_d0p100`
- Best difficulty: `0.100`
- Best final-stable rate: `0.0%`
- Best capture rate: `75.0%`
- Best goal-height dwell: `15.5%`
- Delivered final model capture rate: `75.0%`
- Delivered final model difficulty: `0.100`

## Downward-start evaluation

| Stage | Steps | Difficulty | Train time | Return | Capture | Capture time | Final stable | Goal height | RMS torque |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 0 | 0.000 | 0.0s | 107.5 | 0.0% | - | 0.0% | 0.0% | 0.258 Nm |
| warmup | 100,000 | 0.000 | 945.8s | 123.3 | 0.0% | - | 0.0% | 0.0% | 0.408 Nm |
| block_01_d0p000 | 125,000 | 0.000 | 1201.7s | 919.6 | 33.3% | 28.91s | 0.0% | 7.4% | 0.791 Nm |
| block_02_d0p000 | 150,000 | 0.000 | 1454.6s | 1054.8 | 58.3% | 30.77s | 0.0% | 11.9% | 0.796 Nm |
| block_03_d0p100 | 175,000 | 0.100 | 1706.0s | 911.1 | 41.7% | 32.08s | 0.0% | 6.9% | 0.798 Nm |
| block_04_d0p100 | 200,000 | 0.100 | 1955.3s | 937.4 | 41.7% | 31.82s | 0.0% | 8.2% | 0.785 Nm |
| block_05_d0p200 | 225,000 | 0.200 | 2204.9s | 1114.2 | 50.0% | 26.65s | 0.0% | 13.7% | 0.797 Nm |
| block_06_d0p200 | 250,000 | 0.200 | 2455.5s | 1101.5 | 25.0% | 30.51s | 0.0% | 14.0% | 0.816 Nm |
| block_07_d0p000 | 275,000 | 0.000 | 2704.9s | 1015.6 | 58.3% | 29.93s | 0.0% | 8.9% | 0.807 Nm |
| block_08_d0p000 | 300,000 | 0.000 | 2957.2s | 1133.6 | 66.7% | 29.31s | 0.0% | 13.9% | 0.815 Nm |
| block_09_d0p050 | 325,000 | 0.050 | 3207.3s | 1099.6 | 66.7% | 30.56s | 0.0% | 13.3% | 0.822 Nm |
| block_10_d0p050 | 350,000 | 0.050 | 3458.6s | 1164.0 | 58.3% | 29.15s | 0.0% | 14.5% | 0.806 Nm |
| block_11_d0p100 | 375,000 | 0.100 | 3712.8s | 1216.5 | 50.0% | 23.43s | 0.0% | 16.9% | 0.813 Nm |
| block_12_d0p100 | 400,000 | 0.100 | 3969.5s | 1181.8 | 75.0% | 29.61s | 0.0% | 15.5% | 0.809 Nm |
| block_13_d0p150 | 425,000 | 0.150 | 4231.0s | 1161.6 | 50.0% | 28.51s | 0.0% | 14.0% | 0.813 Nm |
| block_14_d0p150 | 450,000 | 0.150 | 4490.3s | 1198.5 | 66.7% | 27.40s | 0.0% | 16.5% | 0.833 Nm |
| block_15_d0p200 | 475,000 | 0.200 | 4746.2s | 1213.1 | 50.0% | 23.84s | 0.0% | 15.8% | 0.817 Nm |
| block_16_d0p200 | 500,000 | 0.200 | 4997.7s | 1232.6 | 50.0% | 23.84s | 0.0% | 16.3% | 0.821 Nm |
| block_17_d0p250 | 525,000 | 0.250 | 5254.7s | 1213.9 | 50.0% | 27.85s | 0.0% | 17.0% | 0.826 Nm |
| block_18_d0p250 | 550,000 | 0.250 | 5511.7s | 1259.6 | 50.0% | 25.56s | 0.0% | 18.2% | 0.812 Nm |
| block_19_d0p300 | 575,000 | 0.300 | 5767.3s | 1188.1 | 50.0% | 28.02s | 0.0% | 15.1% | 0.809 Nm |
| block_20_d0p300 | 600,000 | 0.300 | 6025.3s | 1227.9 | 33.3% | 24.36s | 0.0% | 18.2% | 0.806 Nm |
| final_model | 600,000 | 0.100 | 6025.3s | 1181.8 | 75.0% | 29.61s | 0.0% | 15.5% | 0.809 Nm |

Capture requires tip height >= 1.0 m with low joint velocity for at least 0.5 s.
Final stable requires that condition for at least 80% of the final 2 s.
The `final_model` row is a fresh evaluation of the model actually saved as `models/final.zip` after any rollback.
Best checkpoint is selected lexicographically by final stability, capture rate, goal-height dwell, then return.
