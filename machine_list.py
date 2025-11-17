import streamlit as st
import pandas as pd
import base64
import requests
from io import BytesIO

st.title("机器清单")

# ------------------------------------------------------
# 🚀 GitHub 設定（全部來自 Secrets）
# ------------------------------------------------------
GIT_TOKEN = st.secrets["GIT_TOKEN"]
GIT_OWNER = st.secrets["GIT_OWNER"]
GIT_REPO = st.secrets["GIT_REPO"]
GIT_BRANCH = st.secrets.get("GIT_BRANCH", "main")

# GitHub API Header
headers = {
    "Authorization": f"Bearer {GIT_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ------------------------------------------------------
# 1️⃣ 從 GitHub 讀取 repo 根目錄的 machines.xlsx
# ------------------------------------------------------
FILE_PATH = "machines.xlsx"
url = f"https://api.github.com/repos/{GIT_OWNER}/{GIT_REPO}/contents/{FILE_PATH}"

resp = requests.get(url, headers=headers, params={"ref": GIT_BRANCH})

if resp.status_code != 200:
    st.error("❌ 無法讀取 GitHub 上的 machines.xlsx\n請確認該檔案存在於 repo 根目錄。")
    st.stop()

json_data = resp.json()
remote_sha = json_data.get("sha")
remote_b64 = json_data.get("content")

# 解碼 Excel
file_bytes = base64.b64decode(remote_b64)
df = pd.read_excel(BytesIO(file_bytes))

# ------------------------------------------------------
# 2️⃣ 顯示可編輯 Data Editor
# ------------------------------------------------------
edited_df = st.data_editor(df, num_rows="dynamic")

# ------------------------------------------------------
# 3️⃣ 保存 + 推送（PUT 更新 GitHub 文件）
# ------------------------------------------------------
if st.button("保存"):

    try:
        # 轉成 excel bytes
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            edited_df.to_excel(writer, index=False)
        new_bytes = output.getvalue()
        new_b64 = base64.b64encode(new_bytes).decode()

        payload = {
            "message": "Update machines.xlsx via Streamlit Cloud",
            "content": new_b64,
            "sha": remote_sha,
            "branch": GIT_BRANCH
        }

        resp_put = requests.put(url, headers=headers, json=payload)

        if resp_put.status_code in (200, 201):
            st.success("✅ 保存成功！")
        else:
            st.error(f"推送失敗：{resp_put.status_code}")
            st.code(resp_put.text)

    except Exception as e:
        st.error(f"推送失敗：{e}")

# ------------------------------------------------------
# 4️⃣ 下載最新編輯版本
# ------------------------------------------------------
def to_excel(df):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()

st.download_button(
    label="下载当前编辑后的 machines.xlsx",
    data=to_excel(edited_df),
    file_name="machines.xlsx"
)

