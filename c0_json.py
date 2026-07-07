# 对照真 Claude Code：这一步 = tool_use（模型返回结构化工具调用，我们用手写 JSON 做极简版）
from dotenv import load_dotenv                                       # 1. 读取 .env 里的 API 密钥
from openai import OpenAI                                           # 2. 导入 OpenAI 兼容 SDK（DeepSeek API 与之兼容）
import os, json, sys, subprocess                                    # 3. os 执行命令；json 解析结构化协议；subprocess 捕获 stderr

# 在 Windows 上强制使用 UTF-8 输出，避免中文乱码
if sys.platform == "win32":
    import io
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

# 用脚本所在目录的 .env，确保从任何位置运行都能读到
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_SCRIPT_DIR, ".env"))

# API 配置（每个文件独立，不依赖外部文件）
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL    = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

# 启动前检查
for key in ["DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL"]:
    if not os.getenv(key):
        print(f"[错误] 环境变量 {key} 未设置，请检查 .env 文件"); sys.exit(1)

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)                # 5. 创建 DeepSeek 客户端

def parse_json(s):                                                  # 模型偶尔会返回 ```json 包裹的 JSON，剥掉再解析
    s = s.strip().strip("`").removeprefix("json").strip()
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("回复里没有找到合法 JSON 对象")
    return json.loads(s[start:end + 1])

# 关键：明确告诉模型——你运行在本地 Windows，命令由 Python 脚本执行，不是你自己执行
SYSTEM = """你是一个编程助手 Agent，运行在用户的本地 Windows 机器上。
你不需要自己去访问文件或执行命令——你只负责输出 JSON，Python 脚本会在本地帮你执行并返回结果。
每次只回复一个 JSON，不要有别的文字，不要用 markdown 包裹；字符串值里别用英文双引号，要引用就用「」：
- 要执行命令时：{"tool": "bash", "args": {"cmd": "要执行的命令"}}
- 任务完成时：  {"done": "给用户的总结"}
不要说「我无法访问」「环境不在本地」——你指定命令，脚本会帮你执行。"""          # 4. 系统提示词：把 s3 的"命令:/完成:"文本协议，升级成 JSON 协议

messages = [{"role": "system", "content": SYSTEM}]                  # 6. 对话历史，第一条是系统提示
while True:                                                          # 7. 外层循环：等用户下达新任务
    messages.append({"role": "user", "content": input("\n你：")})    # 8. 用户输入存入历史
    while True:                                                      # 9. 内层循环：Agent 自主执行直到完成
        reply = client.chat.completions.create(
            model=MODEL,
            messages=messages).choices[0].message.content            # 10. 调用模型，取回复
        messages.append({"role": "assistant", "content": reply})    # 11. AI 回复存入历史
        try:
            action = parse_json(reply)                               # 12. 关键升级：把 JSON 文本解析成 Python 字典
            if "done" in action:                                     # 13. 如果是完成信号 → 跳出内层循环
                print(f"[完成] {action['done']}"); break
            cmd = action["args"]["cmd"]                              # 14. 从结构化字段里取命令（不再靠字符串切割）
            print(f"[执行] {cmd}")
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")  # 15. 执行命令并捕获 stderr
            result = proc.stdout
            if proc.stderr:
                result += f"\n[stderr]\n{proc.stderr}"
            if proc.returncode != 0 and not result.strip():
                result = f"命令退出码非 0：{proc.returncode}"
            print(f"[结果] {result}")
            messages.append({"role": "user", "content": f"命令输出：\n{result}"})  # 16. 把结果反馈给 AI
        except json.JSONDecodeError as e:
            print(f"[解析失败] {e}\n原始回复：\n{reply}")
            messages.append({"role": "user", "content": "上一条不是合法 JSON，请只回一个 JSON，别的都不要"})
            continue
        except Exception as e:
            print(f"[错误] {e}")
            messages.append({"role": "user", "content": f"执行出错：{e}"})
            continue
# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
