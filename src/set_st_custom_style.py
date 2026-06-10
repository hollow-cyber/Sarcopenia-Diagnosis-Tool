"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import os
import base64
import uuid
import streamlit as st
from pathlib import Path
from typing import Literal


def get_image_base64(image_path: str | Path) -> str:
	"""将本地图片转换为 base64 编码

	Args:
		image_path: 图片文件完整路径。

	Returns:
		64位格式的图片。
	"""
	img_bytes = Path(image_path).read_bytes()
	return base64.b64encode(img_bytes).decode()


def set_st_header(
		main_title: str,
		sidebar_title: str | None,
		logo_path: str | Path | None,
		layout_mode: Literal["centered", "wide"] | None = "wide",
		notice_str: str | None = None,
		warning_str: str | None = "运行程序时请不要关闭黑色命令行窗口，它才是本体。",
) -> None:
	"""
	设置streamlit网页头部显示信息。

	Args:
		main_title: 主标题。
		sidebar_title: 侧边栏标题，None表示没有侧边栏。
		logo_path: 图标文件路径，None表示不展示图标。
		layout_mode: 页面显示布局，None表示使用默认布局方式。
		notice_str: 条形框中提示的文字内容。
		warning_str: 主页面显示的警告信息，自带警告符号，可是markdown格式。
	"""
	
	# 设置页面布局
	if layout_mode:
		st.set_page_config(layout=layout_mode)
	
	# 主页面内容
	# 注入自定义 CSS
	st.markdown(
		"""
			<style>
			.main-title {
				display: flex;  /* 使用 flexbox 布局 */
				align-items: center;  /* 垂直居中 */
				justify-content: center;  /* 水平居中 */
				gap: 20px;  /* 图片和文字之间的间距 */
			}
			.main-title img {
				width: 70px;  /* 设置图片宽度 */
				height: auto;  /* 保持图片比例 */
			}
			</style>
		""",
		unsafe_allow_html=True
	)
	
	if logo_path and os.path.isfile(logo_path):
		# 转换图片为 base64
		logo_base64 = get_image_base64(logo_path)
		
		# 在主页面显示图片和标题
		st.markdown(
			f"""
				<div class="main-title">
					<img src="data:image/png;base64,{logo_base64}" alt="logo">
					<h1>{main_title}</h1>
				</div>
				""",
			unsafe_allow_html=True
		)
	else:
		st.markdown(
			f"""
				<div class="main-title">
					<h1>{main_title}</h1>
				</div>
				""",
			unsafe_allow_html=True
		)
	
	# 设置渐变色块显示的醒目告示
	css_style = """
		<style>
		@keyframes tech-flow {
		    0% {
		        background-position: 0% 50%;
		        box-shadow: 0 10px 20px -5px rgba(74, 144, 226, 0.5);
		    }
		    50% {
		        background-position: 100% 50%;
		        box-shadow: 0 15px 30px -5px rgba(144, 19, 254, 0.4);
		    }
		    100% {
		        background-position: 0% 50%;
		        box-shadow: 0 10px 20px -5px rgba(74, 144, 226, 0.5);
		    }
		}

		/* 增加一道横跨色块的光亮扫描感 */
		@keyframes shimmer {
		    0% { transform: translateX(-150%) skewX(-25deg); }
		    100% { transform: translateX(150%) skewX(-25deg); }
		}

		.fancy-gradient-box {
		    /* 保持原色彩，但调整渐变角度和层次 */
		    background: linear-gradient(-45deg, #4A90E2, #9013FE, #23A6D5, #23D5AB);
		    background-size: 300% 300%;

		    /* 更加高级的贝塞尔曲线动画 */
		    animation: tech-flow 8s cubic-bezier(0.4, 0, 0.2, 1) infinite;

		    color: #FFFFFF;
		    padding: 10px; /* 稍微增加一点内边距更有质感 */
		    border-radius: 16px; /* 更圆润的边缘符合现代科技感 */
		    text-align: center;
		    font-weight: 600;
		    font-size: 20px;
		    margin-bottom: 20px;
		    line-height: 1.6;
		    position: relative;
		    overflow: hidden; /* 必须溢出隐藏以实现光效 */

		    /* 强化边框：玻璃态半透明边框 */
		    border: 1px solid rgba(255, 255, 255, 0.2);
		    backdrop-filter: blur(5px);
		}

		/* 科技感亮光扫过效果 */
		.fancy-gradient-box::after {
		    content: "";
		    position: absolute;
		    top: 0;
		    left: 0;
		    width: 60%;
		    height: 100%;
		    background: linear-gradient(
		        120deg,
		        transparent,
		        rgba(255, 255, 255, 0.2),
		        transparent
		    );
		    animation: shimmer 5s infinite linear;
		    z-index: 1;
		}

		/* 确保文字在光效之上 */
		.fancy-gradient-box span {
		    position: relative;
		    z-index: 2;
		}
		</style>
		"""
	# 在调用处稍微修改下 html_content 以适应文字层级
	html_content = f"<div class='fancy-gradient-box'><span>{notice_str}</span></div>"
	st.markdown(css_style + html_content, unsafe_allow_html=True)
	
	if sidebar_title:
		# 添加侧边栏组件
		# 注入自定义 CSS，设置侧边栏标题居中
		st.markdown(
			"""
			<style>
			[data-testid="stSidebar"] h1 {
				text-align: center;  /* 设置文字居中 */
			}
			</style>
			""",
			unsafe_allow_html=True
		)
		st.sidebar.title(sidebar_title)
		st.sidebar.divider()
		
	if warning_str:
		st.warning(
			f"""
			⚠️ {warning_str}
		""")


def show_custom_toast(
		message: str,
		icon: str = "💡",
		total_time: int | float = 2,
		fade_in_time: int | float = 0.25,
		fade_out_time: int | float = 0.5,
		top_gap: int | float = 0.3,
) -> None:
	"""显示一个基于纯 CSS 动画的非阻塞提示窗口。

    该函数通过注入 HTML 和 CSS 实现一个自定义提示框。提示框会从屏幕顶部
    中心弹出，并在指定时间后自动消失。整个过程不使用 time.sleep，
    因此不会阻塞 Streamlit 的主线程或导致页面刷新转圈。
    如果淡入和淡出时间之和大于总时长，将自动调整以确保动画完整。

    Args:
        message: 提示框中显示的文字内容。
        icon: 提示框左侧显示的图标或 Emoji。
        total_time: 提示框从出现到彻底消失的总时长（秒）。
        fade_in_time: 淡入动画的时长（秒）。
        fade_out_time: 淡出动画的时长（秒）。
        top_gap: 提示窗口与屏幕顶部的距离，小于1则表示距离占总体屏幕高度的比例，大于1则表示绝对距离像素。
    """
	
	# 校验并调整时间参数，防止逻辑错误导致关键帧冲突
	if (fade_in_time + fade_out_time) > total_time:
		# 如果总时间不足，按比例缩减淡入淡出时间
		scale = total_time / (fade_in_time + fade_out_time + 0.1)
		fade_in_time *= scale
		fade_out_time *= scale
	
	# 计算 CSS 关键帧百分比
	# 0% 为起点，100% 为终点
	in_pct = (fade_in_time / total_time) * 100
	out_pct = ((total_time - fade_out_time) / total_time) * 100
	
	# 生成唯一的 ID 避免 CSS 类名冲突
	uid = str(uuid.uuid4())[:8]

	# 获取当前屏幕高度
	try:
		import tkinter
		root = tkinter.Tk()
		height = root.winfo_screenheight()
		root.destroy()
	except ImportError:
		# 设置默认屏幕高度为1080
		height = 1080
		# 显式声明 tkinter 未定义
		tkinter = None
	top_distance = int(height * top_gap) if top_gap < 1 else int(top_gap)
	
	toast_html = f"""
    <style>
        @keyframes toast-anim-{uid} {{
            0% {{
                opacity: 0;
                transform: translate(-50%, 50px);  /* 这里的50px表示上浮移动的距离 */
            }}
            {in_pct}% {{
                opacity: 1;
                transform: translate(-50%, 0);
            }}
            {out_pct}% {{
                opacity: 1;
                transform: translate(-50%, 0);
            }}
            100% {{
                opacity: 0;
                transform: translate(-50%, -50px);
                visibility: hidden;
            }}
        }}

        .toast-container-{uid} {{
            position: fixed;
            top: {top_distance}px;  /* 距离顶端的距离 */
            left: 50%;
            transform: translateX(-50%);
            z-index: 999999;

            background-color: rgba(250, 250, 250, 0.9);  /* 设置背景颜色以及透明度 */
            color: #000000;
            padding: 12px 24px;
            border-radius: 10px;  /* 边框倒角大小 */
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);

            display: flex;
            align-items: center;
            gap: 12px;
            font-family: "Source Sans Pro", sans-serif;
            pointer-events: none; /* 确保不挡住下层点击 */

            animation: toast-anim-{uid} {total_time}s ease-in-out forwards;
        }}
    </style>

    <div class="toast-container-{uid}">
        <span style="font-size: 20px;">{icon}</span>
        <span>{message}</span>
    </div>
    """
	
	st.markdown(toast_html, unsafe_allow_html=True)