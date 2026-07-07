# s1_agent.py —— 单轮聊天
# 目标：用户输入一次，模型回答一次。没有历史，记不住上下文。

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

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

system_prompt = "你是一个乐于助人的助手。"

user_input = input("你：").strip()

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_input}
]

response = client.chat.completions.create(
    model=model,
    messages=messages
)

reply = response.choices[0].message.content
print(f"AI：{reply}")
