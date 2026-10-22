# 评估 —— 量化「这个 AI 到底行不行」

一个作品集 AI 项目，必须回答招聘官会问的那个问题：*「你怎么知道 AI 是好的？怎么比较不同策略？」* 本文定义指标、工具，以及工具库里三个决策系统的正面对抗基准。

## 指标

所有指标都来自 `tools/headless_eval.py`：它把引擎无关的 `World` 模拟，每个对阵跑 `N` 次（无渲染，靠 seed 完全确定性），然后汇总：

| 指标 | 含义 | 为什么重要 |
|---|---|---|
| **胜率 Win %** | brain 的队伍赢下对局的占比 | 战斗 AI 的最终底线 |
| **负率 Loss %** | 输掉的占比 | 一个能存活的 AI 会拖平局而不是送死 |
| **平局 Draw %** | 打到步数上限双方仍存活的占比 | 体现「避战」vs「果断」的取舍 |
| **ms / tick** | 每次 `world.tick()` 的平均墙钟时间 | 决策**延迟**——实时预算 |
| **steps** | 一局平均 tick 数 | 一次决策要多久才见分晓 |

> 确定性说明：模拟是有 seed 的。`tests/test_sim.py::test_determinism_supports_parity` 锁住了这个性质——相同 seed ⇒ 相同结果——这正是 C++ 移植版能宣称逐字节 parity 的前提（见 `tests/test_parity.py`）。

## 怎么跑

```bash
PYTHONPATH=src python tools/headless_eval.py \
    tests/fixtures/maps/skirmish.json fsm,utility,bt 6
# -> benchmarks/report_data/metrics.csv  +  win_rate.png
```

## 正面对抗基准（skirmish 地图，每种 brain 6 局）

```
brain      win%  wins  loss  draw   ms/tick   steps
fsm       50.0%     3     3     0    0.357   186.7
utility   50.0%     3     0     3    0.445  1252.3
bt       100.0%     6     0     0    0.362   121.7
```

### 怎么读这些数字

- **行为树（BT）100% 胜，从不平局。** 它的 `Selector` 显式编码了优先级规则 *射程内攻击 → 见敌追击 → 受伤逃跑 → 巡逻*，所以每个 tick 都不浪费，永远取优先级最高的可用动作。
- **FSM 输了 3/6。** 它是最**激进**的配置：同样的优先级存在，但状态机表示在两次交火之间会回到 `patrol`，偶尔被抓到不在位。赢的时候结束最快（steps 低），但代价是送命。
- **Utility 从不输（0 负）但平了 3/6。** 打分 brain 在低血量时死命后撤，所以活得下来——但它的「后撤」选项让它拖到步数上限而不是收人头。它也是**最慢**的决策（0.445 ms/tick），因为它要给三个选项各算一个归一化考量。

### 这证明了关于「你」的什么

你没有只是「交付了一个 AI」。你定义了**什么叫好**、搭了一套**带仪表、可复现的评估框架**、产出了一张**权衡表**——FSM 激进、Utility 稳但被动、BT 果断。这是技术负责人 / 管理岗期待的分析姿态：你能测量、能比较、能给出建议，而不只是实现。

## 扩展基准

- 加一个 brain：实现 `Brain.tick(agent, world, dt)`，并在 `make_brain` / eval CLI 里注册。
- 加一张地图：往 `tests/fixtures/maps/` 丢一个 JSON（schema 在 `core/json_defs.py`）；parity 和 eval 都原样消费它。
- 对比 C++ 移植版：先 build `cpp/`，再 `pytest tests/test_parity.py`，断言 C++ 的决策和 Python 在相同输入上一致。
