# 1_claude_code_basic — 亲手复现一个 mini Claude Code

> 昨天你用 30 行(`0_agent_basic/s3_agent.py`)造出了第一个会干活的 agent。
> 今天,我们把它一步步升级成一个**有工具箱、会规划、能派子智能体、会压缩记忆、有安全门**的 mini Claude Code。
> **"What I can't create, I don't understand."** —— 造得出来,才算真懂。

## 六个阶段(每步只加一个想法)

| 文件 | 新想法 | 一句话 |
|---|---|---|
| `c0_json.py` | JSON 协议 | 把 s3 的"命令:/完成:"文本协议,升级成结构化 JSON |
| `c1_toolbox.py` | 工具箱 | 不止 bash——加 read_file / write_file,按名字派发 |
| `c2_todo.py` | 计划是工具 | TodoWrite:让 agent 先列计划、边做边勾 |
| `c3_subagent.py` | 子智能体 | 派一个有独立上下文的子 agent 去干脏活,只拿回摘要 |
| `c4_compact.py` | 上下文压缩 | 历史太长就自动折叠成摘要,窗口重开 |
| `c5_guard.py` | 权限门 | 危险命令执行前先问人(Human-in-the-loop) |

终点 `c5` 只有 ~35 行,却已经拥有真 Claude Code 的五根支柱的雏形。
每个 `c*.py` 文件头都有一行"**对照真 Claude Code**"注释,告诉你这一步在真 CC 里对应哪个功能。

## demo_project/ — 练习靶子(为什么要有它?)

**先说为什么给你一个"假项目"练手。**
昨天的练习都是"创建 hello.txt"这类一次性小任务——但真实开发从来不长这样:你面对的是一个**有很多文件、互相调用、还可能藏着 bug** 的项目。
mini Claude Code 的五个机制(工具箱 / 计划 / 子 agent / 压缩 / 权限),恰恰**只有在这种真实项目上才显出价值**:简单任务用不上,复杂项目离不开。如果只在"创建 hello.txt"上练,你永远看不出它们为什么存在。

所以我们准备了 `demo_project/`——一个**麻雀虽小、五脏俱全**的玩具笔记本 CLI(`notes_app`:多文件 + README + TODO + 一个故意藏起来的 bug)。
c0–c5 的每个"复杂例子"和全部作业,都在这**同一个**靶子上跑,人人一致、可复现,让你亲眼看到每个机制为什么必须存在。先逛一圈:

```bash
cd demo_project && cat README.md
python -m notes_app.cli list
python -m notes_app.cli stats
```

## 快速开始

```bash
# 1. 复用昨天配好的环境(.env 里已有 OPENROUTER_API_KEY)
cp ../0_agent_basic/.env .          # 或自己新建 .env 写一行 OPENROUTER_API_KEY=...

# 2. 依赖和昨天一样,已装则跳过
pip install openrouter python-dotenv

# 3. 从 c0 开始,一个一个跑
python c0_json.py
#   你：在当前目录创建 hello.txt 内容为 hi，然后列出 txt 文件
```

每个文件都能**单独运行**,退出按 `Ctrl-C`。

## 怎么学(建议顺序)

1. 先跑 `c0`,再打开 `c0_json.py` 对着注释读一遍,和昨天的 `s3_agent.py` 逐行对比——只有"协议"变了。
2. 每往下一个文件,先 `diff` 一下和上一个的区别(变化很小),再跑,再想"为什么要加这个"。
3. 配套教程:`教程_从s3到miniClaudeCode.md`(每阶段的目标/讲解/验收/思考题)。
4. 想要可视化、能勾选的版本:浏览器打开 `web/index.html`(离线可用)。
5. 作业:`作业指南_Agent作业2.md`。

## 和"真 Claude Code"的关系

我们手写 JSON 协议,是为了**看得见每一个字节**。真 Claude Code 用模型原生的 tool_use(更稳),机制却完全一样。
想读工业级实现,看 `../agent_projects/learn-claude-code/`(在线版 https://learn.shareai.run/zh/)——它把同样的思路做到 s01–s12,我们的 c0–c5 正是它的"最小可理解版"。

---
*MIT License｜郑先隽,北师大心理学部教授,人本AI设计与创新｜助教:元真、师婕*
