import streamlit as st
from datetime import datetime
import sqlite3
import os
import pandas as pd

db_path = 'records.db'
init_db = not os.path.exists(db_path)

conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()

if init_db:
    # 创建表（如果不存在）
    c.execute('''CREATE TABLE IF NOT EXISTS records
                 (timestamp TEXT, machine TEXT, description TEXT)''')
    conn.commit()
st.title("设备状态记录")
# 选择设备
machine = st.selectbox("请选择设备", pd.read_excel("machines.xlsx")["Machines"].tolist())
# 输入编号/情况描述
description = st.text_input("编号/情况描述")
# 记录时间
if st.button("记录当前状态"):
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    st.success(f"已记录：{timestamp} - {machine} - {description}")
    # 保存到SQL数据库
    c.execute("INSERT INTO records (timestamp, machine, description) VALUES (?, ?, ?)",
              (timestamp, machine, description))
    conn.commit()
    st.rerun()
