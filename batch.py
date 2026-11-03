"""表格读取、列映射与 Excel 导出；诊断仍由纯 Python 引擎完成。"""

import pandas as pd
from collections.abc import Mapping
from io import BytesIO
from pathlib import Path


from engine import evaluate, resolve_rules
from models import Consensus


def sheet_names(data: bytes) -> list[str]:
    """读取 xlsx 工作表名称并及时关闭工作簿。

    Args:
        data: 上传文件的原始字节。

    Returns:
        工作表名称列表。
    """
    # BytesIO 把上传字节包装成文件对象；with 在读取完成后自动关闭工作簿资源。
    with pd.ExcelFile(BytesIO(data), engine="openpyxl") as workbook:
        return workbook.sheet_names


def read_table(
        data: bytes,
        filename: str,
        sheet: str | None = None,
        has_header: bool = True,
) -> pd.DataFrame:
    """用 pandas 直接读取 CSV 或 xlsx，列名不做任何额外处理。

    有表头时交给 pandas 以 header=0 读取：重复列名、空表头、数字表头等
    都由 pandas 自行决定；无表头时以 header=None 读取，列名为 0、1、2……。
    本函数不再重命名、去空格、去重或校验列名。

    Args:
        data: 文件内容。
        filename: 文件名，仅用于判断 CSV / xlsx 格式。
        sheet: Excel 工作表名；None 表示第一张工作表。
        has_header: 首行是否为列名。

    Returns:
        pandas 直接读取得到的数据表。
    """
    suffix = Path(filename).suffix.lower()
    header = 0 if has_header else None
    if suffix == ".csv":
        try:
            # UTF-8-sig 同时兼容普通 UTF-8 和 Excel 导出的带 BOM 的 UTF-8 文件。
            return pd.read_csv(BytesIO(data), header=header, encoding="utf-8-sig",
                               skip_blank_lines=False)
        except UnicodeDecodeError:
            return pd.read_csv(BytesIO(data), header=header, encoding="gb18030",
                               skip_blank_lines=False)
    if suffix == ".xlsx":
        return pd.read_excel(BytesIO(data), sheet_name=sheet or 0,
                             header=header, engine="openpyxl")
    raise ValueError(f"本工具仅支持 .xlsx 或 .csv 文件，当前文件：{filename}")


def validate_mapping(
        consensus: Consensus,
        frame: pd.DataFrame,
        mapping: Mapping[str, object],
        selections: Mapping[str, str] | None = None,
) -> None:
    """检查“诊断字段 → 上传表格列名”的对应关系，不检查每行测量值。

    例如，mapping={"gender": "性别", "hgs": "右手握力", "gait_speed": None}
    表示：诊断引擎的 gender 从表格“性别”列取值，hgs 从“右手握力”列取值，
    gait_speed 没有指定数据列。字典的键是程序使用的字段编号，值才是文件列名。

    selections 则用于选择测量方案，例如 {"mass": "bia_height"} 表示肌量采用
    BIA、身高平方校正。它决定使用哪些规则，不负责指定从文件哪一列读取数据。

    本函数只检查整张表共用的映射配置。某个单元格是否为空、数值是否有效，
    以及缺测后还能否确定诊断阶段，留给 diagnose_batch 中的 evaluate 逐行判断。

    Args:
        consensus: 当前共识。
        frame: 输入表格。
        mapping: 内部记录字段到源列名的映射；值为 None 表示不从表格读取该项。
        selections: 维度编号到互斥方案编号的映射；None 表示使用默认方案。

    Returns:
        无返回值。正常结束表示映射检查通过；不修改 frame 或 mapping。

    Raises:
        ValueError: 基本信息未映射、重复映射、未知字段或列不存在。
    """
    # 1. 根据所选仪器／校正方式，确定当前真正参与评估的规则。
    active = resolve_rules(consensus, selections)
    # 展平各维度的规则元组，收集所有允许映射的测量字段并去重。
    fields = {rule.field for rules in active.values() for rule in rules}
    # | 是集合的并集：测量字段加上当前共识需要的基本信息字段。
    allowed = fields | set(consensus.context_fields)

    # 2. 表格必须有记录，否则无法进行批量诊断；列名本身不再额外校验。
    if frame.empty:
        raise ValueError("数据表为空")

    # set(mapping) 取得字典的键；集合相减找出“传入了但当前方案不认识”的字段。
    if set(mapping) - allowed:
        raise ValueError("列映射包含当前方案未使用的诊断条目")

    # 3. 性别、需要时的年龄必须选择数据列。
    for field in consensus.context_fields:
        if mapping.get(field) is None:
            label = "性别" if field == "gender" else "年龄"
            raise ValueError(f"请选择记录{label}的数据列")

    # 4. 收集所有实际选中的列名，排除表示“未选择”的 None。
    selected = [column for column in mapping.values() if column is not None]
    # 集合会去重。如果去重后的数量减少，就说明至少一列被多个诊断条目使用。
    if len(set(selected)) != len(selected):
        # dict.fromkeys 按首次出现顺序去重，避免错误提示反复列出同一列。
        repeated = [column for column in dict.fromkeys(selected) if selected.count(column) > 1]
        raise ValueError(f"不同诊断条目不能选择同一列：{'、'.join(map(str, repeated))}")

    # 5. 防止映射引用不存在的列，例如更换文件后沿用了之前文件的列名。
    for column in selected:
        if column not in frame.columns:
            raise ValueError(f"你选择的 {column} 列不存在，请重新选择。")

    # 6. 至少要选择一个测量字段；只选性别、年龄无法开始测量评估。
    # 此处不强制每个维度都选列：部分共识在缺少肌量或体力表现时，仍能给出
    # 疑似阶段或已确认的诊断。缺哪项会阻止当前结论，由各共识的分级函数决定。
    if not any(mapping.get(field) is not None for field in fields):
        raise ValueError("尚未选择任何诊断指标的数据列")


def diagnose_batch(
        consensus: Consensus,
        frame: pd.DataFrame,
        mapping: Mapping[str, object],
        selections: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """将表格中的每一行转换为单人记录，评估后追加结果与说明两列。

    数据流为：整表映射检查 → 按映射取出一名受试者的数据 → 调用统一诊断引擎
    → 收集结论和说明 → 将结果按原始行顺序写入表格副本。

    单行数据无效时，evaluate 返回“无法评估”及错误说明，其他行仍会继续处理；
    整表的列映射或规则配置有误时则抛出异常，停止本次批量处理。

    Args:
        consensus: 当前共识定义。
        frame: 原始记录。
        mapping: 内部记录字段到原始列名的映射；None 表示该项没有数据列。
        selections: 维度编号到互斥方案编号的映射；None 使用共识默认方案。

    Returns:
        原始记录加诊断结果、评估说明的副本，保留原始行顺序和索引。
        原始 frame 不会被修改；新增列名与原始列冲突时，自动附加编号。

    Raises:
        ValueError: 列映射或方案无效。
    """
    # 1. 映射配置整张表共用，因此进入逐行循环前检查一次即可。
    validate_mapping(consensus, frame, mapping, selections)

    # 两个列表始终各保存一个值对应一条原始记录，顺序与 frame 的行顺序一致。
    labels: list[str] = []
    explanations: list[str] = []

    # 2. iterrows() 每次返回 (行索引, 这一行的 Series)。
    for _, row in frame.iterrows():
        # 按映射构造单人记录；两种情况统一转成 None：
        #   column is None：这个诊断条目没有选择数据列；
        #   pd.isna(row[column])：选了列，但当前单元格是 NaN、NA、NaT 等空值。
        # 这里不使用“if not 单元格值”，因为 SPPB 的 0 分是有效测量。
        record = {field: None if column is None or pd.isna(row[column]) else row[column]
                  for field, column in mapping.items()}

        # 3. 交给与单人诊断相同的入口，处理性别、数值范围、阈值及分级。
        # 不在这里捕获所有异常，以免将规则配置错误误当成某一行的数据缺失。
        result = evaluate(consensus, record, selections)

        # result.label 是用于显示的结论，例如“肌少症”或“无法评估”。
        labels.append(result.label)
        # issues 保存非法输入说明；notes 保存缺测或当前诊断阶段的说明。
        explanations.append("；".join((*result.issues, *result.notes)))

    # 4. 在原表副本上追加结果，避免调用本函数后原始 frame 多出两列。
    output = frame.copy()
    for title, values in (("诊断结果", labels), ("评估说明", explanations)):
        name = f"【{consensus.title}】{title}"
        # 保留不带编号的基础列名。若原表已有同名列，则依次尝试 (2)、(3)……，
        # 直到找到未被占用的列名，防止覆盖既有数据或上一次诊断结果。
        original, suffix = name, 2
        while name in output.columns:
            name = f"{original} ({suffix})"
            suffix += 1
        # 5. 列表按行的位置赋值：values[0] 写入第一条记录，以此类推。
        output[name] = values
    return output


def export_excel(frame: pd.DataFrame) -> bytes:
    """生成唯一提供下载的 Excel 格式，单元格按普通文本／数值写入。

    Args:
        frame: 带诊断结果的数据表。

    Returns:
        可供下载的 xlsx 文件字节。
    """
    # 在内存中生成文件，无需为每次下载创建临时磁盘文件。
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # index=False 不把 DataFrame 内部行索引写成额外的 Excel 数据列。
        frame.to_excel(writer, index=False, sheet_name="肌少症诊断结果")
        worksheet = writer.sheets["肌少症诊断结果"]
        # A2 表示滚动区域从第二行开始，第一行的表头始终保留在视窗顶部。
        worksheet.freeze_panes = "A2"
        # 原始数据中的 '=...' 应保留为文本，不在下载文件中意外变成公式。
        for row in worksheet:
            for cell in row:
                if cell.data_type == "f":
                    cell.data_type = "s"
    # 离开 with 后工作簿已写入完成；返回 bytes 交给 st.download_button。
    return buffer.getvalue()
