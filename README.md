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
- episode: **40 s**

角度定義はGymnasium Acrobotと同じで、`theta1=0`は第1リンクが真下、`theta2`は第1リンクに対する相対角です。真上直線姿勢はおおむね `theta1=pi, theta2=0` です。

## 観測

policyが見るのはノイズ付きの

`[cos(theta1), sin(theta1), cos(theta2), sin(theta2), theta1_dot, theta2_dot]`

のみです。真値は評価用`info`にだけ残します。各関節に角度white noise 0.25°、episode bias 1.0°、gyro white noise 0.10°/s、gyro bias 0.30°/sを入れます。

## Reward v6: swing-up + stability shaping

途中終了で報酬を稼ぐ抜け道を避けるため、ゴール到達ではepisodeを終了しません。40秒間ずっと制御させます。

従来のtip height / link alignment / goal bonus / torque・速度penaltyに加えて、v6では**高い位置ほど、かつ角速度が小さいほど連続的に増えるstability reward**を追加します。

```text
stability_height = clip((height - 0.75) / (2.0 - 0.75), 0, 1)
stability_speed  = exp(-0.5*(theta1_dot/1.0)^2 - 0.5*(theta2_dot/1.5)^2)
stability_bonus  = 0.65 * stability_height * stability_speed
```

狙いは「一瞬1.0 mを越える」だけでなく、振り上げた後にエネルギーを抜き、上側で低速状態を長く維持することです。既存の`height >= 1.4 m`かつ低角速度のbonusも残しています。

## Continuous adaptive curriculum

離散的なreset stageの切替は使わず、**difficulty = 0.000〜1.000**の連続値でreset分布を補間します。

| Difficulty | near-upright | upper | full | downward |
|---:|---:|---:|---:|---:|
| 0.00 | 30% | 70% | 0% | 0% |
| 0.35 | 20% | 50% | 30% | 0% |
| 0.70 | 15% | 35% | 50% | 0% |
| 1.00 | 10% | 20% | 30% | 40% |

アンカー間は線形補間されます。評価は常に`evaluation_downward`、つまりほぼ真下から開始します。

- 初期difficulty stepは`0.10`。
- 昇格には**実際のCapture成功**が必要です。Goal-height滞在だけではdifficultyを上げません。
- Captureに加えてGoal-height dwellまたはStable dwellが基準を満たす状態を**2 block連続**で確認するとdifficultyを上げます。
- 同じdifficultyで最大3 block停滞した場合は、小さなprobeとしてstep分だけ難しくします。
- 大きな性能退行を検出すると`models/best.zip`へrollbackします。
- rollback時にはdifficultyをbest checkpointへ戻し、difficulty stepを半分へ縮めます。最小stepは`0.025`です。

## v6 off-policy recovery

run #6ではTD3が325kでCapture 50%を獲得した後、同じbest modelと同じbest replay bufferへ戻るたびにほぼ同じ更新軌道を再演し、25k後にCapture 0%へ崩れ続けました。

v6ではSAC/TD3のrollbackを次のように変更します。

1. **policy / criticのbest重みは復元**する。
2. **古いbest replay bufferは復元しない**。fresh bufferから再開する。
3. 次blockの最初の`5,000 step`は勾配更新を止め、現在のpolicyで新しい遷移だけを収集する。
4. rollbackごとにlearning rateを下げる。
   - SAC: `×0.70`、下限`1e-4`
   - TD3: `×0.50`、下限`5e-5`
5. rollbackごとにrecovery seedを変え、同じ探索系列の単純再演も避ける。

`best-replay.pkl`自体は診断・比較用artifactとして保存しますが、v6のSAC/TD3 rollbackでは復元しません。

## 評価指標

- Capture rate
- Time to capture
- Final stable rate
- **Stable dwell ratio**
- Goal-height dwell ratio
- High-position dwell ratio
- Maximum tip height
- RMS joint speed
- RMS actuator torque
- Curriculum difficulty
- Training wall time

Captureはtip height >= 1.0 mかつ`|theta1_dot| <= 1.0 rad/s`、`|theta2_dot| <= 1.5 rad/s`を0.5秒以上維持した場合です。**Stable dwell**はepisode全体で同条件を満たしていた時間割合、Final stableは最終2秒の80%以上で同条件を満たした場合です。

best checkpointの優先順位は、

`Final stable → Capture → Stable dwell → Goal-height dwell → Return`

です。

## 学習量

| Preset | Steps / algorithm | Evaluation episodes |
|---|---:|---:|
| quick | 30,000 | 4 |
| normal | 600,000 | 12 |
| long | 1,200,000 | 20 |

normalでは100k warmup後、**25k stepごと**にdownward評価とdifficulty更新を実行します。

## Algorithms

### PPO

- learning rate `3e-4`
- 4 parallel envs
- MLP [128, 128]
- gamma 0.995
- GAE 0.95
- SDE enabled
- normal `n_steps=625`（4 envで2,500 step/rollout、25k blockをちょうど分割）

### SAC

- initial learning rate `3e-4`
- replay buffer 800k
- learning starts 5k
- batch 256
- gamma 0.99
- tau 0.005
- train frequency 1 step
- entropy coefficient auto
- rollback時はfresh replay + 5k refill + LR decay

### TD3

v6ではpost-best collapseを抑えるため、v5より更新を保守的にしています。

- initial learning rate **`3e-4`**（v5: `1e-3`）
- replay buffer 800k
- learning starts 5k
- batch 256
- gamma 0.99
- tau 0.005
- train frequency **2 stepsに1回**（v5: 毎step）
- Gaussian action noise sigma **0.15**
- policy delay 2
- target policy noise **0.10**
- target noise clip **0.25**
- rollback時はfresh replay + 5k refill + LR decay

## GitHub Actions

PRではunit test後、PPO/SAC/TD3のquick学習を3 runnerで並列実行します。mainへのbenchmark trigger追加でnormal学習も3方式同時に走ります。

各runは`best.zip` / `final.zip`、`best.mp4` / `final.mp4`、plots、CSV、metadataをArtifactへ保存し、compact summaryと`best-checkpoint.json`を`training-results/run-N/{ppo,sac,td3}`へ残します。

metadataにはreward version、rollback回数、final learning rate、recovery判断も保存します。

## Delivered final model

rollbackが最後のblockで起きても表示が食い違わないよう、学習終了後に**実際に`models/final.zip`へ保存するモデルを評価seed一式で再評価**します。`metrics.csv`の`final_model`行と`metadata.json`の`final_checkpoint`が、その実モデルの数値です。

## GitHub Pages

3方式について **best checkpoint** と **実際に保存されたfinal model** を別々に表示し、Capture、Final stable、Stable dwell、difficulty、RMS torque、学習時間、rollback回数、final learning rate、動画を同じページで比較します。

## References

- Gymnasium Acrobot documentation: https://gymnasium.farama.org/environments/classic_control/acrobot/
- Gymnasium Acrobot source: https://github.com/Farama-Foundation/Gymnasium/blob/main/gymnasium/envs/classic_control/acrobot.py
- Stable-Baselines3: https://stable-baselines3.readthedocs.io/

## License

MIT
