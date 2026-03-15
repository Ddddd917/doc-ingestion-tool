import os
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import streamlit as st

from core.metadata_store import (
    get_records_by_primary_domain,
    get_records_by_related_domain,
    update_record,
    delete_record,
)
from core.config import DOMAIN_COLORS, DOMAIN_FOLDERS, KNOWLEDGE_BASE_ROOT


def _render_record(r: dict, domain_name: str, icon_prefix: str = "📄"):
    """渲染单条文档卡片。"""
    fname = r.get("file_name", "未知")
    file_path = r.get("file_path", "")
    processed_date = r.get("processed_at", "")[:10]
    uid = str(abs(hash(file_path)))
    color = DOMAIN_COLORS.get(domain_name, "#888888")

    with st.expander(f"{icon_prefix} {fname} ｜ {processed_date}"):
        # 摘要
        st.markdown("**📝 摘要**")
        st.markdown(r.get("summary", "—"))

        # 关键要点
        st.markdown("**🎯 关键要点**")
        for point in r.get("key_points", []):
            st.markdown(f"- {point}")

        # 标签
        st.markdown("**🏷️ 标签**")
        tag_html = ""
        for tag in r.get("tags", []):
            tag_html += (
                f'<span style="background:{color};color:#fff;padding:2px 10px;'
                f'border-radius:12px;margin-right:6px;font-size:13px;">'
                f'{tag}</span>'
            )
        if tag_html:
            st.markdown(tag_html, unsafe_allow_html=True)

        # 文档信息
        st.markdown("**📊 文档信息**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("类型", r.get("document_type", "—"))
        c2.metric("语言", r.get("language", "—"))
        c3.metric("难度", r.get("difficulty_level", "—"))
        c4.metric("字数", f"{r.get('word_count', 0):,}")

        # 文件位置
        st.markdown("**📂 文件位置**")
        st.code(file_path, language=None)
        if st.button("在 Finder 中打开", key=f"open_{uid}"):
            try:
                subprocess.run(["open", "-R", file_path])
            except Exception as e:
                st.error(f"打开失败：{e}")

        # ---------- 文件管理 ----------
        with st.expander("⚙️ 文件管理", expanded=False):
            col_rename, col_move = st.columns(2)

            with col_rename:
                st.markdown("**✏️ 重命名**")
                new_name = st.text_input(
                    "文件名",
                    value=fname,
                    key=f"rename_{uid}",
                )
                if st.button("✏️ 确认重命名", key=f"rename_btn_{uid}"):
                    if new_name and new_name != fname:
                        old_path = Path(file_path)
                        new_path = old_path.parent / new_name
                        try:
                            os.rename(old_path, new_path)
                            update_record(file_path, {
                                "file_name": new_name,
                                "file_path": str(new_path),
                            })
                            st.success(f"已重命名为 {new_name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"重命名失败：{e}")
                    else:
                        st.warning("文件名未变更")

            with col_move:
                st.markdown("**📦 移动到其他知识域**")
                other_domains = [d for d in DOMAIN_FOLDERS if d != domain_name]
                target = st.selectbox(
                    "目标知识域",
                    other_domains,
                    key=f"move_{uid}",
                )
                if st.button("📦 确认移动", key=f"move_btn_{uid}"):
                    target_folder = DOMAIN_FOLDERS[target]
                    target_dir = KNOWLEDGE_BASE_ROOT / target_folder
                    target_dir.mkdir(parents=True, exist_ok=True)
                    new_path = target_dir / Path(file_path).name
                    try:
                        shutil.move(file_path, str(new_path))
                        updated_domains = r.get("domains", [])
                        if updated_domains:
                            updated_domains[0]["name"] = target
                        update_record(file_path, {
                            "file_path": str(new_path),
                            "domains": updated_domains,
                        })
                        st.success(f"已移动到 {target_folder}/")
                        st.rerun()
                    except Exception as e:
                        st.error(f"移动失败：{e}")

            st.divider()
            st.caption("⚠️ 删除后不可恢复")
            confirm = st.checkbox("我确认要删除此文档", key=f"del_confirm_{uid}")
            if confirm:
                if st.button("🗑️ 确认删除", key=f"del_btn_{uid}"):
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        delete_record(file_path)
                        st.success(f"已删除 {fname}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"删除失败：{e}")


def render_domain_page(domain_name: str, emoji: str):
    primary = get_records_by_primary_domain(domain_name)
    primary.sort(key=lambda r: r.get("processed_at", ""), reverse=True)

    related = get_records_by_related_domain(domain_name)
    related.sort(key=lambda r: r.get("processed_at", ""), reverse=True)

    # ---------- 区域1：标题和统计 ----------
    st.title(f"{emoji} {domain_name}")

    show_related = st.toggle("显示关联文档", value=False, key=f"show_related_{domain_name}")

    if show_related and related:
        st.caption(f"共 {len(primary) + len(related)} 篇文档（含 {len(related)} 篇关联文档）")
    else:
        st.caption(f"共 {len(primary)} 篇文档")

    # ---------- 区域2：文档列表 ----------
    if not primary and not (show_related and related):
        st.info("该知识域暂无文档，去「📤 上传与分析」页面添加吧")
        return

    # 主知识域文档
    if primary:
        if show_related:
            st.markdown(f"**📌 主知识域文档（{len(primary)} 篇）**")
        for r in primary:
            _render_record(r, domain_name, icon_prefix="📄")

    # 关联文档
    if show_related and related:
        st.markdown(f"**🔗 关联文档（{len(related)} 篇）**")
        st.caption("以下文档的主知识域不在本分类，但内容与本领域相关")
        for r in related:
            _render_record(r, domain_name, icon_prefix="🔗")

    # ---------- 区域3：标签云 ----------
    tag_source = primary + related if show_related else primary
    if not tag_source:
        return

    st.divider()
    st.markdown("**☁️ 标签云**")
    all_tags = []
    for r in tag_source:
        all_tags.extend(r.get("tags", []))

    if not all_tags:
        st.caption("暂无标签数据")
        return

    counter = Counter(all_tags)
    top_tags = counter.most_common(10)
    max_count = top_tags[0][1]

    cloud_html = ""
    for tag, count in top_tags:
        size = 14 + int(14 * count / max_count)
        color = DOMAIN_COLORS.get(domain_name, "#888888")
        cloud_html += (
            f'<span style="font-size:{size}px;color:{color};'
            f'margin-right:10px;font-weight:600;">{tag}</span>'
        )
    st.markdown(cloud_html, unsafe_allow_html=True)
