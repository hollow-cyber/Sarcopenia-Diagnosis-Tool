"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""


def diagnose_sarcopenia(
		data_row: dict,
		consensus_name: str,
		cutoffs_dict: dict,
) -> str:
	"""
	根据输入的一行测试结果数据、选择的共识、诊断阈值字典进行多指标并联诊断。

	Args:
		data_row: 字典形式存储的数据，key 为统一的语义化名称 (如 'age', 'hgs', 'chair_stand' 等)
		consensus_name: 肌少症诊断共识名称
		cutoffs_dict: 肌少症诊断共识的阈值字典

	Returns:
		诊断结果或者无法诊断的信息
	"""
	try:
		# 1. 性别信息提取
		gender = str(data_row.get('gender', '')).strip().upper()
		if gender in ['男', 'M', 'MALE', '0', ]:
			gender_key = 'M'
		elif gender in ['女', 'F', 'FEMALE', '1']:
			gender_key = 'F'
		else:
			return "性别数据无法识别"
		
		# 2. 年龄与共识边界检查
		age = float(data_row.get('age', 0))
		if consensus_name == "AWGS 2025":
			if 50 <= age < 65:
				age_group = "50-64"
			elif age >= 65:
				age_group = ">=65"
			else:
				return f"年龄不在{consensus_name}评估范围内"
			ref = cutoffs_dict[age_group]
		else:
			# AWGS 2019 / EWGSOP2 不在顶层拆分年龄组
			ref = cutoffs_dict
		
		# ==========================================
		# 3. 肌肉力量评估 (Muscle Strength)
		# ==========================================
		# 初始化肌肉力量诊断状态
		strength_status_low = False
		# 存储各种肌肉力量指标的诊断结果
		strength_results = []
		
		# 检查握力
		hgs = float(data_row.get('hgs', 0))
		if hgs > 0:
			if hgs < ref["muscle_strength"]['handgrip'][gender_key]:
				strength_results.append("low")
			else:
				strength_results.append("normal")
		
		# 检查5次起坐 (仅 EWGSOP2 需要)
		chair_stand = float(data_row.get('chair_stand', 0))
		if consensus_name == "EWGSOP2" and chair_stand > 0:
			# 注意：坐立时间大于阈值才算低下
			if chair_stand > ref["muscle_strength"]['chair_stand'][gender_key]:
				strength_results.append("low")
			else:
				strength_results.append("normal")
		
		if not strength_results:
			return "肌肉力量项目均未测试, 无法评估"
		elif "low" in strength_results:
			# 并联逻辑：只要做过的测试里有任意一个为 low，力量就算 low
			strength_status_low = True
		
		# ==========================================
		# 4. 肌肉质量评估 (Muscle Mass)
		# ==========================================
		mass_val = float(data_row.get('muscle_mass', 0))
		mass_status_low = False
		
		if mass_val > 0:
			# 兼容在前端定义的 mass_correct_method ('height' 或 'BMI' 或 '无')
			# st控件写了selectbox的值，这里其实不用设定默认值，因为肯定会有值
			method = data_row.get('mass_measure_method', 'bia').lower()
			method = "bia" if "bia" in method else "dxa"
			adj = data_row.get('mass_adjust_method', 'height').lower()
			
			method_key = f"{method}_{adj}"
			if consensus_name == "AWGS 2019":
				# AWGS 2019 区分 BIA 和 DXA，但只支持身高校正
				method_key = f"{method}_height"
			elif consensus_name == "EWGSOP2":
				# EWGSOP2 根据校正方式区分 asm (绝对质量) 或 asm_height
				method_key = 'asm_height' if adj == 'height' else 'asm'
			
			if mass_val < ref["muscle_mass"][method_key][gender_key]:
				mass_status_low = True
		else:
			return "肌肉质量项目未测试, 无法评估"
		
		# ==========================================
		# 5. 躯体功能评估 (Physical Performance)
		# ==========================================
		perf_status_low = False
		if consensus_name != "AWGS 2025":
			perf_results = []
			gait = float(data_row.get('gait_speed', 0))
			sppb_score = data_row.get('sppb', -1)  # SPPB允许为0分，用-1代表未输入
			cutoff_gait = ref['physical_performance']['gait_speed'][gender_key]
			cutoff_sppb = ref['physical_performance']['sppb'][gender_key]
			
			# SPPB评分诊断逻辑是2个共识共有的，写在if层外面
			if sppb_score >= 0:
				if sppb_score <= cutoff_sppb:
					perf_results.append("low")
				else:
					perf_results.append("normal")
			
			if consensus_name == "AWGS 2019":
				if gait > 0:
					# AWGS 2019 是 <1.0 算低下
					# TODO: 这里的大于小于等于关系后续考虑写入到consensus文件中
					if gait < cutoff_gait:
						perf_results.append("low")
					else:
						perf_results.append("normal")
				
				if chair_stand > 0:
					if chair_stand >= ref['physical_performance']['chair_stand'][gender_key]:
						perf_results.append("low")
					else:
						perf_results.append("normal")
			
			elif consensus_name == "EWGSOP2":
				# EWGSOP2 是 <=0.8算低下
				if gait <= cutoff_gait:
					perf_results.append("low")
				else:
					perf_results.append("normal")
				
				tug = float(data_row.get('tug', 0))
				walk_400 = float(data_row.get('walk_400', 0))
				if tug > 0:
					if tug >= ref['physical_performance']['tug'][gender_key]:
						perf_results.append("low")
					else:
						perf_results.append("normal")
				if walk_400 > 0:
					if walk_400 >= ref['physical_performance']['400m_walk'][gender_key]:
						perf_results.append("low")
					else:
						perf_results.append("normal")
			
			if not perf_results:
				return "体力表现项目均未测试, 无法评估"
			if "low" in perf_results:
				perf_status_low = True
		
		# ==========================================
		# 6. 整合多共识诊断结论
		# ==========================================
		if consensus_name == "AWGS 2025":
			if strength_status_low and mass_status_low:
				return "肌少症 (Sarcopenia)"
			elif strength_status_low:
				return "可能肌少症 (Possible Sarcopenia)"
			return "非肌少症 (No Sarcopenia)"
		
		elif consensus_name == "AWGS 2019":
			# 2019 逻辑：力量或躯体功能低 = 可能；再加肌肉质量低 = 确诊；三者皆低 = 严重
			if mass_status_low:
				if strength_status_low and perf_status_low:
					return "严重肌少症 (Severe Sarcopenia)"
				elif strength_status_low or perf_status_low:
					return "肌少症 (Sarcopenia)"
			elif strength_status_low or perf_status_low:
				return "可能肌少症 (Possible Sarcopenia)"
			return "非肌少症 (No Sarcopenia)"
		
		elif consensus_name == "EWGSOP2":
			# EWGSOP2 逻辑：力量低 = 可能；加质量低 = 确诊；再加功能低 = 严重
			if strength_status_low:
				if mass_status_low:
					if perf_status_low:
						return "严重肌少症 (Severe Sarcopenia)"
					return "肌少症 (Sarcopenia)"
				return "可能肌少症 (Probable Sarcopenia)"
			return "非肌少症 (No Sarcopenia)"
		
		else:
			return "未知的肌少症诊断共识, 无法评估"
	
	except Exception as e:
		return f"诊断计算时出错: {str(e)}, 无法评估"
