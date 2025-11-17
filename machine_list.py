import streamlit as st
import pandas as pd
from io import BytesIO

# 设置页面标题
st.title("机器列表编辑器")
df = pd.read_excel("/Users/user/Desktop/EMS/Recording/machines.xlsx")

# 显示并允许编辑
edited_df = st.data_editor(df, num_rows="dynamic")

# 保存按钮
if st.button("保存到原始文件"):
    try:
        edited_df.to_excel("/Users/user/Desktop/EMS/Recording/machines.xlsx", index=False)
        st.success("已保存到原始文件")
    except Exception as e:
        st.error(f"保存失败：{e}")

# 下载按钮
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output.getvalue()

st.download_button(
    label="下载修改后的 machines.xlsx",
    data=to_excel(edited_df),
    file_name="machines.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
