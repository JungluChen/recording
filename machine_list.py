import streamlit as st
import pandas as pd
import subprocess
import os
from io import BytesIO

st.title("GitHub Example - Auto Push Excel")

# ------------------------------------------------------
# GitHub Config from Secrets
# ------------------------------------------------------
GIT_USER = st.secrets["GIT_USERNAME"]
GIT_EMAIL = st.secrets["GIT_EMAIL"]
GIT_TOKEN = st.secrets["GIT_TOKEN"]
GIT_OWNER = st.secrets["GIT_OWNER"]
GIT_REPO = st.secrets["GIT_REPO"]
GIT_BRANCH = st.secrets["GIT_BRANCH"]

REMOTE_URL = f"https://{GIT_TOKEN}@github.com/{GIT_OWNER}/{GIT_REPO}.git"

# ------------------------------------------------------
# File path (must be writable on Streamlit Cloud)
# ------------------------------------------------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

FILE_PATH = os.path.join(DATA_DIR, "machines.xlsx")

# 初始化檔案
if not os.path.exists(FILE_PATH):
    df_init = pd.DataFrame({"Machine": [], "Spec": [], "Note": []})
    df_init.to_excel(FILE_PATH, index=False)

# ------------------------------------------------------
# Load + Editor
# ------------------------------------------------------
df = pd.read_excel(FILE_PATH)
edited_df = st.data_editor(df, num_rows="dynamic")

# ------------------------------------------------------
# Save & Push
# ------------------------------------------------------
if st.button("Save & Push to GitHub"):

    edited_df.to_excel(FILE_PATH, index=False)

    repo_dir = os.getcwd()

    subprocess.run(["git", "-C", repo_dir, "config", "user.name", GIT_USER])
    subprocess.run(["git", "-C", repo_dir, "config", "user.email", GIT_EMAIL])

    # Add
    subprocess.run(["git", "-C", repo_dir, "add", FILE_PATH])

    # Commit
    commit_msg = "Update machines.xlsx via Streamlit Example"
    r_commit = subprocess.run(
        ["git", "-C", repo_dir, "commit", "-m", commit_msg],
        capture_output=True, text=True
    )

    if "nothing to commit" in r_commit.stdout:
        st.info("No changes to commit.")
    else:
        # Set remote
        subprocess.run(["git", "-C", repo_dir, "remote", "set-url", "origin", REMOTE_URL])

        # Pull (avoid conflicts)
        subprocess.run(["git", "-C", repo_dir, "pull", "--rebase"])

        # Push
        r_push = subprocess.run(["git", "-C", repo_dir, "push", "origin", GIT_BRANCH])

        if r_push.returncode == 0:
            st.success("✓ Successfully pushed to GitHub!")
        else:
            st.error("✗ Failed to push. Check GitHub token / permission.")

# ------------------------------------------------------
# Download
# ------------------------------------------------------
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button(
        label="Download machines.xlsx",
    data=to_excel(edited_df),
    file_name="machines.xlsx",
)
