import streamlit as st

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