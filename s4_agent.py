# s4_agent.py —— 把规则放进 md
# 目标：系统提示词不再写死在代码里，而是从 agent.md 读取。其它循环逻辑与 s3 基本一致。

from openai import OpenAI
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# 在 Windows 上强制使用 UTF-8 输出，避免中文乱码
if sys.platform == "win32":
    import io
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    if sys.stderr.encoding.lower() != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

api_key = os.getenv("KIMI_API_KEY")
base_url = os.getenv("KIMI_BASE_URL", "https://api.kimi.com/coding/v1")
model = os.getenv("KIMI_MODEL", "kimi-for-coding")

if not api_key or api_key.startswith("sk-请"):
    print("错误：请先在 .env 文件里填写有效的 KIMI_API_KEY")
    sys.exit(1)

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# 从外部 markdown 文件加载系统提示词，改能力时先改文档
with open("agent.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# 只在真正的终端里启用 ANSI 颜色；管道或 IDE 内置终端不启用，避免乱码
_USE_COLOR = sys.stdout.isatty()
C_USER = "\033[94m" if _USE_COLOR else ""
C_AI = "\033[92m" if _USE_COLOR else ""
C_SYSTEM = "\033[93m" if _USE_COLOR else ""
C_COMMAND = "\033[96m" if _USE_COLOR else ""
C_RESET = "\033[0m" if _USE_COLOR else ""


def run_agent_turn(messages, user_input, on_ai_reply=None, on_system=None):
    """执行一轮 Agent 自主循环。返回 (updated_messages, final_reply)。"""
    messages = messages + [{"role": "user", "content": user_input}]

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})

        if on_ai_reply:
            on_ai_reply(reply)

        stripped = reply.strip()
        if stripped.startswith("完成:"):
            return messages, reply

        # 容错：如果模型没按格式输出，直接返回让用户看到
        if "命令:" not in stripped:
            return messages, reply

        command = stripped.split("命令:", 1)[1].strip()
        if on_system:
            on_system(f"$ {command}")

        try:
            result = os.popen(command).read()
        except Exception as e:
            result = f"执行出错: {e}"

        if on_system:
            on_system(result)

        messages.append({"role": "user", "content": f"执行完毕:{result}"})


def create_messages():
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def print_message(role, text):
    """在终端里漂亮地打印一条消息。"""
    if role == "你":
        prefix = f"{C_USER}【你】{C_RESET}"
    elif role == "AI":
        prefix = f"{C_AI}【AI】{C_RESET}"
    elif role == "命令":
        prefix = f"{C_COMMAND}【执行命令】{C_RESET}"
    else:
        prefix = f"{C_SYSTEM}【{role}】{C_RESET}"
    print(f"{prefix}\n{text}\n")


def terminal_chat():
    """直接在终端里进行多轮对话。"""
    messages = create_messages()
    print_message("系统", "已连接 Kimi。输入消息直接对话，输入 /new 开启新对话，/quit 退出。")

    while True:
        try:
            user_input = input(f"{C_USER}你：{C_RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in ("/quit", "/exit", "退出"):
            break
        if user_input.lower() == "/new":
            messages = create_messages()
            print_message("系统", "已开启新对话。")
            continue

        def ai_callback(reply):
            if reply.strip().startswith("命令:"):
                command = reply.strip().split("命令:", 1)[1].strip()
                print_message("命令", command)
            else:
                print_message("AI", reply)

        def sys_callback(result):
            print_message("系统", result)

        try:
            messages, final = run_agent_turn(
                messages, user_input, on_ai_reply=ai_callback, on_system=sys_callback
            )
        except Exception as e:
            print_message("系统", f"请求失败: {e}")

    print_message("系统", "再见！")


if __name__ == "__main__":
    terminal_chat()
