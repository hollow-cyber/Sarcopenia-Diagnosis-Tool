"""肌少症诊断工具启动入口。

请在项目主目录运行：python -m streamlit run main.py
模块直接导入，图片和文献使用主目录下的 img、ref，样式复用 src。
"""

import streamlit as st


from src.set_st_custom_style import set_st_header
from consensuses import CONSENSUSES
from ui import clear_diagnosis_results, render_diagnosis, render_source


def main() -> None:
    """绘制应用外框，并把当前共识交给通用页面渲染器。"""
    # 1. 设置页头、logo与支持单位样式
    set_st_header(
        main_title="肌少症在线诊断工具", sidebar_title=None,
        logo_path="img/华西logo.ico", layout_mode="centered", warning_str=None,
        notice_str="本项目受到四川大学华西医院、国家老年疾病临床研究中心的支持",
    )
    # 2. 此处只补充页面宽度、留白和圆角；医学规则及控件选择不放进样式代码。
    #     [data-testid="stMainBlockContainer"] {max-width: 980px; padding-top: 2rem; padding-bottom: 3rem;}
    st.markdown("""<style>
        [data-testid="stExpander"] {border-radius: 12px;}
        [data-testid="stExpander"] summary {font-weight: 600;}
        [data-testid="stBaseButton-primary"] {border-radius: 9px; min-height: 2.8rem;}
        </style>""", unsafe_allow_html=True)
    # 3. 建立“显示名称 → 共识对象”的索引；字典顺序沿用注册表中的页面顺序。
    profiles = {consensus.title: consensus for consensus in CONSENSUSES}
    with st.container(border=True):
        # tuple(profiles)取字典的键作为选项；控件返回显示名称后再查回完整定义。
        selected = st.pills("🔍 用于诊断肌少症的共识：", tuple(profiles),
                             default=CONSENSUSES[0].title, key="diagnosis:consensus",
                             on_change=clear_diagnosis_results)
        if selected is None:
            st.info("请选择一个诊断共识。")
            return
        consensus = profiles[selected]
        render_source(consensus)  # 原文展示位于顶部共识选择容器内。
    # 4. 容器外绘制诊断页面；切换共识只更换定义对象，不切换另一套页面代码。
    render_diagnosis(consensus)


if __name__ == "__main__":
    # 直接运行／由Streamlit执行此文件时启动页面；作为模块导入时不自动绘制。
    main()
