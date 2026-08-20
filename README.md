# rl-acrobot-swingup-benchmark

連続トルクAcrobotのSwing-upを **PPO / SAC / TD3** で同一条件比較するベンチマークです。

## 目的

Cart-Poleで個別に確立したPPO/SAC/TD3の学習・CI・評価・動画・Pagesの流れを、Acrobotから1リポジトリへ統合します。GitHub Actionsのmatrixで3方式を並列実行し、同じ評価seedで直接比較します。

## 環境

標準Acrobotと同じく2リンク直列系で、肩関節は非駆動、肘関節だけを駆動します。Gymnasium AcrobotのSutton/Barto book dynamicsを基礎にしています。

- link length: 1.0 m × 2
- link mass: 1.0 kg × 2
- COM: 0.5 m
- inertia: 1.0 kg m²
- gravity: 9.8 m/s²
- action: continuous `[-1, 1]` → ±1 N m
- control rate: 50 Hz (`dt=0.02 s`)
- motor first-order lag: 0.05 s
- joint viscous damping: 0.02 N m/(rad/s)
- episode: 20 s

角度定義はGymnasium Acrobotと同じで、`theta1=0`は第1リンクが真下、`theta2`は第1リンクに対する相対角です。真上直線姿勢はおおむね `theta1=pi, theta2=0` です。

## 観測

policyが見るのはノイズ付きの

`[cos(theta1), sin(theta1), cos(theta2), sin(theta2), theta1_dot, theta2_dot]`

のみです。真値は評価用`info`にだけ残します。各関節に角度white noise 0.25°、episode bias 1.0°、gyro white noise 0.10°/s、gyro bias 0.30°/sを入れます。

## Reward

途中終了で報酬を稼ぐ抜け道を避けるため、ゴール到達ではepisodeを終了しません。20秒間ずっと制御させます。

主な要素は、

- tip height
- link alignment
- goal height bonus
- high-and-slow bonus
- joint velocity penalty
- actuator torque penalty

です。

## Curriculum

1. `near_upright`
2. `upper`
3. `full`
4. `downward_mix`

評価はすべて`evaluation_downward`、つまりほぼ真下から開始します。

## 評価指標

- Capture rate
- Time to capture
- Final stable rate
- Goal-height dwell ratio
- High-position dwell ratio
- Maximum tip height
- RMS joint speed
- RMS actuator torque
- **Training wall time**

Captureはtip height >= 1.0 mかつ低角速度を0.5秒以上維持した場合です。Final stableは最終2秒の80%以上で同条件を満たした場合です。

## 学習量

| Preset | Steps / algorithm | Evaluation episodes |
|---|---:|---:|
| quick | 30,000 | 4 |
| normal | 600,000 | 12 |
| long | 1,200,000 | 20 |

## Algorithms

### PPO

- 4 parallel envs
- MLP [128, 128]
- gamma 0.995
- GAE 0.95
- SDE enabled

PPOのrollout粒度が各curriculum区間をちょうど割り切るように`n_steps`を選んでいます。

### SAC

- replay buffer 800k
- learning starts 5k
- batch 256
- gamma 0.99
- tau 0.005
- entropy coefficient auto

### TD3

- replay buffer 800k
- learning starts 5k
- batch 256
- gamma 0.99
- tau 0.005
- Gaussian action noise sigma 0.20
- policy delay 2
- target policy noise 0.20
- target noise clip 0.50

## GitHub Actions

PRではunit test後、PPO/SAC/TD3のquick学習を3 runnerで並列実行します。mainへのbenchmark trigger追加でnormal学習も3方式同時に走ります。

各runはモデル、5段階動画、plots、CSV、metadataをArtifactへ保存し、compact summaryを`training-results/run-N/{ppo,sac,td3}`へ残します。

## GitHub Pages

3方式の最終動画、Capture、安定化率、RMS torque、学習時間を同じページで比較します。

## References

- Gymnasium Acrobot documentation: https://gymnasium.farama.org/environments/classic_control/acrobot/
- Gymnasium Acrobot source: https://github.com/Farama-Foundation/Gymnasium/blob/main/gymnasium/envs/classic_control/acrobot.py
- Stable-Baselines3: https://stable-baselines3.readthedocs.io/

## License

MIT
