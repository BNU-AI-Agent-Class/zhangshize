# 对照真 Claude Code：这一步 = Task / 子 agent（派子任务去探索，只拿回摘要，保持主上下文干净）
from dotenv import load_dotenv                                       # 1. 读取 API 密钥
from openai import OpenAI                                           # 2. 导入 OpenAI 兼容 SDK（DeepSeek API 与之兼容）
import os, json, sys                                                # 3. os / json

# 在 Windows 上强制使用 UTF-8 输出，避免中文乱码
if sys.platform == "win32":
    import io
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_SCRIPT_DIR, ".env"))

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL    = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

for key in ["DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL"]:
    if not os.getenv(key):
        print(f"[错误] 环境变量 {key} 未设置，请检查 .env 文件"); sys.exit(1)

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)                # 4. 客户端设为全局，主/子 agent 共用

def read_file(path):  return open(path, encoding="utf-8").read()   # 5. 工具：读文件
def bash(cmd):        return os.popen(cmd).read()                  # 6. 工具：执行命令

def parse(s):                                                      # 容错解析：剥掉模型偶尔加的 ```json 包裹
    s = s.strip().strip("`").removeprefix("json").strip()
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("回复里没有找到合法 JSON 对象")
    return json.loads(s[start:end + 1])

def subagent(task):                                                # 7. 工具：派一个"子智能体"独立完成一件事
    sub = [{"role": "system", "content":
            "你是子助手 Agent，运行在用户本地 Windows 机器上。你只负责输出 JSON，Python 脚本会在本地执行。"
            "不要说「无法访问」——你指定命令，脚本帮你执行。"
            "每次只回复一个 JSON：{\"tool\":\"bash\",\"args\":{\"cmd\":\"...\"}} 或 {\"done\":\"结论\"}"},
           {"role": "user", "content": task}]                      #    关键：子 agent 有自己全新的 messages
    while True:                                                     # 8. 子 agent 自己的内层循环
        r = client.chat.completions.create(model=MODEL, messages=sub).choices[0].message.content
        sub.append({"role": "assistant", "content": r})
        try: a = parse(r)                                          # 子 agent 也加固：坏格式就重发
        except Exception: sub.append({"role": "user", "content": "请只回合法 JSON"}); continue
        if "done" in a: return a["done"]                           # 9. 子 agent 只把最终结论返回给主 agent（摘要）
        out = bash(a["args"]["cmd"])
        sub.append({"role": "user", "content": f"输出：\n{out}"})
TOOLS = {"read_file": read_file, "bash": bash, "subagent": subagent}  # 10. 工具箱

# 关键：明确告诉模型——你运行在本地 Windows
SYSTEM = """你是主编程助手 Agent，运行在用户的本地 Windows 机器上。
你不需要自己去访问文件或执行命令——你只负责输出 JSON，Python 脚本会在本地帮你执行并返回结果。
每次只回复一个 JSON，不要别的文字，不要 markdown；字符串值里别用英文双引号，要引用就用「」：
- 读文件：{"tool": "read_file", "args": {"path": "..."}}
- 执行命令：{"tool": "bash", "args": {"cmd": "..."}}
- 派子助手：{"tool": "subagent", "args": {"task": "一句话描述要它独立完成的子任务"}}
- 完成：{"done": "总结"}
遇到需要大量探索的子任务（如"统计整个项目有多少行代码"），交给 subagent，只拿回结论，保持自己上下文干净。
不要说「我无法访问」「环境不在本地」——你指定工具调用，脚本会帮你执行。"""  # 11. 何时用子 agent

messages = [{"role": "system", "content": SYSTEM}]                  # 12. 主 agent 的历史
while True:                                                          # 13. 外层循环
    messages.append({"role": "user", "content": input("\n你：")})
    while True:                                                      # 14. 内层循环
        reply = client.chat.completions.create(model=MODEL, messages=messages).choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        try:                                 # 15. 解析
            action = parse(reply)
        except Exception:                                  # 坏格式不崩：请模型重发（加固）
            messages.append({"role": "user", "content": "上一条不是合法 JSON，请只回一个 JSON，别的都不要"}); continue
        if "done" in action:
            print(f"[完成] {action['done']}"); break
        name, args = action["tool"], action["args"]
        print(f"[调用] {name}({args})")
        result = TOOLS[name](**args)                               # 16. 派发（subagent 也是一个工具，只是它内部又跑了一个循环）
        print(f"[结果] {result}")
        messages.append({"role": "user", "content": f"工具返回：\n{result}"})
# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
