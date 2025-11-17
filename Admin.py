import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

# 页面配置
st.set_page_config(page_title="设备状态监控台", layout="wide")
st.title("设备状态监控台")

# 连接数据库
db_path = os.path.join(os.path.dirname(__file__), "records.db")
conn = sqlite3.connect(db_path)
conn.execute("CREATE TABLE IF NOT EXISTS records (timestamp TEXT, machine TEXT, description TEXT)")
conn.commit()

# 新增：管理员清空数据库功能
# 使用 session_state 控制弹窗，避免按钮点击后状态丢失
if "show_clear_confirm" not in st.session_state:
    st.session_state.show_clear_confirm = False

if st.sidebar.button("⚠️ 清空全部记录"):
    st.session_state.show_clear_confirm = True

if st.session_state.show_clear_confirm:
    with st.sidebar:
        with st.form("confirm_clear"):
            st.warning("此操作将永久删除所有记录，不可恢复！")
            confirm = st.text_input("请输入“确认清空”以继续")
            submitted = st.form_submit_button("确定")
            if submitted:
                if confirm.strip() == "确认清空":
                    try:
                        conn.execute("DELETE FROM records")
                        conn.commit()
                        st.success("数据库已清空！")
                        st.balloons()
                        # 清空后关闭确认框
                        st.session_state.show_clear_confirm = False
                        # 刷新页面以立即反映变化
                        st.rerun()
                    except Exception as e:
                        st.error(f"删除失败：{e}")
                else:
                    st.error("输入错误，未执行清空操作")

query = "SELECT * FROM records ORDER BY timestamp DESC"
df = pd.read_sql_query(query, conn)
conn.close()

# 检查必需列是否存在
required_cols = {"machine", "description", "timestamp"}
missing_cols = required_cols - set(df.columns)
if missing_cols:
    st.error(f"数据库缺少必要字段：{', '.join(missing_cols)}")
    st.stop()

if df.empty:
    st.warning("暂无数据")
    st.stop()

# 侧边栏筛选
st.sidebar.header("筛选条件")
# 新增：选择查看全部或个别机器
view_mode = st.sidebar.radio("查看模式", ["全部设备", "个别设备"])
if view_mode == "个别设备":
    selected_machine = st.sidebar.selectbox("选择设备", options=df["machine"].unique())
    df_filtered = df[df["machine"] == selected_machine].copy()
else:
    machine_filter = st.sidebar.multiselect("选择设备", options=df["machine"].unique(),
                                            default=df["machine"].unique())
    description_filter = st.sidebar.multiselect("选择状态", options=df["description"].unique(),
                                           default=df["description"].unique())
    df_filtered = df[(df["machine"].isin(machine_filter)) &
                     (df["description"].isin(description_filter))]

# 关键指标
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("设备总数", df["machine"].nunique())
with col2:
    st.metric("运行中", (df_filtered["description"] == "running").sum())
with col3:
    st.metric("停机", (df_filtered["description"] == "stopped").sum())
with col4:
    st.metric("故障", (df_filtered["description"] == "error").sum())

# 状态分布饼图
st.subheader("设备状态分布")
fig_pie = px.pie(df_filtered, names="description", title="状态占比",
                 color_discrete_map={"running": "green",
                                    "stopped": "orange",
                                    "error": "red"})
st.plotly_chart(fig_pie, use_container_width=True)

# 时间序列折线图
st.subheader("状态变化趋势")
df["timestamp"] = pd.to_datetime(df["timestamp"])
status_map = {"running": 1, "stopped": 0, "error": -1}
# 确保 df_filtered 也包含 description_code
df_filtered["description_code"] = df_filtered["description"].map(status_map)
fig_line = px.line(df_filtered, x="timestamp", y="description_code",
                  color="machine", markers=True,
                  labels={"description_code": "状态", "timestamp": "时间"},
                  title="各设备状态随时间变化")
fig_line.update_yaxes(tickvals=[1, 0, -1],
                     ticktext=["运行", "停机", "故障"])
st.plotly_chart(fig_line, use_container_width=True)

# 新增：过去时间点记录图
st.subheader("过去记录时间点分布")
# 使用散点图展示每条记录的时间点
fig_timeline = px.scatter(df_filtered, x="timestamp", y="machine", color="description",
                         title="历史记录时间点",
                         labels={"timestamp": "时间", "machine": "设备"},
                         color_discrete_map={"running": "green", "stopped": "orange", "error": "red"})
fig_timeline.update_layout(height=400)
st.plotly_chart(fig_timeline, use_container_width=True)

# 实时状态表
st.subheader("最新状态一览")
latest = df_filtered.drop_duplicates(subset=["machine"], keep="first")
st.dataframe(latest[["machine", "description", "timestamp"]].reset_index(drop=True))
