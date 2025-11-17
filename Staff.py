import streamlit as st
import pandas as pd
import requests
import base64
from io import BytesIO
from datetime import datetime

st.title("🔧 设备状态记录（员工端）")
clean_streamlit_ui = """
<style>

    /* --- 隱藏右上角所有 Streamlit Cloud 相關按鈕 --- */
    [data-testid="stAppToolbar"] {display: none !important;}
    header {visibility: hidden !important;}
    button[title="Manage the app"] {display: none !important;}
    button[title="Deploy this app"] {display: none !important;}
    button[title="Settings"] {display: none !important;}

    /* --- 隱藏右下角所有浮動元素：Manage App / Cloud Badge / 控制面板 --- */
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stBadge"] {display: none !important;}

    /* --- 你要求的第二種最爆裂版本：隱藏所有 iframe --- */
    iframe {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        height: 0 !important;
        width: 0 !important;
    }

</style>
"""

st.markdown(clean_streamlit_ui, unsafe_allow_html=True)



# ------------------------------------------------------
# GitHub Secrets
# ------------------------------------------------------
GIT_TOKEN = st.secrets["GIT_TOKEN"]
GIT_OWNER = st.secrets["GIT_OWNER"]
GIT_REPO = st.secrets["GIT_REPO"]
GIT_BRANCH = st.secrets.get("GIT_BRANCH", "main")

headers = {
    "Authorization": f"Bearer {GIT_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ------------------------------------------------------
# 讀 machines.xlsx（用於選單）
# ------------------------------------------------------
def load_excel_from_github(path):
    url = f"https://api.github.com/repos/{GIT_OWNER}/{GIT_REPO}/contents/{path}"
    r = requests.get(url, headers=headers, params={"ref": GIT_BRANCH})
    if r.status_code != 200:
        st.error("❌ 無法讀取 machines.xlsx，請確認檔案存在於 repo 根目錄。")
        st.stop()
    data = r.json()
    b = base64.b64decode(data["content"])
    return pd.read_excel(BytesIO(b))

df_machines = load_excel_from_github("machines.xlsx")
machine_list = df_machines["Machines"].dropna().tolist()

machine = st.selectbox("请选择设备", machine_list)
description = st.text_input("编号 / 情况描述")

# ------------------------------------------------------
# 讀 records.csv（如無則建立空 DataFrame）
# ------------------------------------------------------
def load_records():
    url = f"https://api.github.com/repos/{GIT_OWNER}/{GIT_REPO}/contents/records.csv"
    r = requests.get(url, headers=headers, params={"ref": GIT_BRANCH})

    if r.status_code == 200:
        json_data = r.json()
        sha = json_data["sha"]
        content = base64.b64decode(json_data["content"])
        df = pd.read_csv(BytesIO(content), encoding="utf-8")
        return df, sha
    else:
        # 初次使用：建立空白
        empty_df = pd.DataFrame(columns=["timestamp", "machine", "description"])
        return empty_df, None

records_df, records_sha = load_records()

# ------------------------------------------------------
# 按下「新增記錄」 → append → push 回 GitHub
# ------------------------------------------------------
if st.button("记录当前状态"):
    if description.strip() == "":
        st.error("⚠ 请填写描述")
        st.stop()

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    new_row = pd.DataFrame([{
        "timestamp": timestamp,
        "machine": machine,
        "description": description
    }])

    # append
    updated_df = pd.concat([records_df, new_row], ignore_index=True)

    # 轉 CSV → base64
    csv_bytes = updated_df.to_csv(index=False).encode("utf-8")
    csv_b64 = base64.b64encode(csv_bytes).decode()

    payload = {
        "message": f"Add record: {timestamp} {machine}",
        "content": csv_b64,
        "branch": GIT_BRANCH
    }

    if records_sha:
        payload["sha"] = records_sha

    url = f"https://api.github.com/repos/{GIT_OWNER}/{GIT_REPO}/contents/records.csv"
    resp = requests.put(url, headers=headers, json=payload)

    if resp.status_code in (200, 201):
        st.success("✅ 状态已记录并同步到 GitHub！")
        st.rerun()
    else:
        st.error(f"❌ 推送失败：{resp.status_code}")
        st.code(resp.text)
