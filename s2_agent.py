# s2_agent.py —— 多轮 + 记忆
# 目标：messages 变成对话历史，可以追问，上下文一直在。

from openai import OpenAI
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# 在 Windows 上强制 UTF-8，避免中文乱码
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
    raise SystemExit(1)

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

messages = [{"role": "system", "content": "你是一个乐于助人的助手。"}]

print("已开启多轮对话，输入 /quit 或 /new 退出或开新对话。")

while True:
    user_input = input("\n你：").strip()
    if not user_input:
        continue
    if user_input.lower() in ("/quit", "/exit", "退出"):
        break
    if user_input.lower() == "/new":
        messages = [{"role": "system", "content": "你是一个乐于助人的助手。"}]
        print("已开启新对话。")
        continue

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    reply = response.choices[0].message.content
    print(f"AI：{reply}")

    messages.append({"role": "assistant", "content": reply})

print("再见！")
