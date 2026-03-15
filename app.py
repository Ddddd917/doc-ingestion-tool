import streamlit as st
from core.config import ensure_knowledge_base

st.set_page_config(page_title="第二大脑 · 文档智能入库", page_icon="📚", layout="wide")

# 启动时确保知识库目录存在
ensure_knowledge_base()

# ---------- 定义多页导航 ----------
pages = [
    st.Page("pages/dashboard.py", title="Dashboard",  icon="📊", default=True),
    st.Page("pages/upload.py",    title="上传与分析", icon="📤"),
    st.Page("pages/academic.py",  title="学术知识",   icon="🎓"),
    st.Page("pages/career.py",    title="职业经验",   icon="💼"),
    st.Page("pages/ai_tech.py",   title="AI与技术",   icon="🤖"),
    st.Page("pages/reading.py",   title="阅读笔记",   icon="📖"),
    st.Page("pages/goals.py",     title="目标与计划", icon="🎯"),
    st.Page("pages/insights.py",  title="思考与洞察", icon="💭"),
    st.Page("pages/life.py",      title="生活记录",   icon="🍳"),
    st.Page("pages/culture.py",   title="影视与文化", icon="🎬"),
]

pg = st.navigation(pages)

# ---------- 侧边栏 ----------
with st.sidebar:
    st.markdown("## 📚 第二大脑")
    st.divider()
    # 统计信息放在底部
    from core.metadata_store import load_metadata
    total_docs = len(load_metadata())
    st.caption(f"已入库 {total_docs} 篇文档")

pg.run()
