"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import io
import os
import pandas as pd
import streamlit as st
from urllib.parse import urljoin
from typing import cast

from src.consensus import CUTOFFS
from src.set_st_custom_style import set_st_header, show_custom_toast
from src.diagnose_sarcopenia import diagnose_sarcopenia
from src.process_col_vars import check_col_vars_unique, get_label_from_var, check_module_vars, check_row_module_vars


def clear_st_session():
	"""清除所有的st.session_state"""
	st.session_state.clear()


def st_diagnose_sarcopenia():
	# 设置页面配置
	set_st_header(
		main_title="肌少症在线诊断工具",
		sidebar_title=None,
		logo_path="imgs/华西logo.ico",
		layout_mode="centered",
		notice_str="本项目受到四川大学华西医院、国家老年疾病临床研究中心的支持",
		warning_str=None,
	)
	
	# 增加一空行
	st.write()
	
	with st.container(border=True):
		url_main = "https://doi.org/"
		sarcopenia_consensus_doi = {
			"AWGS 2025": "10.1038/s43587-025-01004-y",
			"AWGS 2019": "10.1016/j.jamda.2019.12.012",
			"EWGSOP2": "10.1093/ageing/afy169",
		}
		sarcopenia_consensus_list = list(sarcopenia_consensus_doi.keys())
		sarcopenia_consensus = st.pills("🔍 用于诊断肌少症的共识：", sarcopenia_consensus_list,
		                                default=sarcopenia_consensus_list[0], on_change=clear_st_session)
		
		sarcopenia_cutoffs = CUTOFFS[sarcopenia_consensus]
		imgs_list = [f"imgs/{sarcopenia_consensus} cutoff.png", f"imgs/{sarcopenia_consensus} algorithm.png"]
		url = urljoin(url_main, sarcopenia_consensus_doi[sarcopenia_consensus])
		if sarcopenia_consensus == "AWGS 2025":
			st.warning(f"⚠️ {sarcopenia_consensus}诊断共识仅支持诊断50岁及以上的受试者。")
		
		with st.expander("查看当前诊断共识"):
			for img_path in imgs_list:
				if os.path.exists(img_path):
					st.image(img_path)
			st.page_link(url, label="查看共识原文", icon="📄", width="stretch")
	
	# 选择诊断模式
	diagnosis_mode_list = ["👤 手动输入受试者信息进行诊断", "📁 批量 Excel/CSV 诊断与结果下载"]
	diagnosis_mode = st.segmented_control("🔍 诊断模式：", diagnosis_mode_list,
	                                      default=diagnosis_mode_list[0], on_change=clear_st_session)
	# 存储上传文件的所有列名的list
	columns = []
	df = pd.DataFrame()
	if diagnosis_mode == diagnosis_mode_list[1]:
		uploaded_file = st.file_uploader("请上传包含所有诊断项结果的Excel或csv文件：", type=["xlsx", "xls", "csv"],
		                                 help="程序默认csv文件中数据首行为列名，非数字型内容会被当成空值")
		
		if uploaded_file is not None:
			try:
				show_data = True
				# 读取文件
				if uploaded_file.name.lower().endswith('.csv'):
					df = cast(pd.DataFrame, pd.read_csv(uploaded_file))
				else:
					# 读取 Excel 文件的所有表单名称
					excel_file = pd.ExcelFile(uploaded_file)
					sheet_names = excel_file.sheet_names
					st.info(f"📋 发现文件共包含 {len(sheet_names)} 个表单: {', '.join(sheet_names)}")
					
					cols = st.columns([1, 1])
					with cols[0]:
						# 让用户选择表单
						selected_sheet = st.selectbox("需要读取的表单：", sheet_names)
					with cols[1]:
						header = st.checkbox("表单包含列名且首行是列名", value=True)
						header = 0 if header else None
						show_data = st.checkbox("显示表单数据", value=True)
					df = pd.read_excel(uploaded_file, sheet_name=selected_sheet, header=header)
					columns = df.columns.tolist()
				
				if show_data:
					with st.expander("📊 数据预览"):
						st.dataframe(df)
					st.divider()
			except Exception as e:
				st.error(f"❌ 读取文件时出错: {e}")
				st.stop()
		else:
			st.stop()
	
	with st.expander("🧑‍🦳 受试者基本信息", expanded=True):
		# 记录当前基本信息模块存储的变量名称
		base_info_vars = []
		gender_label = "性别"
		age_label = "年龄"
		
		# 根据是否选择了AWGS 2025共识自动判断是否将界面拆分成2列
		cols_list = [1]
		if sarcopenia_consensus == "AWGS 2025":
			cols_list.append(1)
		
		cols = st.columns(cols_list)
		with cols[0]:
			if diagnosis_mode == diagnosis_mode_list[0]:
				gender = st.radio(f"{gender_label}：", ["男", "女"], horizontal=True)
				base_info_vars.append("gender")
			elif diagnosis_mode == diagnosis_mode_list[1]:
				gender_col = st.selectbox(f"记录{gender_label}的列名：", columns, index=None, placeholder="请选择列名",
				                          help="该列值可为：男/女、M/F、male/female、0/1")
				base_info_vars.append("gender_col")
		if sarcopenia_consensus == "AWGS 2025":
			with cols[1]:
				if diagnosis_mode == diagnosis_mode_list[0]:
					age = st.number_input(f"{age_label}：", min_value=50, max_value=None, value=50)
					base_info_vars.append("age")
				elif diagnosis_mode == diagnosis_mode_list[1]:
					age_col = st.selectbox(f"记录{age_label}的列名：", columns, index=None, placeholder="请选择列名")
					base_info_vars.append("age_col")
	
	with st.expander("🏋️ 受试者肌肉力量信息", expanded=True):
		muscle_strength_vars = []
		hgs_label = "握力(kg)"
		chair_stand_label = "5次起坐用时(秒)"
		
		cols_list = [1]
		if sarcopenia_consensus == "EWGSOP2":
			st.caption("只要此类项目中的任意一项低于阈值即会被判断为肌肉力量低下")
			cols_list.append(1)
		
		cols = st.columns(cols_list)
		with cols[0]:
			if diagnosis_mode == diagnosis_mode_list[0]:
				hgs = st.number_input(f"{hgs_label}：", min_value=0.0, max_value=None, format="%.2f")
				muscle_strength_vars.append("hgs")
			elif diagnosis_mode == diagnosis_mode_list[1]:
				hgs_col = st.selectbox(f"记录{hgs_label}的列名：", columns, index=None, placeholder="请选择列名")
				muscle_strength_vars.append("hgs_col")
		if sarcopenia_consensus == "EWGSOP2":
			with cols[1]:
				if diagnosis_mode == diagnosis_mode_list[0]:
					chair_stand = st.number_input(f"{chair_stand_label}：", min_value=0.0, max_value=None, format="%.2f")
					muscle_strength_vars.append("chair_stand")
				elif diagnosis_mode == diagnosis_mode_list[1]:
					chair_stand_col = st.selectbox(f"记录{chair_stand_label}的列名：", columns, placeholder="请选择列名")
					muscle_strength_vars.append("chair_stand_col")
	
	with st.expander("💪 受试者肌肉质量信息", expanded=True):
		muscle_mass_vars = []
		muscle_mass_label = "四肢骨骼肌质量(ASM)"
		
		cols = st.columns([1, 1])
		with cols[0]:
			mass_measure_method = st.selectbox("肌肉质量的测量仪器：",
			                                   ["BIA (Bioelectrical impedance analysis)",
			                                    "DXA (Dual-energy X-ray absorptiometry)"],
			                                   help="此选项在EWGSOP2诊断共识中无意义")
		with cols[1]:
			if sarcopenia_consensus == "AWGS 2025":
				mass_adjust_method = st.selectbox("肌肉质量的校正方式：", ["身高(m)", "BMI"])
			elif sarcopenia_consensus == "AWGS 2019":
				mass_adjust_method = st.selectbox("肌肉质量的校正方式：", ["身高(m)", "BMI"], disabled=True)
			elif sarcopenia_consensus == "EWGSOP2":
				mass_adjust_method = st.selectbox("肌肉质量的校正方式：", ["身高(m)", "无"])
		
		if mass_adjust_method == "身高(m)":
			mass_adjust_method = "height"
		if mass_adjust_method == "height":
			muscle_mass_label = muscle_mass_label[:-1] + "/height²)"
		elif mass_adjust_method == "BMI":
			muscle_mass_label = muscle_mass_label[:-1] + "/BMI)"
		if diagnosis_mode == diagnosis_mode_list[0]:
			muscle_mass = st.number_input(f"{muscle_mass_label}：", min_value=0.0, max_value=None, format="%.2f")
			muscle_mass_vars.append("muscle_mass")
		elif diagnosis_mode == diagnosis_mode_list[1]:
			muscle_mass_col = st.selectbox(f"记录{muscle_mass_label}的列名：", columns, index=None,
			                               placeholder="请选择列名")
			muscle_mass_vars.append("muscle_mass_col")
	
	physical_performance_vars = []
	if sarcopenia_consensus != "AWGS 2025":
		with st.expander("🚶‍♂️‍➡️ 受试者体力表现信息", expanded=True):
			st.caption("只要此类项目中的任意一项低于阈值即会被判断为体力表现低下")
			gait_speed_label = "步速(m/s)"
			sppb_label = "简易躯体功能评分(SPPB)"
			
			if sarcopenia_consensus == "AWGS 2019":
				gait_speed_label = "6米" + gait_speed_label
				cols = st.columns([1, 1, 1.2])
				with cols[0]:
					if diagnosis_mode == diagnosis_mode_list[0]:
						gait_speed = st.number_input(f"{gait_speed_label}：", min_value=0.0, max_value=None,
						                             format="%.2f")
						physical_performance_vars.append("gait_speed")
					elif diagnosis_mode == diagnosis_mode_list[1]:
						gait_speed_col = st.selectbox(f"记录{gait_speed_label}的列名：", columns, index=None,
						                              placeholder="请选择列名")
						physical_performance_vars.append("gait_speed_col")
				with cols[1]:
					chair_stand_label = "5次起坐用时(秒)"
					if diagnosis_mode == diagnosis_mode_list[0]:
						chair_stand = st.number_input(f"{chair_stand_label}：", min_value=0.0, max_value=None,
						                              format="%.2f")
						physical_performance_vars.append("chair_stand")
					elif diagnosis_mode == diagnosis_mode_list[1]:
						chair_stand_col = st.selectbox(f"记录{chair_stand_label}的列名：", columns, index=None,
						                               placeholder="请选择列名")
						physical_performance_vars.append("chair_stand_col")
				with cols[2]:
					if diagnosis_mode == diagnosis_mode_list[0]:
						sppb = st.number_input(f"{sppb_label}：", min_value=0, max_value=12)
						physical_performance_vars.append("sppb")
					elif diagnosis_mode == diagnosis_mode_list[1]:
						sppb_col = st.selectbox(f"记录{sppb_label}的列名：", columns, index=None,
						                        placeholder="请选择列名")
						physical_performance_vars.append("sppb_col")
			
			elif sarcopenia_consensus == "EWGSOP2":
				tug_label = "Timed Up and Go (TUG) 测试用时(秒)"
				_400_m_walk_label = "400米步行测试用时(秒)"
				cols = st.columns([1, 1])
				with cols[0]:
					if diagnosis_mode == diagnosis_mode_list[0]:
						gait_speed = st.number_input(f"{gait_speed_label}：", min_value=0.0, max_value=None,
						                             format="%.2f")
						physical_performance_vars.append("gait_speed")
						tug = st.number_input(f"{tug_label}：", min_value=0.0, max_value=None, format="%.2f")
						physical_performance_vars.append("tug")
					elif diagnosis_mode == diagnosis_mode_list[1]:
						gait_speed_col = st.selectbox(f"记录{gait_speed_label}的列名：", columns, index=None,
						                              placeholder="请选择列名")
						physical_performance_vars.append("gait_speed_col")
						tug_col = st.selectbox(f"记录{tug_label}的列名：", columns, index=None, placeholder="请选择列名")
						physical_performance_vars.append("tug_col")
				with cols[1]:
					if diagnosis_mode == diagnosis_mode_list[0]:
						sppb = st.number_input(f"{sppb_label}：", min_value=0, max_value=12)
						physical_performance_vars.append("sppb")
						_400_m_walk = st.number_input(f"{_400_m_walk_label}：", min_value=0.0, max_value=None,
						                              format="%.2f")
						physical_performance_vars.append("_400_m_walk")
					elif diagnosis_mode == diagnosis_mode_list[1]:
						sppb_col = st.selectbox(f"记录{sppb_label}的列名：", columns, index=None,
						                        placeholder="请选择列名")
						physical_performance_vars.append("sppb_col")
						_400_m_walk_col = st.selectbox(f"记录{_400_m_walk_label}的列名：", columns, index=None,
						                               placeholder="请选择列名")
						physical_performance_vars.append("_400_m_walk_col")
	
	# 初始化记录开始诊断按钮点击的状态和存储诊断结果的变量
	if "diagnose_button_click" not in st.session_state:
		st.session_state.diagnose_button_click = False
	if "df_final" not in st.session_state:
		st.session_state.df_final = None
	
	if st.button("🩺 开始诊断", use_container_width=True):
		# 更改diagnose_button_click的状态，并且初始化df_final，后续就能进行诊断计算
		st.session_state.diagnose_button_click = True
		st.session_state.df_final = None
	
	# 只有当diagnose_button_click = True且df_final = None时，才进行诊断
	# 防止有了df_final点击下载结果按钮的时候又诊断一遍
	if st.session_state.diagnose_button_click and st.session_state.df_final is None:
		# 确认执行诊断逻辑后就初始化diagnose_button_click，防止后续更改一个变量的值就自动诊断了
		st.session_state.diagnose_button_click = False
		
		# ------ 场景 A：单个受试者手动输入诊断 ------
		if diagnosis_mode == diagnosis_mode_list[0]:
			# 单个受试者手动输入诊断不会有批量输出结果，所以初始化st.session_state.df_final
			st.session_state.df_final = None
			
			# 计算前先严格校验各模块的数值变量是否都为 0，即没传入数据
			# 由于性别通过st.radio选择，肯定存在，年龄也设定了默认值，所以这两个不用判断
			error_messages = check_module_vars(muscle_strength_vars, "肌肉力量")
			error_messages = check_module_vars(muscle_mass_vars, "肌肉质量", error_messages)
			error_messages = check_module_vars(physical_performance_vars, "体力表现", error_messages)
			
			# 如果有错误信息就中断执行
			if error_messages:
				for err in error_messages:
					st.error(err)
				st.stop()
			else:
				# 打包单人数据并执行诊断
				# 这里可能存在的变量均设定了输入值的范围，不会存在没输入为None的情况
				single_row = {
					'age': age if sarcopenia_consensus == "AWGS 2025" else 65,  # 非2025共识默认给常备年龄
					'gender': gender,
					'hgs': hgs,
					'chair_stand': chair_stand if 'chair_stand' in locals() else 0.0,
					'muscle_mass': muscle_mass,
					'mass_measure_method': mass_measure_method,
					'mass_adjust_method': mass_adjust_method,
					'gait_speed': gait_speed if 'gait_speed' in locals() else 0.0,
					'sppb': sppb if 'sppb' in locals() else -1,
					'tug': tug if 'tug' in locals() else 0.0,
					'walk_400': _400_m_walk if '_400_m_walk' in locals() else 0.0
				}
				
				result = diagnose_sarcopenia(single_row, sarcopenia_consensus, sarcopenia_cutoffs)
				
				# 展示单人诊断结果
				show_custom_toast("诊断完成！", icon="✅")
				if "非" in result:
					st.success(f"### 诊断结果：{result}")
				elif "可能" in result:
					st.warning(f"### 诊断结果：{result}")
				else:
					st.error(f"### 诊断结果：{result}")
		
		
		# ------ 场景 B：批量 Excel/CSV 诊断与下载 -----
		elif diagnosis_mode == diagnosis_mode_list[1]:
			error_messages = []
			
			if not gender_col:
				error_messages.append("❌ 【基本信息】模块：请选择性别的列名。")
			if sarcopenia_consensus == "AWGS 2025" and not age_col:
				error_messages.append("❌ 【基本信息】模块：请选择年龄的列名。")
			
			error_messages = check_module_vars(muscle_strength_vars, "肌肉力量", error_messages, using_col_vars=True)
			error_messages = check_module_vars(muscle_mass_vars, "肌肉质量", error_messages, using_col_vars=True)
			error_messages = check_module_vars(physical_performance_vars, "体力表现", error_messages,
			                                   using_col_vars=True)
			
			# 检查是否有不同的诊断项条目选择了同一列名（排重）
			if_duplicate_cols, duplicates = check_col_vars_unique()
			if if_duplicate_cols:
				error_messages.append("❌ 错误：请勿为不同的诊断项条目重复选择相同的列名！")
				for value, vars in duplicates.items():
					error_messages.append(
						f"程序发现以下诊断项条目使用了相同的列名，请检查: {', '.join([get_label_from_var(var) for var in vars])}")
			
			if error_messages:
				for err in error_messages:
					st.error(err)
				st.stop()
			else:
				# 逐行执行批量诊断
				with st.spinner("系统正在基于选定的共识对表格中数据进行批量诊断...", show_time=True):
					# 存储批量诊断结果的空列表
					batch_results = []
					
					# 定义内部软转换工具函数，防止因为单项文本导致整行崩溃
					def to_float_safe(val: int | float | str, default: float = 0.0) -> float:
						try:
							if pd.isna(val): return default
							return float(val)
						except (ValueError, TypeError):
							return default
					
					def to_int_safe(val: int | float | str, default: int = -1) -> int:
						try:
							if pd.isna(val): return default
							# 先转float防1.0浮点字符串报错
							return int(float(val))
						except (ValueError, TypeError):
							return default
					
					for idx, row in df.iterrows():
						# 基础必需项校验：如果性别或肌肉质量本身就不是数字/是空的，则无法诊断
						if pd.isna(row.get(gender_col)):
							batch_results.append({'诊断结果': '缺失性别数据'})
							continue
						elif pd.isna(row.get(muscle_mass_col)):
							batch_results.append({'诊断结果': '缺失肌肉质量数据'})
							continue
						
						# 转换当前行数据为标准字典结构
						try:
							# 2. 精细化装配行数据，对每一项使用安全转换
							row_data = {
								'age': to_float_safe(row[age_col], default=65.0) if (
										'age_col' in locals() and age_col is not None) else 65.0,
								'gender': row[gender_col],
								'hgs': to_float_safe(row[hgs_col]) if (
										'hgs_col' in locals() and hgs_col is not None) else 0.0,
								'chair_stand': to_float_safe(row[chair_stand_col]) if (
										'chair_stand_col' in locals() and chair_stand_col is not None) else 0.0,
								'muscle_mass': to_float_safe(row[muscle_mass_col]),
								'mass_measure_method': mass_measure_method,
								'mass_adjust_method': mass_adjust_method,
								'gait_speed': to_float_safe(row[gait_speed_col]) if (
										'gait_speed_col' in locals() and gait_speed_col is not None) else 0.0,
								'sppb': to_int_safe(row[sppb_col]) if (
										'sppb_col' in locals() and sppb_col is not None) else -1,
								'tug': to_float_safe(row[tug_col]) if (
										'tug_col' in locals() and tug_col is not None) else 0.0,
								'walk_400': to_float_safe(row[_400_m_walk_col]) if (
										'_400_m_walk_col' in locals() and _400_m_walk_col is not None) else 0.0
							}
							
							# 3. 诊断前二次校验：确保虽然格式转成功了，但并联项不全为默认非测值
							check_module_result = [
								check_row_module_vars(row_data, muscle_strength_vars, "肌肉力量"),
								check_row_module_vars(row_data, muscle_mass_vars, "肌肉质量"),
								check_row_module_vars(row_data, physical_performance_vars, "体力表现")
							]
							check_module_result = [result for result in check_module_result if result]
							if check_module_result:
								result = "、".join(check_module_result)
							else:
								# 运行诊断算法
								result = diagnose_sarcopenia(row_data, sarcopenia_consensus, sarcopenia_cutoffs)
						
						except Exception as e:
							result = f"行数据解析异常: {str(e)}"
						
						batch_results.append({'诊断结果': result})
					
					# 将诊断结果合并写回原始 DataFrame 并展示
					df_final = pd.DataFrame(batch_results)
					df[f'【{sarcopenia_consensus}】诊断结果'] = df_final['诊断结果']
					show_custom_toast("诊断完成！", icon="✅")
					st.session_state.df_final = df
	
	if st.session_state.df_final is not None:
		# 根据df_final是否有值来决定显示数据和下载按钮
		st.success(f"🎉 批量诊断成功！应用{sarcopenia_consensus}标准的诊断结果见数据表最后一列。")
		st.dataframe(st.session_state.df_final)
		output_stream = io.BytesIO()
		with pd.ExcelWriter(output_stream, engine='openpyxl') as writer:
			st.session_state.df_final.to_excel(writer, index=False, sheet_name='肌少症诊断结果')
		excel_data = output_stream.getvalue()
		
		st.download_button(
			label="📥 下载完成诊断的 Excel 报表",
			data=excel_data,
			file_name=f"Sarcopenia_{sarcopenia_consensus}_Results.xlsx",
		)


if __name__ == "__main__":
	st_diagnose_sarcopenia()
