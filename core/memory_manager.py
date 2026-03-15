import json
import re
from datetime import datetime
from pathlib import Path

from core.config import KNOWLEDGE_BASE_ROOT
from core.llm_client import call_llm

MEMORY_PATH = KNOWLEDGE_BASE_ROOT / "memory.json"

_DEFAULT_MEMORY = {
    "last_updated": None,
    "weekly_summary": "",
    "recent_focus": [],
    "strengths": [],
    "improvements": [],
    "knowledge_gaps": [],
}

SYSTEM_PROMPT = """\
你是一个个人成长分析师。基于用户知识库中的文档元数据，生成洞察分析。
请严格返回JSON格式（不要包含markdown代码块标记）：
{
  "weekly_summary": "一段话总结用户最近在忙什么（100字以内）",
  "recent_focus": ["最近的3-5个工作/学习重心"],
  "strengths": ["从文档内容中识别出的3-5个做得好的地方，要具体"],
  "improvements": ["从文档内容中识别出的3-5个需要改进的地方，要具体可执行"],
  "knowledge_gaps": ["知识库中明显缺失或薄弱的领域，给出2-3个建议补充的方向"]
}
注意：
- strengths 和 improvements 要基于文档内容给出具体的、可执行的反馈，不要泛泛而谈
- knowledge_gaps 对比8个知识域（学术知识、职业经验、AI与技术、阅读笔记、目标与计划、思考与洞察、生活记录、影视与文化），指出哪些域内容稀少或空白
"""


def load_memory() -> dict:
    """读取 memory.json，文件不存在则返回默认结构。"""
    if not MEMORY_PATH.exists():
        return dict(_DEFAULT_MEMORY)
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_MEMORY)


def save_memory(memory: dict):
    """写入 memory.json。"""
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def _build_user_message(metadata: list[dict]) -> str:
    """将文档元数据拼接为用户消息，控制在 6000 字以内。"""
    # 按时间倒序，超出则只取最近 20 篇
    sorted_meta = sorted(metadata, key=lambda r: r.get("processed_at", ""), reverse=True)
    if len(sorted_meta) > 20:
        sorted_meta = sorted_meta[:20]

    all_domains = set()
    for r in metadata:
        for d in r.get("domains", []):
            all_domains.add(d.get("name", ""))

    lines = [
        f"以下是用户知识库的文档概要：",
        f"共 {len(metadata)} 篇文档，覆盖知识域：{', '.join(sorted(all_domains))}",
        "文档清单：",
    ]

    for i, r in enumerate(sorted_meta, 1):
        domains = r.get("domains", [])
        domain_name = domains[0].get("name", "未知") if domains else "未知"
        tags = ", ".join(r.get("tags", []))
        summary = r.get("summary", "")
        key_points = "; ".join(r.get("key_points", []))
        line = (
            f"{i}. {r.get('file_name', '未知')} | "
            f"知识域：{domain_name} | "
            f"标签：{tags} | "
            f"摘要：{summary} | "
            f"关键要点：{key_points}"
        )
        lines.append(line)

    text = "\n".join(lines)
    # 控制在 6000 字以内
    if len(text) > 6000:
        text = text[:6000]
    return text


def _parse_llm_json(raw: str) -> dict | None:
    """解析 LLM 返回的 JSON，兼容 markdown 代码块包裹。"""
    if not raw:
        return None
    # 去掉可能的 ```json ... ``` 包裹
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def generate_insights(metadata: list[dict]) -> dict:
    """基于文档元数据调用 LLM 生成洞察，保存并返回完整 memory。"""
    if not metadata:
        memory = dict(_DEFAULT_MEMORY)
        save_memory(memory)
        return memory

    user_message = _build_user_message(metadata)
    raw = call_llm(SYSTEM_PROMPT, user_message, temperature=0.4)

    parsed = _parse_llm_json(raw)
    if parsed is None:
        # 解析失败，保留旧 memory 或返回默认
        memory = load_memory()
        memory["last_updated"] = datetime.now().isoformat()
        save_memory(memory)
        return memory

    memory = {
        "last_updated": datetime.now().isoformat(),
        "weekly_summary": parsed.get("weekly_summary", ""),
        "recent_focus": parsed.get("recent_focus", []),
        "strengths": parsed.get("strengths", []),
        "improvements": parsed.get("improvements", []),
        "knowledge_gaps": parsed.get("knowledge_gaps", []),
    }
    save_memory(memory)
    return memory
