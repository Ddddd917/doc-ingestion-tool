import os
import re
from datetime import date
from pathlib import Path

from core.config import KNOWLEDGE_BASE_ROOT, DOMAIN_FOLDERS, DOMAIN_ABBREV


_DOC_TYPE_MAP = {
    "笔记": "笔记",
    "报告": "报告",
    "论文": "论文",
    "文章": "文章",
    "手册": "手册",
    "其他": "文档",
}

_SPECIAL_TYPE_KEYWORDS = [
    "面试复盘", "面试准备", "复盘", "准备材料",
    "学习笔记", "调研报告", "竞品分析",
]


def suggest_filename(analysis_result: dict) -> str:
    today = date.today().strftime("%Y%m%d")

    domains = analysis_result.get("domains", [])
    primary_domain = domains[0].get("name", "") if domains else ""
    abbrev = DOMAIN_ABBREV.get(primary_domain, "其他")

    tags = list(analysis_result.get("tags", []))

    # 检查 tags 中是否包含特殊文档类型关键词
    doc_type_override = None
    for kw in _SPECIAL_TYPE_KEYWORDS:
        for tag in tags:
            if kw in tag:
                doc_type_override = kw
                tags.remove(tag)
                break
        if doc_type_override:
            break

    # 主题：剩余 tags 前 2 个
    topic_parts = [re.sub(r"[^\w\u4e00-\u9fff]", "", t) for t in tags[:2]]
    topic = "_".join(p for p in topic_parts if p) or "未命名"

    # 文档类型
    if doc_type_override:
        doc_type = doc_type_override
    else:
        raw_type = analysis_result.get("document_type", "")
        doc_type = _DOC_TYPE_MAP.get(raw_type, "文档")

    ext = analysis_result.get("format", "txt")
    return f"{today}_{abbrev}_{topic}_{doc_type}.{ext}"


def move_and_rename(
    source_file_bytes: bytes,
    original_name: str,
    new_name: str,
    target_domain: str,
) -> str:
    folder_name = DOMAIN_FOLDERS.get(target_domain)
    if not folder_name:
        folder_name = "01_学术知识"
    target_dir = KNOWLEDGE_BASE_ROOT / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / new_name

    # 重名处理
    if target_path.exists():
        stem = target_path.stem
        suffix = target_path.suffix
        counter = 1
        while target_path.exists():
            target_path = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    target_path.write_bytes(source_file_bytes)
    return str(target_path)
