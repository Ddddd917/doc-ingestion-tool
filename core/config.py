import os
from pathlib import Path

KNOWLEDGE_BASE_ROOT = Path.home() / "Documents" / "SecondBrain"

DOMAIN_FOLDERS = {
    "学术知识": "01_学术知识",
    "职业经验": "02_职业经验",
    "AI与技术": "03_AI与技术",
    "阅读笔记": "04_阅读笔记",
    "目标与计划": "05_目标与计划",
    "思考与洞察": "06_思考与洞察",
    "生活记录": "07_生活记录",
    "影视与文化": "08_影视与文化",
}

DOMAIN_ABBREV = {
    "学术知识": "学术",
    "职业经验": "职业",
    "AI与技术": "AI",
    "阅读笔记": "阅读",
    "目标与计划": "目标",
    "思考与洞察": "思考",
    "生活记录": "生活",
    "影视与文化": "影视",
}

DOMAIN_COLORS = {
    "学术知识": "#4A90D9",
    "职业经验": "#50C878",
    "AI与技术": "#9B59B6",
    "阅读笔记": "#E67E22",
    "目标与计划": "#E74C3C",
    "思考与洞察": "#1ABC9C",
    "生活记录": "#FF69B4",
    "影视与文化": "#F1C40F",
}

DOMAIN_ICONS = {
    "学术知识": "🎓",
    "职业经验": "💼",
    "AI与技术": "🤖",
    "阅读笔记": "📖",
    "目标与计划": "🎯",
    "思考与洞察": "💭",
    "生活记录": "🍳",
    "影视与文化": "🎬",
}


def ensure_knowledge_base():
    """创建知识库根目录和所有子文件夹（如果不存在）。"""
    KNOWLEDGE_BASE_ROOT.mkdir(parents=True, exist_ok=True)
    for folder in DOMAIN_FOLDERS.values():
        (KNOWLEDGE_BASE_ROOT / folder).mkdir(exist_ok=True)
