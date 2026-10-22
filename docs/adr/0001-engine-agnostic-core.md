# ADR 0001：引擎无关的 core

## 状态
已接受（M1）。

## 背景
项目必须展示「可移植到 UE / C++ 生产管线」的游戏 AI，而不是一个 Python-only 玩具。一个会 import 引擎代码（比如 pygame）的 core，无法在别处复用，还会削弱「可迁移」这个卖点。

## 决策
AI 逻辑放在 `src/gameai/core/`，**禁止** import 任何引擎相关模块。所有与引擎的交互都通过 `abc.py` 里定义的抽象接口（`IAgent`、`IWorld`、`IBlackboard`、`IEventSink`）进行。`demo/` 包是（唯一的）引擎适配器，依赖 `core/`，绝不反向。

## 后果
- core 无需渲染器就能单测（快、确定）。
- 同一个 core 能跑在 pygame、无头评估器、或 C++ 移植版下。
- 引擎相关的关切（渲染、输入）被隔离、可替换。
- 权衡：core 不能直接用引擎的便利设施，必须走接口，会多一点点样板代码。
