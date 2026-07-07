# 对照真 Claude Code：这一步 = Read / Write / Bash 等专用工具（比全用 bash 更可控、可审计）
from dotenv import load_dotenv                                       # 1. 读取 .env 里的 API 密钥
from openai import OpenAI                                           # 2. 导入 OpenAI 兼容 SDK（DeepSeek API 与之兼容）
import os, json, sys, subprocess                                    # 3. os 执行命令；json 解析协议；subprocess 捕获 stderr

# 在 Windows 上强制使用 UTF-8 输出，避免中文乱码
if sys.platform == "win32":
    import io
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

# 用脚本所在目录的 .env，确保从任何位置运行都能读到
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_SCRIPT_DIR, ".env"))

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL    = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

for key in ["DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL"]:
    if not os.getenv(key):
        print(f"[错误] 环境变量 {key} 未设置，请检查 .env 文件"); sys.exit(1)

def read_file(path):  return open(path, encoding="utf-8").read()   # 4. 工具：读文件（真 Claude Code 的 Read）
def write_file(path, text):                                        # 5. 工具：写文件（真 Claude Code 的 Write）
    with open(path, "w", encoding="utf-8") as f: f.write(text)
    return f"已写入 {path}"
def bash(cmd):                                                     # 6. 工具：执行命令（真 Claude Code 的 Bash）
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
    out = proc.stdout
    if proc.stderr: out += f"\n[stderr]\n{proc.stderr}"
    if proc.returncode != 0 and not out.strip(): out = f"命令退出码非 0：{proc.returncode}"
    return out
def search(directory, keyword):                                    # 6b. 工具：项目内搜索（真 Claude Code 的 Grep）
    hits = []                                                      # 存放命中结果
    skip = {".git", "__pycache__", "node_modules", ".venv"}       # 跳过垃圾目录
    for root, dirs, files in os.walk(directory):                   # 递归遍历目录树
        dirs[:] = [d for d in dirs if d not in skip]              # 原地过滤，os.walk 后续不会进这些目录
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                for i, line in enumerate(open(fpath, encoding="utf-8", errors="ignore"), 1):
                    if keyword in line:
                        hits.append(f"{fpath}:{i}: {line.strip()}")
            except (PermissionError, OSError):                     # 二进制文件、权限问题等 → 跳过
                continue
    if not hits:
        return f"在 {directory} 里没找到包含「{keyword}」的内容"
    if len(hits) > 30:                                             # 截断：超过 30 条就只列前 20 + 总数提示
        return "\n".join(hits[:20]) + f"\n...共 {len(hits)} 条命中，只显示前 20 条"
    return "\n".join(hits)
TOOLS = {"read_file": read_file, "write_file": write_file, "bash": bash, "search": search}  # 7. 工具箱：名字 → 函数
def parse(s):                                                      # 7b. 容错解析：模型偶尔会用 ```json 包裹（这就是 c0 有时崩的原因），剥掉再解析
    s = s.strip().strip("`").removeprefix("json").strip()
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("回复里没有找到合法 JSON 对象")
    return json.loads(s[start:end + 1])

# 关键：明确告诉模型——你运行在本地 Windows，命令由 Python 脚本执行
SYSTEM = """你是一个编程助手 Agent，运行在用户的本地 Windows 机器上。
你不需要自己去访问文件或执行命令——你只负责输出 JSON，Python 脚本会在本地帮你执行并返回结果。
每次只回复一个 JSON，不要有别的文字，不要 markdown 包裹；字符串值里别用英文双引号，要引用就用「」：
- 读文件：{"tool": "read_file", "args": {"path": "..."}}
- 写文件：{"tool": "write_file", "args": {"path": "...", "text": "..."}}
- 执行命令：{"tool": "bash", "args": {"cmd": "..."}}
- 搜索代码：{"tool": "search", "args": {"directory": "...", "keyword": "..."}}
- 完成时：{"done": "总结"}
优先用 read_file / write_file 处理文件，它们比 bash 更安全可控。
优先用 search 搜索代码位置，比 bash grep 更可靠。
不要说「我无法访问」「环境不在本地」——你指定工具调用，脚本会帮你执行。"""  # 8. 系统提示：告诉模型有哪些工具、何时用

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)                # 9. 创建 DeepSeek 客户端
messages = [{"role": "system", "content": SYSTEM}]                  # 10. 对话历史
while True:                                                          # 11. 外层循环：等新任务
    messages.append({"role": "user", "content": input("\n你：")})
    while True:                                                      # 12. 内层循环：自主执行
        reply = client.chat.completions.create(
            model=MODEL,
            messages=messages).choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        try:                              # 13. 解析 JSON
            action = parse(reply)
        except Exception:                              # 坏格式不崩：请模型重发（这就是加固）
            messages.append({"role": "user", "content": "上一条不是合法 JSON，请只回一个 JSON，别的都不要"}); continue
        if "done" in action:                                    # 14. 完成 → 跳出
            print(f"[完成] {action['done']}"); break
        name, args = action["tool"], action["args"]            # 15. 取出工具名和参数
        print(f"[调用] {name}({args})")
        result = TOOLS[name](**args)                            # 16. 关键升级：按名字派发到对应工具函数
        print(f"[结果] {result}")
        messages.append({"role": "user", "content": f"工具返回：\n{result}"})  # 17. 结果反馈
# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
