# 演示指南 / Presentation Guide

> 用途：把整个 `game-ai-toolkit` 文件夹拷到**另一台电脑**上，零基础也能跑起来做演示。
> 面向：面试 / 作品集展示。这份 Demo 是**纯观赏型 AI 对抗**，你不用操作，看两支 AI 队伍自动打架即可。

---

## 1. 这份 Demo 是什么（先讲清楚，避免现场尴尬）

- 一个**引擎无关**的 Python 游戏 AI 库的可视化 Demo：红队（Team A）vs 蓝队（Team B）在网格地图上自动对战。
- 双方由**不同的 AI 大脑**驱动：`fsm`（状态机）/ `utility`（效用评分）/ `bt`（行为树）。
- **没有玩家操作**：AI 自己巡逻 → 发现敌人 → 追击 → A\* 绕墙寻路 → 交战 → 分出胜负。你只看。
- 关掉窗口 = 结束演示。
- 每个 agent 头顶有调试文字（当前状态 + 血量），血条随时可见，方便边看边讲。

---

## 2. 演示前：目标电脑需要什么

| 需要 | 说明 |
|---|---|
| Python 3.11 或以上 | 推荐 3.12。装完在终端输入 `python --version` 能看到版本号 |
| 能联网 | 首次需 `pip install` 装依赖（只需装一次） |
| 有显示器 + 桌面 | 窗口 Demo 需要本地桌面；无显示器也能跑 headless 模式看文字结果 |
| 项目文件夹 | 把整个 `game-ai-toolkit` 拷过去即可，**不需要 git、不需要编译器** |

> 演示前建议：在自己电脑上先 `pip install matplotlib` 并跑一次第 6 节的基准命令，把 `benchmarks/report_data/win_rate.png` 和 `metrics.csv` 一起拷走，现场就不依赖网速出图了。

---

## 3. 一分钟极简启动（最常用）

在**项目根目录** `game-ai-toolkit/` 下执行：

```bash
pip install numpy pygame
python examples/run_skirmish.py
```

默认效果：红队 FSM vs 蓝队 Utility，弹出**桌面窗口**自动对战，关窗结束。

> **重要澄清**：这个 Demo 是一个**本地桌面窗口程序（pygame）**，**不是网页、也不是网址链接**，不需要浏览器、不需要联网打开任何 URL。运行后会直接弹出一个游戏窗口；如果你只看到 CMD 里滚文字、没弹窗，说明 pygame 没装好或没被启用（见第 7 节排查）。

> 从本版起，脚本已**内置自动寻路**，`PYTHONPATH` 不再需要手动设置。Windows CMD 直接 `python examples/run_skirmish.py` 即可；嫌敲命令麻烦就用下面的 `run_demo.bat` 双击启动。

## 3.1 一键启动（推荐用于演示）

项目根目录已提供 `run_demo.bat`：双击即启动 Demo（红队行为树 vs 蓝队效用，现场最好看的组合），不用记命令、也不用手设 `PYTHONPATH`。

> 前提：目标电脑已 `pip install numpy pygame`，且项目放在**不含中文/空格**的路径下。
> 想换 AI 组合，右键编辑 `run_demo.bat` 最后一行，把 `bt utility` 改成 `fsm bt` 等即可。

---

## 4. 分系统详细步骤

### Windows（命令提示符 CMD）

```bat
:: 1) 装 Python：去 python.org 下 3.12，安装时务必勾选 "Add python.exe to PATH"
:: 2) 进入项目目录（改成你拷过去的路径，建议放不含中文/空格的路径，如 C:\demo\game-ai-toolkit）
cd C:\demo\game-ai-toolkit

:: 3) 装依赖
pip install numpy pygame

:: 4) 启动（指定地图 + 红队brain + 蓝队brain）
python examples/run_skirmish.py tests/fixtures/maps/skirmish.json fsm utility
```

> 脚本已自动把 `src/` 加入路径，`PYTHONPATH` 无需设置。PowerShell 用户同样直接 `python examples/run_skirmish.py ...` 即可。

### macOS / Linux

```bash
# 1) 确认 Python（没有就 brew install python / apt install python3）
python3 --version

# 2) 进入项目根目录
cd game-ai-toolkit

# 3) 装依赖（建议先建虚拟环境，不强制）
pip3 install numpy pygame

# 4) 启动
python3 examples/run_skirmish.py tests/fixtures/maps/skirmish.json fsm utility
```

---

## 5. 切换 AI 打法（现场最好看的组合）

命令格式：`python examples/run_skirmish.py <地图> <红队brain> <蓝队brain>`

`brain` 三选一：`fsm` / `utility` / `bt`

推荐现场直接用的几条：

| 命令（任意系统直接 `python examples/run_skirmish.py ...`，无需设 PYTHONPATH） | 观感 |
|---|---|
| `python examples/run_skirmish.py tests/fixtures/maps/arena.json bt utility` | **首选**：行为树果断、结束快、胜负明确，现场不拖沓 |
| `python examples/run_skirmish.py tests/fixtures/maps/arena.json fsm bt` | 看状态机 vs 行为树，两种架构风格对比 |
| `python examples/run_skirmish.py tests/fixtures/maps/arena.json utility utility` | 两边保守，常出拉锯，适合讲"效用决策的权衡" |

> 默认地图已换成更开阔的 `arena.json`（两队必相遇、战局利落）；`skirmish.json` 保留给量化基准用。

> 默认就是 **循环模式**（`--loop` 已开），一局打完自动重开、窗口不会自己关；想要只打一局后停，加 `--no-loop`。

三种 brain 的"性格"（来自量化基准）：
- **FSM**：激进，上手快但容易被风筝。
- **Utility**：保守、爱算分，最稳（负场最少）但偏慢。
- **BT**：果断、节奏快、胜率最高（基准约 95% vs FSM）。

### 5.1 玩家参与：实时发令（核心亮点）

这份 Demo 不只是"看两个 AI 打架"——**你是指挥官**，红蓝两队里你控制其中一队，
另一队是纯 AI。你发宏观指令，AI 自己做微操（寻路、索敌、开火）。这正好展示
架构的卖点：**AI 能响应外部指令，而不只是自己跑**。

窗口运行时按键（底部有提示条）：

| 按键 | 指令 | 效果（作用于你操控的那一队） |
|---|---|---|
| `1` | Attack 进攻 | 全速压上，拉满交战距离 |
| `2` | Defend 防御 | 推进接敌后守线、近距离 trade fire，不过度冒进 |
| `3` | Focus 集火 | 全队锁定**血量最低的敌人**，集中火力快速减员 |
| `4` | Retreat 撤退 | 边撤边向队形集结、贴脸才还手（避战，可能僵持→自动重开） |
| `5` / `0` | Auto 自动 | 取消指令，回到该 brain 的默认行为 |
| `T` | 切换操控队 | 在指挥红队 / 蓝队之间切换（HUD 标 `(YOU)`） |

要点：
- 指令通过 `World.set_order(team, ...)` 经 **eventbus** 广播，三种 brain（FSM/效用/行为树）
  都在同一个注入点读取并作为**硬约束门控**行为（按 Attack 时 Retreat 选项被移除，AI 绝不后退）
  ——**一个接口影响全部 AI 范式**。
- HUD 顶部实时显示双方存活数与当前指令，标 `(YOU)` 的是你操控的队。
- 现场最好讲的故事："我指挥蓝队，看我的策略能不能打赢纯 AI 的红队（行为树）。"

---

## 6. 顺手展示的"硬核"数据（30 秒讲清技术价值）

### 出胜率图表（需要 matplotlib）
```bash
pip install matplotlib
python tools/headless_eval.py
```
生成 `benchmarks/report_data/win_rate.png`（胜率柱状图）+ `metrics.csv`（胜率/胜负数/平均每 tick 耗时表）。现场把这张图投出来，比空讲有说服力。

### 跑测试证明质量
```bash
pip install pytest
pytest
```
显示 53 个测试通过（9 个 C++ parity 测试在无 C++ 环境时自动跳过）。

### 一句话架构亮点（讲给面试官）
> "同一份 JSON 行为/地图配置，同时驱动 Python 核心和 C++17 薄端口，跨语言 parity 测试保证结果逐字节一致——意味着这套 AI 能直接迁移进 Unreal / C++ 生产管线。而且 AI 是**可指挥**的：玩家/策划/脚本的宏观指令经 eventbus 注入，三种 AI 范式在同一个接口上响应，不是只会自己跑的黑盒。"

---

## 7. 录屏 / 截图（可选）

- 窗口 Demo：直接屏幕录制或截图即可。
- 终端录屏（可选）：`bash tools/record_demo.sh`（用 asciinema，需本地桌面环境手动跑）。
- 开发者小工具（非演示必需）：`python -m gameai.demo.config_editor tests/fixtures/maps/skirmish.json` 会打印地图尺寸/障碍数/出生点，可顺带展示"配置即数据"。

---

## 8. 常见问题排查

| 现象 | 原因 / 解决 |
|---|---|
| `ModuleNotFoundError: No module named 'pygame'` | 没装 pygame → `pip install pygame` |
| `ModuleNotFoundError: No module named 'gameai'` | 没在 `game-ai-toolkit/` 根目录跑，或 `src/` 文件夹被误删 → 回到第 4 节。本版脚本已自动加路径，正常情况不会触发 |
| 弹窗报 `SDL` / `No available video device` | 跑在没有显示器的服务器上 → 程序会自动回退 headless 打印文字结果；要窗口必须在本地桌面 |
| 中文/空格路径下诡异报错 | 把项目移到纯英文路径（如 `C:\demo\game-ai-toolkit`）再试 |
| 窗口一闪而过、CMD 里秒出文字结果 | 多半是 pygame 渲染时抛了异常（旧版未初始化）。已修复：脚本现在会**把真实报错打印出来**而不是静默跳过。把那一串 `!! pygame window failed: ...` 报错发我即可定位 |
| 窗口出来了但 agent 不动 | 极少见；按任意键/移动鼠标激活窗口，或检查是否卡在后台；循环模式会自动重开 |

---

## 9. 打包成 exe（双击即运行，目标电脑零依赖）

不想在现场敲命令、也不想目标电脑装 Python？打包成单个 exe 即可。

**在本机（有 Python+pygame 的电脑）双击 `build_exe.bat`**，它会：
1. `pip install pyinstaller`（打包工具）
2. 用 PyInstaller 把 Python + pygame + numpy + 项目代码冻结成 `dist\gameai-skirmish.exe`
3. 地图 JSON 已内嵌进 exe（用 `--add-data`）

**结果**：把 `dist\gameai-skirmish.exe` 拷到任意 Windows 电脑，双击就能跑——目标电脑**不需要装 Python、不需要 pygame、不需要联网**。默认就是红队 bt vs 蓝队 utility 循环演示，关窗退出。

> 想换 AI 组合再打包：编辑 `build_exe.bat` 末尾，把 `examples/run_skirmish.py` 改成 `examples/run_skirmish.py fsm bt`（或 `utility utility`）。
> 若双击没反应：在 CMD 里直接运行该 exe 看报错；或把 `--noconsole` 去掉重新打包以显示错误黑框便于排查。
> 体积约 30–50 MB（自带 Python 运行时），属正常。

---

## 10. 演示台词参考（求职 30 秒）

> "这是一个**引擎无关**的游戏 AI 核心，纯 Python 实现 **FSM、行为树、A\*、效用** 四种子系统。
> 左边红队、右边蓝队由不同 AI 策略驱动，自动对抗——你能看到它们巡逻、发现敌人、绕墙寻路、交战。
> 同一份 JSON 配置既驱动 Python 也驱动 C++ 端口，跨语言结果一致，所以这套 AI 能直接迁移进 Unreal / C++ 生产管线。"

---

## 11. 打包带走清单

- [ ] **最省事**：只拷 `dist\gameai-skirmish.exe` 一个文件到演示电脑，双击即运行（无需 Python）
- [ ] 或整份 `game-ai-toolkit` 文件夹（U 盘 / 网盘均可，无需 git），用 `build_exe.bat` 现场打包 / 用 `run_demo.bat` 直接跑
- [ ] 若走"源码运行"路线：目标电脑已装 Python 3.11+（演示前确认 `python --version`）且联网（或提前装好 `numpy pygame matplotlib pytest`）
- [ ] 可选：提前生成的 `benchmarks/report_data/win_rate.png` + `metrics.csv` 一起拷走
- [ ] 演示路径避开中文/空格

> 需要纯英文版（面向海外面试官）可告诉我，我另出一版 `PRESENTATION_GUIDE_EN.md`。
