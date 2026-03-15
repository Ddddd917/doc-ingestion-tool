import os
from dotenv import load_dotenv
from zhipuai import ZhipuAI

load_dotenv()

MODEL = "glm-4-flashx"

_api_key = os.getenv("ZHIPU_API_KEY")
if not _api_key:
    raise RuntimeError("未找到 ZHIPU_API_KEY，请在项目根目录 .env 文件中配置")

_client = ZhipuAI(api_key=_api_key)


def call_llm(system_prompt: str, user_message: str, temperature: float = 0.3) -> str:
    try:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            timeout=60,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[LLM 调用失败] {e}")
        return ""
