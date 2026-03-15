import streamlit as st
from core.doc_parser import parse_file
from core.doc_analyzer import analyze_document
from core.file_manager import suggest_filename, move_and_rename
from core.metadata_store import add_record, load_metadata
from core.memory_manager import load_memory, generate_insights
from core.config import DOMAIN_FOLDERS, DOMAIN_COLORS

st.title("📤 上传与分析")
st.caption("将散乱文档自动转化为结构化知识条目，为你的第二大脑提供标准化入库流程")

# ---------- 文档上传 ----------
uploaded_files = st.file_uploader(
    "上传文档",
    type=["pdf", "md", "txt"],
    accept_multiple_files=True,
)

FORMAT_ICONS = {"pdf": "📕", "md": "📘", "txt": "📄"}

if uploaded_files:
    cols = st.columns(min(len(uploaded_files), 4))
    for i, f in enumerate(uploaded_files):
        ext = f.name.rsplit(".", 1)[-1].lower()
        icon = FORMAT_ICONS.get(ext, "📄")
        with cols[i % len(cols)]:
            st.markdown(f"{icon} **{f.name}**  \n{f.size / 1024:.1f} KB")

    start = st.button("🚀 开始处理")
else:
    start = False

# ---------- 处理过程 ----------
if start and uploaded_files:
    results = []
    file_bytes_map = {}
    progress = st.progress(0, text="准备中…")
    total = len(uploaded_files)

    for idx, f in enumerate(uploaded_files):
        with st.status(f"正在处理：{f.name}", expanded=True) as status:
            st.write("📖 解析文档…")
            doc = parse_file(f)

            st.write("🤖 AI 分析中…")
            result = analyze_document(doc)
            results.append(result)

            # 保存原始字节，供入库使用
            f.seek(0)
            file_bytes_map[f.name] = f.read()

            status.update(label=f"✅ {f.name} 处理完成", state="complete", expanded=False)

        progress.progress((idx + 1) / total, text=f"已处理 {idx + 1}/{total}")

    st.session_state["results"] = results
    st.session_state["file_bytes"] = file_bytes_map
    st.success(f"全部处理完成！共 {total} 个文档。")

# ---------- 结果展示 ----------
if "results" in st.session_state:
    results = st.session_state["results"]
    file_bytes_map = st.session_state.get("file_bytes", {})
    domain_names = list(DOMAIN_FOLDERS.keys())

    st.divider()
    st.subheader("📋 分析结果")

    for i, r in enumerate(results):
        primary_domain = (
            r.get("domains", [{}])[0].get("name", "未知")
            if r.get("domains") else "未知"
        )
        fname = r["file_name"]
        with st.expander(f"📄 {fname} ｜ {primary_domain}", expanded=(i == 0)):

            # 摘要
            st.markdown("**📝 摘要**")
            st.text_area(
                "摘要内容",
                value=r.get("summary", ""),
                key=f"summary_{fname}",
                label_visibility="collapsed",
            )

            # 关键要点
            st.markdown("**🎯 关键要点**")
            for point in r.get("key_points", []):
                st.markdown(f"- {point}")

            # 知识域
            st.markdown("**📚 知识域**")
            domain_html_parts = []
            for d in r.get("domains", []):
                name = d.get("name", "未知")
                confidence = d.get("confidence", 0)
                color = DOMAIN_COLORS.get(name, "#888888")
                domain_html_parts.append(
                    f'<span style="background:{color};color:#fff;padding:2px 10px;'
                    f'border-radius:12px;margin-right:8px;font-size:14px;">'
                    f'{name} {confidence:.0%}</span>'
                )
            st.markdown("".join(domain_html_parts), unsafe_allow_html=True)

            # 标签
            st.markdown("**🏷️ 标签**")
            st.text_input(
                "编辑标签（逗号分隔）",
                value=", ".join(r.get("tags", [])),
                key=f"tags_{fname}",
                label_visibility="collapsed",
            )

            # 文档信息
            st.markdown("**📊 文档信息**")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("类型", r.get("document_type", "—"))
            c2.metric("语言", r.get("language", "—"))
            c3.metric("难度", r.get("difficulty_level", "—"))
            c4.metric("字数", f"{r.get('word_count', 0):,}")

            # ---------- 入库操作 ----------
            st.divider()
            st.markdown("**📂 入库操作**")

            suggested = suggest_filename(r)
            new_name = st.text_input(
                "建议文件名",
                value=suggested,
                key=f"newname_{fname}",
            )

            default_idx = (
                domain_names.index(primary_domain)
                if primary_domain in domain_names else 0
            )
            target_domain = st.selectbox(
                "目标知识域",
                domain_names,
                index=default_idx,
                key=f"domain_{fname}",
            )

            ingest_key = f"ingested_{fname}"
            if st.button("✅ 确认入库", key=f"ingest_{fname}"):
                raw_bytes = file_bytes_map.get(fname, b"")
                if not raw_bytes:
                    st.error("找不到原始文件数据，请重新上传并处理。")
                else:
                    saved_path = move_and_rename(raw_bytes, fname, new_name, target_domain)
                    record = {
                        "file_name": new_name,
                        "original_name": fname,
                        "summary": st.session_state.get(f"summary_{fname}", r.get("summary", "")),
                        "key_points": r.get("key_points", []),
                        "domains": r.get("domains", []),
                        "tags": [
                            t.strip()
                            for t in st.session_state.get(f"tags_{fname}", "").split(",")
                            if t.strip()
                        ],
                        "document_type": r.get("document_type", ""),
                        "language": r.get("language", ""),
                        "difficulty_level": r.get("difficulty_level", ""),
                        "word_count": r.get("word_count", 0),
                        "processed_at": r.get("processed_at", ""),
                        "file_path": saved_path,
                    }
                    add_record(record)
                    folder = DOMAIN_FOLDERS.get(target_domain, target_domain)
                    st.success(f"已入库到 {folder}/{new_name}")

                    # 如果已有洞察，自动更新
                    _memory = load_memory()
                    if _memory.get("last_updated") is not None:
                        try:
                            generate_insights(load_metadata())
                            st.toast("📡 知识库洞察已更新")
                        except Exception:
                            pass

    # ---------- 统计与导出占位 ----------
    st.divider()
    all_domains = set()
    all_tags = []
    for r in results:
        for d in r.get("domains", []):
            all_domains.add(d.get("name", ""))
        all_tags.extend(r.get("tags", []))

    st.markdown(
        f"✅ 共处理 **{len(results)}** 个文档 ｜ "
        f"📚 覆盖 **{len(all_domains)}** 个知识域 ｜ "
        f"🏷️ 生成 **{len(all_tags)}** 个标签"
    )

    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        st.button("📥 导出 JSON", disabled=True, help="功能开发中")
    with ec2:
        st.button("📥 导出 CSV", disabled=True, help="功能开发中")
    with ec3:
        st.button("📥 导出 Markdown", disabled=True, help="功能开发中")
