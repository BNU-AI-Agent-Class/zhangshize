# Agent 作业 2 指南｜给你的 mini Claude Code 添把新武器

> **前提**:课上已跑通 c0–c5(不然先回 `教程_从s3到miniClaudeCode.md`)。
>
> **为什么作业都在 demo_project 上做?** 因为这些机制的价值只有在**真实项目**上才看得出来——`demo_project/` 就是给你准备的一个"麻雀虽小五脏俱全"的真实小项目(多文件 + 一个藏起来的 bug)。在它上面做作业,你练的是**用 agent 干真实开发活**,而不是"创建 hello.txt"。先逛一圈:`cd demo_project && cat README.md`,再跑 `python -m notes_app.cli list`。
> **作业**:从下面**三选一**(必做),再挑战 **capstone 加分题**。以 c1/c3/c5 为基础改,**每个改动都要能单独跑通**。
> **提交**:改好的 `.py` + 一段说明,推到你自己的 GitHub 仓库(和作业1同一个仓库,新建 `hw2/` 文件夹)。
> **原则**:这份指南**不给答案代码**。每题有"目标 / 真实场景 / 验收 / 三级提示",卡住了一层层翻,别一上来就看提示③。

> 建议先把 `demo_project/` **复制一份**到 `hw2/` 下再折腾,别改坏原件:`cp -r ../demo_project hw2_demo`(路径按你的仓库结构调整)。

---

## 必做(三选一)

### 选项 A｜给工具箱加一件"搜索"工具(改 c1)——真实开发最高频的动作

**真实场景**:你接手 `demo_project`,想知道"哪个文件调用了 `save_note`?"、"`stats` 命令定义在哪?"——这就是每个程序员每天都在做的**全项目搜索**。真 Claude Code 有 `Grep`/`Glob` 工具专门干这个。你来给 mini 版补上。

**目标**:在 `c1_toolbox.py` 基础上新增一个 `search` 工具(在项目里按关键词搜文件内容,返回命中的文件名+行),并让 agent 真的调用它。

**验收**(在 demo_project 上)
```
你：在 demo_project 里搜一下，哪个文件用到了 add_note？
→ [调用] search(...) → 定位到 store.py（定义）和 cli.py（调用）
```

<details><summary>💡 提示①(概念级):一个工具"存在"要几样东西?</summary>

回想 c1 里工具是怎么"存在"的:一个**函数**,登记进 **TOOLS 字典**,再在 **SYSTEM** 里介绍给 AI。三样缺一不可。你的 `search` 也一样。
</details>

<details><summary>💡 提示②(操作级):search 内部怎么搜?</summary>

最朴素的做法:遍历目录下的文件,逐个打开、逐行看有没有包含关键词,命中就记下"文件名:行号:该行"。"Python 怎么遍历一个目录下所有文件""怎么逐行读文件"——这两个都可以问 AI(问积木,不是问答案)。参数建议 `{"keyword": "...", "path": "demo_project"}`。
</details>

<details><summary>💡 提示③(兜底级):自查清单</summary>

- 函数参数名,和你在 SYSTEM 里写的 `args` 字段名一致吗?(派发是 `TOOLS[name](**args)`)
- 二进制文件/编码错误会不会让它崩?(可以 try 一下跳过读不了的文件)
- 返回内容别太长(几十个命中就够),否则会把上下文塞爆——想想这跟 c3/c4 学的有没有关系
- 跑通后,问一个搜不到的词,它会不会体面地说"没找到"?
</details>

---

### 选项 B｜给子 agent 装一个"代码审查员"人设(改 c3)——真 CC 的 code-review 子 agent

**真实场景**:`demo_project` 里藏着一个 bug(`analyze.py` 的 `stats` 在没有带标签的笔记时会崩)。真 Claude Code 可以派一个"审查员"子 agent 去通读代码、挑毛病。你来做一个 mini 版。

**目标**:把 `c3_subagent.py` 的子 agent 改成"代码审查员":主 agent 派它去读 `demo_project` 的代码,**找出可能的 bug 并报告**(不用它修,只报告)。

**验收**
```
你：派审查员去 demo_project 检查代码质量，报告潜在 bug
→ subagent 通读后返回：analyze.py 的 summary() 在无标签时会 IndexError（能定位到就算成功）
```

<details><summary>💡 提示①(概念级):子 agent 的"人设"写在哪?</summary>

c3 里,子 agent 的第一条 `system` 消息决定了它是谁、用什么眼光看东西——和昨天 s5 换 skill 文件同理。把"你是子助手"改写成"你是代码审查员"。
</details>

<details><summary>💡 提示②(操作级):要改哪几处?</summary>

主要改 `subagent()` 里那条 `system` 消息:告诉它"你是代码审查员,任务是读代码、找逻辑漏洞(空输入、越界、异常没处理…),只报告不修改"。子 agent 需要能读文件——它已经有 bash 了,可以用 `cat`/`ls`;想更专业可以给子 agent 也配 `read_file`。再顺手在主 SYSTEM 里说清"什么时候派审查员"。
</details>

<details><summary>💡 提示③(兜底级):自查清单</summary>

- 审查员报告的 bug,是不是**真的**在代码里?(去 `analyze.py` 核对,别信它编的)
- 它会不会读了一个文件就急着下结论?想让它多读几个再报告,提示词该怎么写?
- 主 agent 有没有把审查员的结论**完整转达**给你?
</details>

---

### 选项 C｜防崩加强版(改任一版)——堵住 c1 还没堵的洞

我们的 c1–c5 已经用 `try/except` 挡住了"解析坏 JSON"。但还有洞:**AI 指定一个不存在的工具名**(如 `{"tool": "fly", ...}`)会 `KeyError` 直接崩;而且现在的重试是**无限**的。你来把这两个洞堵上。

**真实场景**:模型偶尔会"幻觉"出一个不存在的工具名(昨天讲过锯齿智能)。真 Claude Code 遇到这种会告诉模型"没这个工具",而不是崩溃。

**验收**
```
临时在 SYSTEM 里加一个假工具名诱导它调用，
→ 程序不崩，提示"没有这个工具，可用的有：…"，继续；连续失败若干次能体面停下
```

<details><summary>💡 提示①(概念级):还剩哪两个洞?</summary>

① **未知工具**:`TOOLS[name]` 里 `name` 不在字典会抛 `KeyError`。② **无限重试**:`except` 里只有 `continue`,模型一直犯错就永远出不来。
</details>

<details><summary>💡 提示②(操作级):怎么补?</summary>

① 派发前先判断 `name in TOOLS`,不在就别调,给 AI 一条"没有叫 xxx 的工具,可用的有:…"再 continue。("字典有没有这个键"怎么判断,可以问 AI。)② 加个计数器,重试超过 N 次就打印放弃并 break。
</details>

<details><summary>💡 提示③(兜底级):自查清单</summary>

- "解析失败"和"未知工具"是两种错,给 AI 不同的提示它才知道怎么改
- 计数器要在**成功一步后清零**,否则正常长任务会被误杀
- 补完后正常任务还跑得通吗?故意点名假工具,它能自己纠正回来吗?
</details>

---

## Capstone 加分题｜真的修好那个 bug

**这是最像"用真 Claude Code 干活"的一题。**

`demo_project` 的 `stats` 命令在**一条带标签的笔记都没有**时会崩(`analyze.py` 里 `counts[0]` 越界)。你的任务:**用你自己改好的 mini Claude Code**(任意一版),让它去**定位并修好**这个 bug。

**怎么复现 bug**:把 `data/notes.json` 换成一个都不带 `#标签` 的版本,再跑 `python -m notes_app.cli stats`,它会 `IndexError`。

**验收 & 提交**
- 修好后:空标签时 `stats` 不崩,而是友好提示(如"还没有任何标签")
- 提交:①修改前后的 `diff` ②你和 mini Claude Code 的**完整对话过程**(截图或贴文本)③一段话:**这次它哪一步最像真 Claude Code?哪一步最不像?你觉得还差哪个机制?**

<details><summary>💡 提示:让它自己找,别直接告诉它答案</summary>

好的用法是:先让它 `stats` 跑一次看到报错 → 让它读 `analyze.py` → 让它说出"为什么会崩" → 再让它改。全程你只把关、不代劳。这正是你以后用 Claude Code 调 bug 的真实姿势。(如果你做了选项 B 的审查员,可以先让审查员定位,再让主 agent 修——这就是多 agent 协作。)
</details>

---

## 提交前检查

- [ ] 改动的文件能**单独 `python xxx.py` 跑通**
- [ ] `.env` / API key **没有**被传上 GitHub(`.gitignore` 里有 `.env`)
- [ ] `hw2/` 里有:你的代码 + 一个 `说明.md`(选了哪题 / 新增了什么 / 遇到的最大一个坑)
- [ ] 你能对助教**口头讲清**你加的每一处代码在干什么

> 怎么问 AI 不算作弊?**问概念、问报错、问 Python 怎么写某个小功能——都行;让 AI 直接把整道题的答案文件写给你——不行。** 你交的每一行,都要能自己解释。

---
*MIT License｜郑先隽,北师大心理学部教授,人本AI设计与创新｜助教:元真、师婕*
