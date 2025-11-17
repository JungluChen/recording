import streamlit as st
import pandas as pd
import os
from io import BytesIO
import base64
import requests

st.title("机器清单维护与推送")

# ------------------------------------------------------
# GitHub Config from Secrets
# ------------------------------------------------------
GIT_USER = st.secrets.get("GIT_USERNAME", "")
GIT_EMAIL = st.secrets.get("GIT_EMAIL", "")
GIT_TOKEN = st.secrets.get("GIT_TOKEN", "")
GIT_OWNER = st.secrets.get("GIT_OWNER", "")
GIT_REPO = st.secrets.get("GIT_REPO", "")
GIT_BRANCH = st.secrets.get("GIT_BRANCH", "main")

# ------------------------------------------------------
# File path (must be writable on Streamlit Cloud)
# ------------------------------------------------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

FILE_PATH = os.path.join(DATA_DIR, "machines.xlsx")

# 初始化檔案
if not os.path.exists(FILE_PATH):
    df_init = pd.DataFrame({"Machines": [], "Spec": [], "Note": []})
    df_init.to_excel(FILE_PATH, index=False)

# ------------------------------------------------------
# Load + Editor
# ------------------------------------------------------
df = pd.read_excel(FILE_PATH)
edited_df = st.data_editor(df, num_rows="dynamic")

if st.button("保存并推送到 GitHub"):
    if not all([GIT_TOKEN, GIT_OWNER, GIT_REPO, GIT_BRANCH]):
        st.error("缺少必要的 GitHub 机密配置")
    else:
        edited_df.to_excel(FILE_PATH, index=False)
        try:
            with open(FILE_PATH, "rb") as f:
                content_b64 = base64.b64encode(f.read()).decode()
            url = f"https://api.github.com/repos/{GIT_OWNER}/{GIT_REPO}/contents/{FILE_PATH}"
            headers = {"Authorization": f"Bearer {GIT_TOKEN}", "Accept": "application/vnd.github+json"}
            sha = None
            resp_get = requests.get(url, headers=headers, params={"ref": GIT_BRANCH})
            if resp_get.status_code == 200:
                data = resp_get.json()
                sha = data.get("sha")
            payload = {"message": "Update machines.xlsx via Streamlit", "content": content_b64, "branch": GIT_BRANCH}
            if sha:
                payload["sha"] = sha
            resp_put = requests.put(url, headers=headers, json=payload)
            if resp_put.status_code in (200, 201):
                st.success("已推送到 GitHub")
            else:
                st.error("推送失败，请检查令牌或权限")
        except Exception:
            st.error("推送失败，请检查令牌或权限")

# ------------------------------------------------------
# Download
# ------------------------------------------------------
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button(label="下载 machines.xlsx", data=to_excel(edited_df), file_name="machines.xlsx")
