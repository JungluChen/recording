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

# ------------------------------------------------------
# Load + Editor
# ------------------------------------------------------
headers = {"Authorization": f"Bearer {GIT_TOKEN}", "Accept": "application/vnd.github+json"} if GIT_TOKEN else {}
remote_df = None
remote_sha = None
remote_path = None
remote_content_b64 = None
if all([GIT_OWNER, GIT_REPO, GIT_BRANCH, GIT_TOKEN]):
    for p in ["machines.xlsx", "data/machines.xlsx"]:
        url = f"https://api.github.com/repos/{GIT_OWNER}/{GIT_REPO}/contents/{p}"
        resp_get = requests.get(url, headers=headers, params={"ref": GIT_BRANCH})
        if resp_get.status_code == 200:
            data = resp_get.json()
            remote_sha = data.get("sha")
            remote_path = p
            remote_content_b64 = data.get("content")
            try:
                content_bytes = base64.b64decode(remote_content_b64)
                remote_df = pd.read_excel(BytesIO(content_bytes))
            except Exception:
                remote_df = None
            break
if remote_df is None:
    if not os.path.exists(FILE_PATH):
        pd.DataFrame({"Machines": [], "Spec": [], "Note": []}).to_excel(FILE_PATH, index=False)
    df = pd.read_excel(FILE_PATH)
else:
    df = remote_df
st.session_state["remote_sha"] = remote_sha
st.session_state["remote_path"] = remote_path or "machines.xlsx"
st.session_state["remote_content_b64"] = remote_content_b64
edited_df = st.data_editor(df, num_rows="dynamic")

if st.button("保存并推送到 GitHub"):
    if not all([GIT_TOKEN, GIT_OWNER, GIT_REPO, GIT_BRANCH]):
        st.error("缺少必要的 GitHub 机密配置")
    else:
        try:
            output_bytes = BytesIO()
            with pd.ExcelWriter(output_bytes, engine="openpyxl") as writer:
                edited_df.to_excel(writer, index=False)
            new_bytes = output_bytes.getvalue()
            prev_b64 = st.session_state.get("remote_content_b64")
            prev_bytes = base64.b64decode(prev_b64) if isinstance(prev_b64, str) else None
            if prev_bytes is not None and prev_bytes == new_bytes:
                st.info("未检测到变化")
            else:
                content_b64 = base64.b64encode(new_bytes).decode()
                rp = st.session_state.get("remote_path") or "machines.xlsx"
                url = f"https://api.github.com/repos/{GIT_OWNER}/{GIT_REPO}/contents/{rp}"
                sha = st.session_state.get("remote_sha")
                payload = {"message": "Update machines.xlsx via Streamlit", "content": content_b64, "branch": GIT_BRANCH}
                if sha:
                    payload["sha"] = sha
                resp_put = requests.put(url, headers=headers, json=payload)
                if resp_put.status_code in (200, 201):
                    st.success("已推送到 GitHub")
                    st.session_state["remote_sha"] = resp_put.json().get("content", {}).get("sha") or sha
                    st.session_state["remote_content_b64"] = content_b64
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
