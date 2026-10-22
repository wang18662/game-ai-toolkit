# 用到的设计模式 & 为什么

本文把工具库里用到的每一个 GoF 设计模式，映射到实现它的具体代码。它同时是 *Software Design* 课程（CUH404CMD）的作业素材：每条都写清「问题、选的模式、被否决的替代方案」。

> 约定：`core/` 是**引擎无关**的——它只依赖 `abc.py` 抽象，从不依赖 `pygame`。任何碰到渲染的模式都在 `demo/` 里，那里才允许依赖引擎。

## 模式映射表

| 模式 | 位置（Python） | 位置（C++ 移植） | 它解决的问题 |
|---|---|---|---|
| **Strategy** | `core/astar.py`（`Heuristic`, `Cost`） | `cpp/.../astar.hpp`（`Heuristic`, `Cost`） | 不碰 `find_path` 就能换寻路启发式 / 步进代价。 |
| **Strategy** | `core/utility.py`（`CurveType` + `response_curve`） | `cpp/.../utility.hpp`（`CurveType`） | 每个考量（consideration）可换响应曲线（线性/平方/sigmoid）。 |
| **State** | `core/fsm.py`（`State`, `FSM`）+ `sim/behaviors.py`（`PatrolState`…） | `cpp/.../fsm.hpp`（`State`, `FSM`） | 把 agent 行为建模成显式的、可替换的状态。 |
| **Composite** | `core/behavior_tree.py`（`Node`, `Sequence`, `Selector`, `Inverter`） | `cpp/.../behavior_tree.hpp` | 单个动作和整棵子树通过同一个 `tick()` 统一处理。 |
| **Observer** | `core/eventbus.py`（`EventBus`） | —（仅 Python） | 解耦「发生了某事」和「谁在响应」。 |
| **Factory** | `sim/behaviors.py`（`make_brain`） | — | 把三个 brain 的构造函数藏到一个入口后面。 |
| **Dependency Inversion** | `core/abc.py`（`IAgent`, `IWorld`, `IBlackboard`, `IEventSink`） | 同理（parity_runner 用 `AgentView`/`WorldView`） | core 从不 import 引擎；引擎来实现我们的接口。 |
| **Interface Segregation** | `core/abc.py`（拆成独立小接口） | — | agent 只依赖它需要的那一小片 world。 |
| **Adapter** | `demo/pygame_adapter.py` | — | 把引擎无关的 `World` 适配到 pygame 绘制调用。 |

## Strategy —— 寻路

**问题**：A\* 需要「到目标的代价估计」（启发式）和「每步代价」。把它们硬编码，换一种移动模型（比如对角线、地形代价）就得重写。

**方案**：`Heuristic` 和 `Cost` 是抽象基类；`Octile`/`Manhattan` 和 `UniformCost` 是可插拔策略。`find_path()` 把它们当参数传入，换策略时搜索主体一行不改。

```python
path = find_path(start, goal, walkable, Octile(), UniformCost(), allow_diagonal=True)
```

**被否决的替代**：在 `find_path` 里写 `if diagonal: ... else: ...` 分支。能用，但把代价模型锁死在算法里，也没法单独单测。

## State —— agent 行为

**问题**：agent 是 巡逻 → 追击 → 攻击 → 逃跑，带进入/退出副作用（如 `set_state`）。在字符串上写一大坨 `if/elif` 没法测，加状态就爆炸。

**方案**：每个状态是一个 `State` 子类，带 `on_enter` / `on_exit` / `update`（返回一个转移事件）。`FSM` 持有转移表 `{state: {event: next_state}}`，它从不知道某个状态「做什么」。

**被否决的替代**：枚举 + `match`/`switch` 块。小 FSM 够用，但它把「我在哪个状态」和「我做什么」搅在一起，加行为就得改中心函数（违反开闭原则）。

## Composite —— 行为树

**问题**：要表达「射程内就攻击，否则看到敌人就追，否则受伤就逃，否则巡逻」。把这段逻辑用函数嵌套，会产生共享控制流的意大利面。

**方案**：`Sequence`（快速失败 AND）、`Selector`（首个成功 OR）、`Inverter` 都是 `Node`；叶子是 `Action`/`Condition`。整棵树由同一个 `tick(agent, world, blackboard)` 调用搭起来，所以「子树就是节点」——这是教科书级的 Composite 结构。

```python
root = Selector([
    Sequence([Condition(in_range),   Action(attack)]),
    Sequence([Condition(enemy_seen), Action(chase)]),
    Sequence([Condition(low_hp),     Action(flee)]),
    Action(patrol),
])
```

## Observer —— 事件总线

**问题**：战斗、计分、调试覆盖层都想知道「某个 agent 死了 / 造成了伤害」，但不希望 `World` 知道它们的存在。

**方案**：`EventBus.subscribe(type, fn)` + `emit(event)`。生产者 emit，消费者 subscribe。`World` 完全不知道自己的监听者是谁。

## Dependency Inversion —— 架构基石

这是作品集故事里最重要的模式。`core/` 只 import `abc.py`。`pygame`（或未来的 UE/C++ 适配器）来实现 `IAgent` / `IWorld`。所以 AI 逻辑是一块**中间件**，能塞进任何 Python 游戏，或在 C++ 移植后塞进任何 C++ 引擎——**一行 `core/` 都不用改**。

```python
# core 依赖的是抽象，不是 pygame：
def tick(self, agent: IAgent, world: IWorld, dt: float) -> None: ...
```

## Factory —— brain 选择

`make_brain("fsm" | "utility" | "bt")` 返回正确的 brain。调用方只依赖返回对象的 `tick()` 接口，从不依赖具体类——所以加第 4 种 brain 只需在 factory 里改一行。

## 考试要点提炼

- **哪个模式，压什么力？** 上面每条都点出了「力」（没有这个模式会坏在哪），不只是背名字。
- **为什么不用替代方案？** 每个「被否决的替代」都是考试级答案。
- **一个模式一个职责。** `Strategy` 管算法、`State` 管状态、`Composite` 管树、`Observer` 管事件、`DIP` 管边界——互不重叠。
