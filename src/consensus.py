"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

# 存放不同肌少症诊断共识的字典
# 第一层key为诊断共识名称，第二层key为年龄区间（仅AWGS 2025有），
# 第三层key为评估大类名称，第四层key为测试条目名称，第五层key为性别简写
CUTOFFS = {
	"AWGS 2025": {
		"50-64": {
			"muscle_strength": {
				"handgrip": {"M": 34.0, "F": 20.0},
			},
			"muscle_mass": {
				"dxa_height": {"M": 7.2, "F": 5.5},
				"bia_height": {"M": 7.6, "F": 5.7},
				"dxa_bmi": {"M": 0.80, "F": 0.55},
				"bia_bmi": {"M": 0.90, "F": 0.63},
			},
		},
		
		">=65": {
			"muscle_strength": {
				"handgrip": {"M": 28.0, "F": 18.0},
			},
			"muscle_mass": {
				"dxa_height": {"M": 7.0, "F": 5.4},
				"bia_height": {"M": 7.0, "F": 5.7},
				"dxa_bmi": {"M": 0.73, "F": 0.52},
				"bia_bmi": {"M": 0.83, "F": 0.57},
			},
		},
	},

	"AWGS 2019": {
		"muscle_strength": {
			"handgrip": {
				"M": 28.0,  # 男性握力 < 28 kg 提示下降
				"F": 18.0  # 女性握力 < 18 kg 提示下降
			},
		},
		
		"muscle_mass": {
			"dxa_height": {
				"M": 7.0,  # DXA 测量：男性 ASM/height² < 7.0 kg/m²
				"F": 5.4  # DXA 测量：女性 ASM/height² < 5.4 kg/m²
			},
			"bia_height": {
				"M": 7.0,  # BIA 测量：男性 ASM/height² < 7.0 kg/m²
				"F": 5.7  # BIA 测量：女性 ASM/height² < 5.7 kg/m²
			},
		},
		
		"physical_performance": {
			"gait_speed": {
				"M": 1.0,  # 步速 < 1.0 m/s
				"F": 1.0
			},
			"chair_stand": {
				"M": 12.0,  # 5次坐立试验 ≥ 12 秒
				"F": 12.0
			},
			"sppb": {
				"M": 9.0,  # 简易躯体功能电池评分 (SPPB) ≤ 9 分提示低躯体功能
				"F": 9.0
			},
		},
	},

	"EWGSOP2": {
		"muscle_strength": {
			"handgrip": {
				"M": 27.0,  # 男性握力 < 27 kg
				"F": 16.0  # 女性握力 < 16 kg
			},
			"chair_stand": {
				"M": 15.0,  # 5次坐立试验 > 15 秒 (注：部分临床研究采用 ≥15s)
				"F": 15.0
			},
		},
		
		"muscle_mass": {
			"asm": {
				"M": 20.0,  # 绝对骨骼肌质量 (ASM) < 20.0 kg
				"F": 15.0  # 绝对骨骼肌质量 (ASM) < 15.0 kg
			},
			"asm_height": {
				"M": 7.0,  # ASM/height² < 7.0 kg/m²
				"F": 5.5  # ASM/height² < 5.5 kg/m²
			},
		},
		
		"physical_performance": {
			"gait_speed": {
				"M": 0.8,  # 步速 ≤ 0.8 m/s
				"F": 0.8
			},
			"sppb": {
				"M": 8.0,  # SPPB 评分 ≤ 8 分
				"F": 8.0
			},
			"tug": {
				"M": 20.0,  # Timed Up and Go (TUG) 测试 ≥ 20 秒
				"F": 20.0
			},
			"400m_walk": {
				"M": 360.0,  # 400米步行测试：无法完成或耗时 ≥ 6 分钟 (360秒)
				"F": 360.0
			},
		},
	},
}