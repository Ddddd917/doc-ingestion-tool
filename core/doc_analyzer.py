import json
import re
from datetime import datetime

from core.llm_client import call_llm

SYSTEM_PROMPT = """你是一个知识管理专家。请分析以下文档内容，完成摘要提取、知识域分类和标签生成。
请严格返回JSON格式（不要包含markdown代码块标记、不要有任何额外文字）：
{
  "summary": "100字以内的核心摘要",
  "key_points": ["关键要点1", "关键要点2", "关键要点3"],
  "domains": [
    {"name": "知识域名称", "confidence": 0.95, "reason": "分类理由"}
  ],
  "tags": ["标签1", "标签2", "标签3"],
  "document_type": "笔记/报告/论文/文章/手册/其他",
  "language": "中文/英文/中英混合",
  "difficulty_level": "入门/中级/高级/专业"
}
知识域从以下8类中选择（可多选，按置信度从高到低排列）：
1. 学术知识（CS课程、算法、编程、学术项目）
2. 职业经验（实习、工作、行业洞察、职业发展）
3. AI与技术（AI工具、大模型、技术趋势、产品技术）
4. 阅读笔记（书籍、文章、论文的阅读记录）
5. 目标与计划（求职、学习计划、个人规划）
6. 思考与洞察（行业思考、产品灵感、复盘反思）
7. 生活记录（食谱、健身、理财、旅行、日常）
8. 影视与文化（电影、音乐、文化相关内容）
标签要求：3-8个，按重要性排序，要具体有辨识度（"RAG架构"优于"技术"），包含人名、公司名、专业术语等实体标签。"""

MAX_CONTENT_LENGTH = 8000


def _default_result(error_msg="解析失败"):
    return {
        "summary": error_msg,
        "key_points": [],
        "domains": [{"name": error_msg, "confidence": 0, "reason": error_msg}],
        "tags": [],
        "document_type": error_msg,
        "language": error_msg,
        "difficulty_level": error_msg,
    }


def _parse_llm_json(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = cleaned.strip().rstrip("`")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"[JSON 解析失败] {text[:200]}")
        return _default_result()


def analyze_document(doc: dict) -> dict:
    content = doc.get("content", "")

    if not content.strip():
        result = _default_result("文档内容为空，无法分析")
    else:
        if len(content) > MAX_CONTENT_LENGTH:
            content = content[:MAX_CONTENT_LENGTH]

        raw = call_llm(SYSTEM_PROMPT, content)
        result = _parse_llm_json(raw) if raw else _default_result("LLM 调用失败")

    result["file_name"] = doc.get("file_name", "")
    result["format"] = doc.get("format", "")
    result["word_count"] = doc.get("word_count", 0)
    result["processed_at"] = datetime.now().isoformat()
    return result
