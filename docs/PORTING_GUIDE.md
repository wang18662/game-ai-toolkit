# 移植指南 —— Python core → C++17 / UE

Python core 从第一天起就是为可移植设计的：`core/` **零**引擎依赖，只依赖 `abc.py` 抽象。本指南讲怎么把这套 AI 带进 C++ / Unreal Engine 生产环境，以及 `cpp/` 薄移植版已经证明了什么。

## C++ 移植版已经覆盖了什么

`cpp/` 目录是对**算法价值最高的四个子系统**的薄移植。它不是完整重写——它证明这套 AI 能在 C++ 里原生跑。

| 子系统 | 移植了吗？ | 证据 |
|---|---|---|
| FSM（State） | ✅ | `cpp/.../fsm.hpp`、`cpp/src/fsm.cpp` |
| 行为树（Composite） | ✅（header-only） | `cpp/.../behavior_tree.hpp` |
| A* 寻路（Strategy） | ✅ | `cpp/.../astar.hpp`、`cpp/src/astar.cpp` |
| Utility / 决策打分 | ✅ | `cpp/.../utility.hpp`、`cpp/src/utility.cpp` |
| Steering（arrive/seek/flee） | ❌ 仅 Python | 留在 `core/steering.py` |
| 事件总线（Observer） | ❌ 仅 Python | 留在 `core/eventbus.py` |

## 编译 C++ 移植版

要求：C++17 编译器（MSVC / g++ ≥ 9 / clang ≥ 9）和 CMake ≥ 3.20。`googletest` 和 `nlohmann/json` 通过 CMake `FetchContent` 拉取（首次编译需要联网）；`vcpkg.json` 记录了等价的 vcpkg 包。

```bash
cd cpp
cmake -S . -B build
cmake --build build -j
cd build && ctest --output-on-failure     # 单元测试
../build/parity_runner astar ../tests/fixtures/maps/skirmish.json 0 0 5 0   # 冒烟测试
```

## 类型映射：Python → C++

| Python | C++ | 说明 |
|---|---|---|
| `@dataclass` | `struct` | 普通聚合，无需继承 |
| `ABC` / `@abstractmethod` | `struct X { virtual ~X()=default; virtual … =0; }` | 抽象基类 |
| `Callable[[IAgent, IWorld], float]`（如 utility 输入函数） | `std::function<double(const AgentView&, const WorldView&)>` | **最棘手的那个**——见下 |
| `Dict[str, Any]`（blackboard） | `std::map<std::string, double>` | 收窄到我们实际存的标量类型 |
| `Enum` | `enum class` | `CurveType`、`Status`、`Team` |
| `List[Node]`（BT 子节点） | `std::vector<std::unique_ptr<Node>>` | 用 `unique_ptr` 管所有权 |
| `Optional[str]`（FSM 事件） | `std::optional<std::string>` | 语义完全一致 |

### 唯一真正棘手的映射：utility 输入函数

Python 里一个「考量（consideration）」是 `Consideration(input_fn, curve, min, max, weight)`，其中 `input_fn` 是**任意 Python 可调用对象**——甚至可以是捕获 agent 状态的闭包。C++ 没有能跨 DLL/UE 边界的一等公民可移植闭包，所以移植版用固定的 `std::function` 配一个*窄视图*接口：

```cpp
struct AgentView { double hp, max_hp, sight_range, attack_range; Vector2 pos; };
struct WorldView { bool enemy_exists; double enemy_distance; };
using InputFn = std::function<double(const AgentView&, const WorldView&)>;
```

skirmish 的三个输入（`enemy_closeness`、`in_attack_range`、`retreat_score`）直接对着 `AgentView`/`WorldView` 实现。**给 UE 的教训**：每个子系统暴露一个小的只读视图 struct；绝不要把整个 `AActor` 传进纯 AI 代码。这样打分数学才可单测、且引擎无关。

## Parity：证明两种语言一致

`cpp/src/parity_runner.cpp` 读取 Python core 用的**同一份 JSON map**，打印归一化结果（`path` 字符串、选中的选项名、或最终 FSM 状态）。`tests/test_parity.py` 然后用 Python core 在相同输入上重算，并断言字节级一致。在 CI 里 build 完 C++ 移植版后跑：

```bash
pytest tests/test_parity.py -q        # 除非 parity_runner 已构建，否则跳过
```

如果你改了 Python AI，就重跑 parity——任何不一致都是移植 bug，不是「语言差异」。

## 嵌入 Unreal Engine

两种现实的集成方式：

1. **桥接服务（首版推荐）。** 把 Python AI（或 C++ 移植版）当作本地进程跑；UE 客户端通过 `WebSocket`/`HTTP` 消息（携带 `WorldView`）问它「agent X 现在该干什么？」。这能让 AI 待在自己的进程里，正是很多工作室隔离行为的方式。
2. **原生模块。** 把 `cpp/` 编译成 UE 模块（`*.Build.cs` 链接 `gameai_core` 静态库）。把 `AgentView`/`WorldView` 的填充改成从 `AActor`/`UWorld` 读取；`find_path` / `decide` / `FSM::update` 保持不动——它们本来就引擎无关。

针对行为树，你也可以用 [BehaviorTree.CPP](https://github.com/BehaviorTree/BehaviorTree.CPP) 的 XML 来写树，Python 侧只当**编辑器/调试器**用——这正对应真实工作室里「脚本工具（Python）vs C++ 运行时」的分工。
