# Game-AI Toolkit

一个**引擎无关（engine-agnostic）**的游戏 AI 库，用 Python 编写，并附带一个薄 C++17 移植版，用来证明这套 AI 能迁进 UE / C++ 生产管线。

core 只依赖它自己（抽象接口在 `src/gameai/core/abc.py`）。引擎——包括内置的 `pygame` demo——都是实现这些接口的可插拔适配器。同一份中立的 JSON 行为/地图定义，同时驱动 Python core 和 C++ 移植版；跨语言的 **parity 测试**断言两者产出**逐字节一致**的结果。

## 亮点（作品集 / 面试用）

- 四个可直接落地的 AI 子系统：**FSM**、**行为树（Behavior Tree）**、**A\*** 寻路、**Utility** 决策打分，外加 **Steering 9 个行为**（seek / arrive / flee / pursue / evade / separation / collision_avoidance / obstacle_avoidance / wander）。
- **LLM 混合架构（已实现）**：确定性 FSM 决定 NPC「做什么」，可选的 LLM 层决定它「说什么」。LLM 只产出「台词 + 意图」，字段写权限由 `core/validator.py`（白名单 + 数值区间）守门，状态转移唯一权威仍是 FSM 转移表。含「越权写 `gold=999` 被拒」与「断网降级模板台词」两个可跑用例。**核心原则：绝不能用 LLM 去校验 LLM。** 见 `src/gameai/integrations/llm_brain.py`、`examples/llm_npc_demo.py`。
- 架构清晰，体现 GoF 设计模式：State、Composite、Strategy、Observer、依赖倒置（Dependency Inversion）、接口隔离（Interface Segregation）。
- 跨语言 parity：Python 和 C++ 跑**同一套**行为，输出一致。
- 量化评估框架（胜率、决策延迟、目标达成率、路径质量）。
- 完整文档：`DESIGN_PATTERNS.md`、`ARCHITECTURE.md`、`PORTING_GUIDE.md`、`EVALUATION.md`、以及 ADR。

## 快速开始

```bash
pip install -e ".[dev]"
pytest                       # 45 个测试全绿（core + sim + steering + parity*）

# 无头（headless）小规模对战基准（无需显示器）
python tools/headless_eval.py tests/fixtures/maps/skirmish.json fsm,utility,bt 20

# 可玩 demo（需要 pygame）：A=FSM 对 B=Utility，在 skirmish 地图上
python examples/run_skirmish.py tests/fixtures/maps/skirmish.json fsm utility

# C++ 薄移植版（需要 C++17 工具链 + CMake）
cd cpp && cmake -S . -B build && cmake --build build -j && cd build && ctest --output-on-failure
```
*\*parity 测试默认自动跳过，除非先编译出 C++ 的 `parity_runner` 可执行文件——它们在 `cpp` CI job 里跑，那里会先编译移植版。*

## 目录结构

```
src/gameai/core/   # 零引擎依赖的 AI 核心（这才是资产本体）
src/gameai/sim/    # 无头 World + Agent + 3 个可互换 brain（FSM/BT/Utility）
src/gameai/demo/   # pygame 适配器 + HUD 覆盖层 + JSON 配置编辑器（引擎相关）
tests/             # pytest 套件 + 共享 JSON fixtures
cpp/               # C++17 薄移植版（M4）
docs/              # 架构、设计模式、移植指南、ADR
tools/             # 无头评估、录制
benchmarks/        # headless_eval 产出的 metrics.csv + win_rate.png
```

> 状态：**M1 + M2 + M3 + M4 已完成。** 引擎无关 core（FSM/BT/A\*/Utility/steering/agent）、
> 一个带三种可互换 AI brain 的无头小规模对战模拟、一个 pygame 渲染器 + 配置编辑器、
> 以及一套量化评估框架。C++17 薄移植版（FSM/BT/A\*/Utility）在 CMake + GoogleTest 下编译通过，
> 带跨语言 parity 测试。45 个测试全绿（9 个 parity 测试在 C++ exe 编译前跳过）。
> 求职材料：`DESIGN_PATTERNS.md`、`PORTING_GUIDE.md`、`EVALUATION.md`、ADR ×3。
