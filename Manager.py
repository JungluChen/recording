import streamlit as st
clean_ui = """
<style>
/* 隱藏右上角所有工具列（包含 Manage the app） */
[data-testid="stAppToolbar"] {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
button[title="Manage the app"] {display: none !important;}
button[title="Deploy this app"] {display: none !important;}
button[title="Settings"] {display: none !important;}

/* 隱藏右下角 Streamlit Cloud 小船徽章 */
[data-testid="stBadge"] {display: none !important;}

/* 隱藏 header */
header {visibility: hidden;}
</style>
"""
st.markdown(clean_ui, unsafe_allow_html=True)

st.set_page_config(
    page_title="工厂管理",  # 页面标题
    page_icon="🏭",             # 页面图标
    layout="wide",              # 页面布局：宽屏适配工厂数据
    initial_sidebar_state="expanded",  # 侧边栏初始状态：展开便于导航
    menu_items={                # 隐藏右上角菜单项
        "Get help": None,
        "Report a bug": None,
        "About": None
    }
)

pg = st.navigation(["Admin.py", "machine_list.py"])
pg.run()
