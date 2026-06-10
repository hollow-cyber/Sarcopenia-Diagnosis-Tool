"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import sys


def check_col_vars_unique() -> tuple[bool, dict[str, list[str]]]:
	"""
	检查当前作用域中所有以"_col"结尾的变量，在排除掉None后，对应的值是否有重复
	
	Returns:
		是否有重复的值，值重复的变量名
	"""
	# 获取调用者的作用域（往上一层）
	frame = sys._getframe(1)
	# 获取当前作用域的所有变量
	local_vars = frame.f_locals
	
	# 筛选以 _col 结尾的变量
	col_vars = {}
	for name, value in local_vars.items():
		if name.endswith('_col') and value is not None:
			col_vars[name] = value
	
	# 构建值到变量名的映射
	value_to_vars = {}
	for var_name, value in col_vars.items():
		if value not in value_to_vars:
			value_to_vars[value] = []
		value_to_vars[value].append(var_name)
	
	# 找出重复的
	duplicate_info = {value: vars for value, vars in value_to_vars.items() if len(vars) > 1}
	
	return len(duplicate_info) > 0, duplicate_info


def get_label_from_var(
		var_name: str,
		local_layer: int = 1,
) -> str:
	"""
	根据变量名获取对应的以"_label"结尾的变量的值
	如果变量是以"_col"结尾，则替换为"_label"，否则添加"_label"后缀
	
	Args:
		var_name: 变量名
		local_layer: 需要往上移动作用域的层数
		
	Returns:
		对应的以"_value"结尾的变量名的值，没有则为空字符串
	"""
	# 获取调用者的作用域
	frame = sys._getframe(local_layer)
	local_vars = frame.f_locals
	
	if var_name.endswith('_col'):
		# 将 '_col' 替换为 '_label'
		label_var_name = var_name.replace('_col', '_label')
	else:
		label_var_name = var_name + "_label"
	
	# 获取对应的标签值
	return local_vars.get(label_var_name, "")


def check_module_vars(
		module_var_names: list[str],
		module_name: str,
		error_messages: list[str] | None = None,
		using_col_vars: bool = False,
) -> list[str]:
	"""
	检查各个模块的变量是否至少有一个有参数值
	
	Args:
		module_var_names: 当前模块的所有变量名字符串
		module_name: 当前模块的名称
		error_messages: 记录报错信息的list
		using_col_vars: 当前模块的变量是否传入的是数据列名

	Returns:
		记录报错信息的list
	"""
	# 如果没有传入error_messages，则初始化一个空list
	if error_messages is None:
		error_messages = []
	
	# 统计模块变量中没有值的个数
	not_exist_num = 0
	for var_name in module_var_names:
		# 往上前进一层获取模块变量的作用域
		frame = sys._getframe(1)
		local_vars = frame.f_locals
		# 数值变量为0，或者为None，或者SPPB结果为-1都表示无值
		if not local_vars[var_name] or local_vars[var_name] == -1:
			not_exist_num += 1
	
	if not_exist_num and not_exist_num == len(module_var_names):
		# 获取模块各变量的标签名，注意这里要往上2层获取作用域
		var_label = "、".join([get_label_from_var(var_name, local_layer=2) for var_name in module_var_names])
		if not using_col_vars:
			if not_exist_num == 1:
				error_messages.append(f"❌ 【{module_name}】模块：{var_label}的值不能为0。")
			else:
				error_messages.append(f"❌ 【{module_name}】模块：{var_label}必须至少输入一项，不能全为0。")
		else:
			if not_exist_num == 1:
				error_messages.append(f"❌ 【{module_name}】模块：请选择{var_label}的列名。")
			else:
				error_messages.append(f"❌ 【{module_name}】模块：请选择{var_label}至少其中一项的列名。")
	
	return error_messages


def check_row_module_vars(
		row_data: dict,
		module_var_names: list[str],
		module_name: str,
) -> str:
	"""
	检查批量诊断时构造的每一行数据的各模块的变量是否至少有一个有参数值
	
	Args:
		row_data: 构造用于诊断的行数据
		module_var_names: 当前模块的所有变量名字符串
		module_name: 当前模块的名称

	Returns:
		如果检查通过，则返回空字符串，否则返回检查未通过信息
	"""
	not_exist_num = 0
	for var_name in module_var_names:
		var_name = var_name.replace('_col', '')
		if not row_data[var_name] or row_data[var_name] == -1:
			not_exist_num += 1
	
	if not_exist_num and not_exist_num == len(module_var_names):
		return f"{module_name}数据无效/未测"
	
	return ""
