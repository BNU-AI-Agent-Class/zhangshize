# s0_agent.py —— 最小 API 骨架
# 目标：只验证"环境能跑"，向模型发一次固定请求并打印回复。

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

response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "你好，请用一句话证明你在线。"}]
)

print(response.choices[0].message.content)
