from collections import Counter
from datetime import datetime, date, timedelta

import pandas as pd
import streamlit as st

from core.metadata_store import load_metadata
from core.config import DOMAIN_COLORS, DOMAIN_ICONS, DOMAIN_FOLDERS
from core.memory_manager import load_memory, generate_insights

st.title("📊 Dashboard")
st.caption("你的第二大脑，一目了然")

records = load_metadata()

# ========== 空状态 ==========
if not records:
    st.markdown("")
    st.markdown(
        "<h2 style='text-align:center;margin-top:80px;'>🚀 开始构建你的第二大脑</h2>"
        "<p style='text-align:center;color:gray;'>去「📤 上传与分析」页面上传你的第一个文档吧</p>",
        unsafe_allow_html=True,
    )
    st.stop()

# ========== 预处理 ==========
all_tags_flat = []
for r in records:
    all_tags_flat.extend(r.get("tags", []))
unique_tags = set(all_tags_flat)

# 每条记录的主知识域
primary_domains = []
for r in records:
    domains = r.get("domains", [])
    primary_domains.append(domains[0].get("name", "未知") if domains else "未知")

covered_domains = set(primary_domains)

# 时间解析
processed_dates = []
for r in records:
    try:
        processed_dates.append(datetime.fromisoformat(r["processed_at"]))
    except (KeyError, ValueError):
        pass

today = datetime.now()

if processed_dates:
    latest = max(processed_dates)
    days_ago = (today - latest).days
    if days_ago == 0:
        latest_text = "今天"
    elif days_ago == 1:
        latest_text = "昨天"
    else:
        latest_text = f"{days_ago}天前"
else:
    latest_text = "—"

# ========== 板块1：核心指标 ==========
m1, m2, m3, m4 = st.columns(4)
m1.metric("📚 总文档数", len(records))
m2.metric("🏷️ 总标签数", len(unique_tags))
m3.metric("📂 已覆盖知识域", f"{len(covered_domains)}/8")
m4.metric("📅 最近入库", latest_text)

st.divider()

# ========== 板块2：知识域分布 ==========
st.subheader("📂 知识域分布")

domain_names_ordered = list(DOMAIN_FOLDERS.keys())
domain_counts = Counter(primary_domains)

col_chart, col_list = st.columns([3, 2])

with col_chart:
    chart_data = pd.DataFrame({
        "知识域": [f"{DOMAIN_ICONS.get(d, '')} {d}" for d in domain_names_ordered],
        "文档数": [domain_counts.get(d, 0) for d in domain_names_ordered],
    })
    chart_data = chart_data.set_index("知识域")
    st.bar_chart(chart_data, color="#4A90D9")

with col_list:
    sorted_domains = sorted(domain_names_ordered, key=lambda d: domain_counts.get(d, 0), reverse=True)
    total = len(records)
    for d in sorted_domains:
        cnt = domain_counts.get(d, 0)
        pct = cnt / total * 100 if total else 0
        icon = DOMAIN_ICONS.get(d, "")
        color = DOMAIN_COLORS.get(d, "#888888")
        if cnt == 0:
            st.markdown(
                f'<span style="color:#aaa;">{icon} {d} &nbsp; 0 篇 (0%)</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'{icon} **{d}** &nbsp; '
                f'<span style="color:{color};font-weight:700;">{cnt} 篇</span>'
                f' ({pct:.0f}%)',
                unsafe_allow_html=True,
            )

st.divider()

# ========== 板块3：入库时间线（最近30天） ==========
st.subheader("📅 入库时间线")

today_date = date.today()
date_range = [today_date - timedelta(days=i) for i in range(29, -1, -1)]
date_counts = Counter(dt.date() for dt in processed_dates)

timeline_df = pd.DataFrame({
    "日期": date_range,
    "入库数": [date_counts.get(d, 0) for d in date_range],
})
timeline_df = timeline_df.set_index("日期")
st.area_chart(timeline_df, color="#4A90D9")

recent_7 = sum(date_counts.get(today_date - timedelta(days=i), 0) for i in range(7))
recent_30 = sum(date_counts.get(d, 0) for d in date_range)
st.caption(f"最近7天入库 {recent_7} 篇 | 最近30天入库 {recent_30} 篇")

st.divider()

# ========== 板块4：高频标签云（Top 20） ==========
st.subheader("☁️ 高频标签云")

if all_tags_flat:
    tag_counter = Counter(all_tags_flat)
    top_20 = tag_counter.most_common(20)
    max_count = top_20[0][1]

    # 确定每个标签的主知识域颜色（出现次数最多的域）
    tag_domain_counter: dict[str, Counter] = {}
    for r in records:
        domains = r.get("domains", [])
        pd_name = domains[0].get("name", "") if domains else ""
        for tag in r.get("tags", []):
            if tag not in tag_domain_counter:
                tag_domain_counter[tag] = Counter()
            tag_domain_counter[tag][pd_name] += 1

    cloud_html = ""
    for tag, count in top_20:
        size = 14 + int(22 * count / max_count)
        dominant_domain = tag_domain_counter.get(tag, Counter()).most_common(1)
        color = DOMAIN_COLORS.get(dominant_domain[0][0], "#888888") if dominant_domain else "#888888"
        cloud_html += (
            f'<span style="font-size:{size}px;color:{color};'
            f'margin-right:12px;font-weight:600;line-height:2;">{tag}</span>'
        )
    st.markdown(cloud_html, unsafe_allow_html=True)
else:
    st.caption("暂无标签数据")

st.divider()

# ========== 板块5：最近入库文档（最新5篇） ==========
st.subheader("🕐 最近入库")

sorted_records = sorted(records, key=lambda r: r.get("processed_at", ""), reverse=True)[:5]
for r in sorted_records:
    fname = r.get("file_name", "未知")
    domains = r.get("domains", [])
    pd_name = domains[0].get("name", "未知") if domains else "未知"
    color = DOMAIN_COLORS.get(pd_name, "#888888")
    domain_badge = (
        f'<span style="background:{color};color:#fff;padding:1px 8px;'
        f'border-radius:10px;font-size:12px;">{pd_name}</span>'
    )

    try:
        pt = datetime.fromisoformat(r["processed_at"])
        delta = (today - pt).days
        if delta == 0:
            time_text = "今天"
        elif delta == 1:
            time_text = "昨天"
        else:
            time_text = f"{delta}天前"
    except (KeyError, ValueError):
        time_text = "—"

    st.markdown(
        f"📄 **{fname}** &nbsp; {domain_badge} &nbsp; {time_text}",
        unsafe_allow_html=True,
    )

st.divider()

# ========== 板块6：AI 洞察 ==========
st.subheader("📡 AI 洞察")

memory = load_memory()
last_updated = memory.get("last_updated")

# 刷新按钮行
btn_col, info_col = st.columns([1, 3])
with btn_col:
    refresh_clicked = st.button("🔄 刷新洞察")
with info_col:
    if last_updated:
        try:
            updated_dt = datetime.fromisoformat(last_updated)
            delta_seconds = (today - updated_dt).total_seconds()
            if delta_seconds < 60:
                time_ago = "刚刚"
            elif delta_seconds < 3600:
                time_ago = f"{int(delta_seconds // 60)}分钟前"
            elif delta_seconds < 86400:
                time_ago = f"今天 {updated_dt.strftime('%H:%M')}"
            else:
                days = int(delta_seconds // 86400)
                time_ago = f"{days}天前"
        except (ValueError, TypeError):
            time_ago = "未知"
        st.caption(f"上次更新：{time_ago}")
    else:
        st.caption("尚未生成，点击刷新按钮生成第一份洞察")

# 刷新逻辑
if refresh_clicked:
    with st.spinner("正在分析你的知识库..."):
        try:
            memory = generate_insights(records)
            st.toast("📡 洞察已更新！")
            st.rerun()
        except Exception as e:
            st.error(f"洞察生成失败：{e}")

# 展示洞察内容（只要有数据就显示）
has_insights = memory.get("weekly_summary") or memory.get("recent_focus")
if has_insights:
    left_col, right_col = st.columns(2)

    with left_col:
        # 最近在忙什么
        st.markdown("**📝 最近在忙什么**")
        weekly_summary = memory.get("weekly_summary", "")
        if weekly_summary:
            st.markdown(weekly_summary)
        else:
            st.caption("暂无数据")

        # 近期重心
        st.markdown("**🎯 近期重心**")
        recent_focus = memory.get("recent_focus", [])
        if recent_focus:
            focus_html = ""
            focus_colors = ["#4A90D9", "#50C878", "#9B59B6", "#E67E22", "#E74C3C"]
            for i, focus in enumerate(recent_focus):
                c = focus_colors[i % len(focus_colors)]
                focus_html += (
                    f'<span style="background:{c};color:#fff;padding:3px 12px;'
                    f'border-radius:12px;margin:2px 4px;display:inline-block;'
                    f'font-size:14px;">{focus}</span>'
                )
            st.markdown(focus_html, unsafe_allow_html=True)
        else:
            st.caption("暂无数据")

        # 做得好的
        st.markdown("**✅ 做得好的**")
        strengths = memory.get("strengths", [])
        if strengths:
            for s in strengths:
                st.success(s)
        else:
            st.caption("暂无数据")

    with right_col:
        # 需要改进的
        st.markdown("**⚠️ 需要改进的**")
        improvements = memory.get("improvements", [])
        if improvements:
            for imp in improvements:
                st.warning(imp)
        else:
            st.caption("暂无数据")

        # 知识盲区
        st.markdown("**🕳️ 知识盲区**")
        knowledge_gaps = memory.get("knowledge_gaps", [])
        if knowledge_gaps:
            for gap in knowledge_gaps:
                st.info(gap)
        else:
            st.caption("暂无数据")

