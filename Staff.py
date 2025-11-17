import streamlit as st
import pandas as pd
import requests
import base64
from io import BytesIO
import plotly.express as px
from datetime import datetime

# 页面配置
st.set_page_config(page_title="设备状态监控台", layout="wide")
st.title("设备状态监控台（主管端）")

# ------------------------------------------------------
# GitHub 設定（來自 Secrets）
# ------------------------------------------------------
GIT_TOKEN = st.secrets["GIT_TOKEN"]
GIT_OWNER = st.secrets["GIT_OWNER"]
GIT_REPO = st.secrets["GIT_REPO"]
GIT_BRANCH = st.secrets.get("GIT_BRANCH", "main")

headers = {
    "Authorization": f"Bearer {GIT_TOKEN}",
    "Accept": "application/vnd.github+json"
}

RECORDS_PATH = "records.csv"
GH_URL = f"https://api.github.com/repos/{GIT_OWNER}/{GIT_REPO}/contents/{RECORDS_PATH}"

# ------------------------------------------------------
# 讀取 GitHub records.csv（如不存在則視為空）
# ------------------------------------------------------
def load_records():
    r = requests.get(GH_URL, headers=headers, params={"ref": GIT_BRANCH})

    if r.status_code == 200:
        data = r.json()
        sha = data["sha"]
        content = base64.b64decode(data["content"])
        df = pd.read_csv(BytesIO(content))
        return df, sha

    # 若無記錄則建立空白
    df_empty = pd.DataFrame(columns=["timestamp", "machine", "description"])
    return df_empty, None

df, current_sha = load_records()

# ------------------------------------------------------
# 管理員「清空全部記錄」功能
# ------------------------------------------------------
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
                    # 建立空 CSV
                    empty_df = pd.DataFrame(columns=["timestamp", "machine", "description"])
                    csv_bytes = empty_df.to_csv(index=False).encode("utf-8")
                    csv_b64 = base64.b64encode(csv_bytes).decode()

                    payload = {
                        "message": "Clear all records",
                        "content": csv_b64,
                        "branch": GIT_BRANCH
                    }

                    if current_sha:
                        payload["sha"] = current_sha

                    resp = requests.put(GH_URL, headers=headers, json=payload)
                    if resp.status_code in (200, 201):
                        st.success("数据库已清空！")
                        st.balloons()
                        st.session_state.show_clear_confirm = False
                        st.rerun()
                    else:
                        st.error("清空失败")
                else:
                    st.error("输入错误，未执行清空操作")


# ------------------------------------------------------
# 无数据提示
# ------------------------------------------------------
if df.empty:
    st.warning("暂无数据")
    st.stop()

# 确保格式正确
required_cols = {"machine", "description", "timestamp"}
missing = required_cols - set(df.columns)
if missing:
    st.error(f"records.csv 缺少必要字段：{missing}")
    st.stop()

# 转换 timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])

# ------------------------------------------------------
# 侧边栏筛选
# ------------------------------------------------------
st.sidebar.header("筛选条件")
view_mode = st.sidebar.radio("查看模式", ["全部设备", "个别设备"])

if view_mode == "个别设备":
    selected = st.sidebar.selectbox("选择设备", df["machine"].unique())
    df_filtered = df[df["machine"] == selected].copy()
else:
    machine_filter = st.sidebar.multiselect("选择设备",
                                            options=df["machine"].unique(),
                                            default=df["machine"].unique())
    state_filter = st.sidebar.multiselect("选择状态",
                                          options=df["description"].unique(),
                                          default=df["description"].unique())
    df_filtered = df[df["machine"].isin(machine_filter) &
                     df["description"].isin(state_filter)]

# ------------------------------------------------------
# 关键指标
# ------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("设备总数", df["machine"].nunique())

with col2:
    st.metric("运行中", (df_filtered["description"] == "running").sum())

with col3:
    st.metric("停机", (df_filtered["description"] == "stopped").sum())

with col4:
    st.metric("故障", (df_filtered["description"] == "error").sum())

# ------------------------------------------------------
# 状态分布饼图
# ------------------------------------------------------
st.subheader("设备状态分布")

fig_pie = px.pie(df_filtered, names="description", title="状态占比",
                 color_discrete_map={"running": "green",
                                     "stopped": "orange",
                                     "error": "red"})
st.plotly_chart(fig_pie, use_container_width=True)

# ------------------------------------------------------
# 时间序列折线图
# ------------------------------------------------------
st.subheader("状态变化趋势")

status_map = {"running": 1, "stopped": 0, "error": -1}
df_filtered["description_code"] = df_filtered["description"].map(status_map)

fig_line = px.line(df_filtered, x="timestamp", y="description_code",
                   color="machine", markers=True,
                   labels={"description_code": "状态", "timestamp": "时间"},
                   title="各设备状态随时间变化")

fig_line.update_yaxes(tickvals=[1, 0, -1],
                      ticktext=["运行", "停机", "故障"])

st.plotly_chart(fig_line, use_container_width=True)

# ------------------------------------------------------
# 历史记录时间点散点图
# ------------------------------------------------------
st.subheader("过去记录时间点分布")
fig_timeline = px.scatter(df_filtered, x="timestamp", y="machine",
                          color="description",
                          title="历史记录时间点",
                          color_discrete_map={"running": "green",
                                              "stopped": "orange",
                                              "error": "red"})
st.plotly_chart(fig_timeline, use_container_width=True)

# ------------------------------------------------------
# 最新状态表
# ------------------------------------------------------
st.subheader("最新状态一览")
latest = df_filtered.sort_values("timestamp", ascending=False).drop_duplicates("machine")
st.dataframe(latest.reset_index(drop=True)[["machine", "description", "timestamp"]])
