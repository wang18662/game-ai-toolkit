# Game-AI Toolkit 项目学习状态（协同接口文件）

本文件是 **「对话（本会话）推进」** 与 **「自动化·每日技术训练」** 之间的协同接口。

## 当前阶段：构建完成（2026-09-04）
**M3 + M4 已全部落地并验证。** 用户要求对话侧只推进项目、不做逐节点讲解；
因此 P1→P8 的"讲解中/已完成"状态暂未翻动。自动化"项目实战轨道"在构建期内
可继续围绕 `src/gameai/core/` 源码出**概念预习**练习，帮用户在已成型代码上熟悉。

## 已完成的里程碑
- **M1** 基础：仓库骨架、`abc` 接口、`vector`/`eventbus`/`blackboard`/`json_defs`、CI、ADR×1。
- **M2** 核心 AI：FSM/行为树/A*/效用 + 29 测试绿（Python 全实现）。
- **M3** 工具+演示：`steering`/`agent`/`sim`(World 含 FSM/BT/Utility 三套 brain) + pygame 渲染 + `config_editor` + `headless_eval` 量化评估（36 测试绿）。
- **M4** C++ 端口：FSM/行为树/A*/效用 四子系统（C++17，CMake+GoogleTest）+ `parity_runner` + `tests/test_parity.py` 跨语言 parity + 求职文档套件（DESIGN_PATTERNS/PORTING_GUIDE/EVALUATION/ADR×3）+ 架构图。

## 节点清单（构建完成后，按用户节奏逐条讲解，P1→P8）
| 节点 | 源码文件 | 核心知识点 | 状态 |
|------|----------|-----------|------|
| P1 | `core/vector.py` | 类与对象、`@dataclass`、运算符重载、`math.hypot` | 未讲解（项目已用） |
| P2 | `core/blackboard.py` + `core/eventbus.py` | `Dict[str,Any]`、实现抽象接口、`Observer` 模式 | 未讲解 |
| P3 | `core/fsm.py` | `@property`、嵌套 `Dict`、`State` 模式 | 未讲解 |
| P4 | `core/utility.py` | `@dataclass` 嵌套、`field(default_factory)`、闭包/`Callable` | 未讲解 |
| P5 | `core/behavior_tree.py` | 多层继承、多态 `tick`、`Composite` 模式 | 未讲解 |
| P6 | `core/astar.py` | `heapq`、`Tuple` 别名、`Callable`/`__call__`、`Strategy`、A* 算法 | 未讲解 |
| P7 | `core/abc.py` | `ABC`/`abstractmethod`、`Enum`、`typing`、依赖倒置/接口隔离 | 未讲解（最重要） |
| P8 | `core/json_defs.py` | `@classmethod`、字典推导式、跨语言 JSON schema | 未讲解 |

## 对话侧进度记录
- 2026-09-04：用户决定先完成 M3+M4 再讲解；进入构建期并完成 M3+M4。
- M4 交付：C++17 端口（4 子系统）+ GoogleTest 单测 + `parity_runner` + `tests/test_parity.py`（exe 未构建时自动 skip）+ 求职文档套件。
- 注意：本地无 C++ 编译器，C++ 端口靠 CI（ubuntu + cmake/g++/FetchContent）编译验证；parity 测试在 `cpp` CI job 构建后运行。
