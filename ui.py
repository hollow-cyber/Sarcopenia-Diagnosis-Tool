"""共识驱动的 Streamlit 页面外壳。

这里只处理所有共识共用的部分：页头、基本信息、模式切换、批量文件读取、
结果展示与下载。每个共识自己的输入面板写在 consensuses/<共识>.py 的
render_form(ctx) 中，本模块通过共识注册表调用它。
"""

import pandas as pd
import streamlit as st
from collections.abc import Sequence
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile
from openpyxl.utils.exceptions import InvalidFileException

from batch import diagnose_batch, export_excel, header_issues, read_table, sheet_names
from consensuses import renderer_for
from engine import evaluate
from models import UNASSESSABLE, NEGATIVE, POSSIBLE, PROBABLE, Consensus, Result
from ui_controls import FormContext, render_in_columns


CONTEXT_LABELS = {"gender": "性别", "age": "年龄"}
DOWNLOAD_NOTICE_KEY = "diagnosis:download_notice"


def clear_diagnosis_results() -> None:
    """清空所有共识、模式保存的诊断结果。

    切换共识、诊断模式、上传文件或选择工作表时作为 on_change 回调调用，
    避免用户还没完成当前输入时看到上一次的诊断结论。
    """
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith("diagnosis:") and key.endswith(":result"):
            st.session_state.pop(key, None)
    st.session_state.pop(DOWNLOAD_NOTICE_KEY, None)


def mark_download_clicked() -> None:
    """记录下载按钮点击，供本次重运行显示下载成功提示。"""
    st.session_state[DOWNLOAD_NOTICE_KEY] = True


def render_context(
        consensus: Consensus,
        batch: bool,
        columns: Sequence[object],
        namespace: str,
) -> dict[str, object]:
    """仅生成当前共识需要的基本信息。

    Args:
        consensus: 当前定义。
        batch: 是否绘制批量列映射。
        columns: 数据表列名。
        namespace: 当前共识、模式及文件的控件命名空间。

    Returns:
        单人基本信息值，或批量列名映射。
    """
    # 同一套基本信息布局，单人模式保存“输入值”，批量模式保存“源列名”。
    values: dict[str, object] = {}
    with st.expander("🧑‍🦳 受试者基本信息", expanded=True):
        def draw(field: str) -> None:
            """绘制一个基本信息控件。

            Args:
                field: 基本信息字段编号。
            """
            label = CONTEXT_LABELS[field]
            # key 标识控件状态，不是诊断字段；namespace 使不同共识／模式互不覆盖。
            key = f"{namespace}:context:{field}"
            if batch:
                values[field] = st.selectbox(
                    f"记录{label}的列名：", columns, index=None, placeholder="请选择列名", key=key,
                    help="支持男/女、M/F、male/female、1/2（1男，2女）。" if field == "gender" else None)
            elif field == "gender":
                # 页面显示男／女，实际返回 M/F，避免显示文案影响内部数据格式。
                values[field] = st.radio("性别：", ("M", "F"), horizontal=True,
                                         format_func={"M": "男", "F": "女"}.get, key=key)
            else:
                # 年龄下限来自共识的第一个年龄组，避免输入低于适用范围的年龄。
                bands = list(consensus.age_bands.values())
                minimum_age = bands[0][0]
                last_maximum = bands[-1][1]
                maximum_age = last_maximum - 1 if last_maximum is not None else None
                # value=None 使输入初始为空；不默认填入 50 或 65 岁来代替真实年龄。
                values[field] = st.number_input("年龄（岁）：", min_value=minimum_age,
                                               max_value=maximum_age, value=None, step=1,
                                               placeholder="请输入年龄",
                                               help=f"本共识适用于年龄{consensus.age_range_label}的人群。",
                                               key=key)
        # 需要哪些基本信息由共识对象决定，不在此处按共识名称判断。
        render_in_columns(consensus.context_fields, draw, max_columns=2)
    return values


def render_source(consensus: Consensus) -> None:
    """展示共享目录中的原文截图、适用说明和 DOI 链接。

    Args:
        consensus: 当前定义。
    """
    with st.expander("查看当前诊断共识"):
        # 文献适用范围及本工具的取舍集中放在原文折叠框，测量界面保持简洁。
        for note in consensus.notes:
            st.caption(note)
        # 图片与图注按相同位置配对；注册校验已保证提供图注时两者长度一致。
        for index, filename in enumerate(consensus.images):
            # 应用从主目录启动，直接使用 img 中的相对路径。
            path = Path("img") / filename
            if path.is_file():
                caption = consensus.image_captions[index] if consensus.image_captions else None
                st.image(str(path), width="stretch", caption=caption)
            else:
                st.warning(f"图片文件缺失：{filename}")
        st.page_link(f"https://doi.org/{consensus.doi}", label="查看共识原文", icon="📄", width="stretch")


def show_result(result: Result) -> None:
    """按稳定的结果代码展示结论，并逐条显示输入问题或缺测说明。

    Args:
        result: 统一引擎返回的诊断结果。
    """
    message = f"诊断结果：{result.label}"
    if result.code == NEGATIVE:
        st.success(message)
    elif result.code in (POSSIBLE, PROBABLE, UNASSESSABLE):
        st.warning(message)
    else:
        # st.error 在这里充当醒目的红色结论框，不表示 Python 抛出了运行异常。
        st.error(message)
    for note in (*result.issues, *result.notes):
        st.write(f"• {note}")


def display_table(frame: pd.DataFrame) -> None:
    """绘制含非法原始数据的表格，不触发 Arrow 的混合类型转换错误。

    Args:
        frame: 原始数据或诊断结果；仅创建显示副本，不修改下载内容。
    """
    # infer_objects 尝试恢复 object 列中可推断的数值类型，随后只修改显示副本。
    view = frame.infer_objects().copy()
    for column in view.columns:
        if view[column].dtype == object:
            # 数字和“invalid”混在一列时，Arrow 无法直接推断统一数值类型。
            view[column] = view[column].astype("string")
    st.dataframe(view, hide_index=True, width="stretch")


@st.cache_data(show_spinner=False)
def load_table(
        data: bytes,
        filename: str,
        sheet: str | None,
        has_header: bool,
) -> pd.DataFrame:
    """按当前选项读取上传文件；列名完全保留 pandas 的读取结果。

    Args:
        data: 文件字节。
        filename: 文件名。
        sheet: 工作表名称。
        has_header: 是否有表头。

    Returns:
        解析完成的记录表。
    """
    # Streamlit 交互会让脚本重新执行；装饰器按全部参数缓存返回数据，避免每次
    # 点输入框都重新解析同一个工作簿。文件、工作表或表头改变后自动重新读取。
    return read_table(data, filename, sheet=sheet, has_header=has_header)


def render_diagnosis(
        consensus: Consensus,
        upload_file_ext: tuple[str, ...] = ("xlsx", "csv"),
) -> None:
    """连接通用页面、共识输入面板、统一诊断入口与可持续下载的结果状态。

    Args:
        consensus: 用户选中的共识。
        upload_file_ext: 允许用户上传的文件类型
    """
    # 1. Streamlit 每次交互都会重新执行本函数。key 稳定才能保留输入，同时按共识
    # 区分命名空间，避免 AWGS 与 FNIH 等不同页面控件互相覆盖。
    prefix = f"diagnosis:{consensus.key}"
    options = ["👤 手动输入单人数据", "📁 批量 Excel/CSV 上传"]
    mode = st.segmented_control("🔍 诊断模式：", options,
                                default=options[0], key=f"{prefix}:mode",
                                on_change=clear_diagnosis_results)
    if mode is None:
        # segmented_control 允许取消选择，此时不继续绘制任何一种诊断表单。
        return
    batch = mode == options[1]
    frame: pd.DataFrame | None = None
    columns: list[object] = []
    file_tag = ""
    file_name = ""
    
    # 2. 批量模式先读文件，得到供列映射控件选择的列名；单人模式直接跳过此段。
    if batch:
        uploaded = st.file_uploader("请上传包含受试者数据的 Excel 或 CSV 文件：", type=upload_file_ext,
                                    key=f"{prefix}:upload", on_change=clear_diagnosis_results,
                                    help="空列、重复列名等会被pandas库自动处理，下载的结果文件中的列名是处理后的列名"
                                    )
        if uploaded is None:
            return
        data = uploaded.getvalue()
        file_tag = uploaded.name
        file_name = Path(uploaded.name).stem
        has_header = st.checkbox("首行为列名", value=True, key=f"{prefix}:header",
                                 on_change=clear_diagnosis_results)
        sheet: str | None = None
        try:
            # CSV 没有工作表选择；Excel 先列出工作表，再按所选表读取记录。
            if uploaded.name.lower().endswith(".xlsx"):
                sheet = st.selectbox("需要读取的工作表：", sheet_names(data),
                                     key=f"{prefix}:sheet:{file_tag}",
                                     on_change=clear_diagnosis_results)
            frame = load_table(data, uploaded.name, sheet, has_header)
        except (ValueError, OSError, KeyError, EOFError, BadZipFile,
                InvalidFileException, ParseError) as exc:
            st.error(f"读取文件失败：{exc}")
            return
        columns = frame.columns.tolist()
        with st.expander("📊 数据预览"):
            display_table(frame)
        # 原始表头有空列名或重复列名时，pandas 会自动改写；提示按预览中的列名映射。
        problems = header_issues(data, uploaded.name, sheet) if has_header else []
        if problems:
            st.warning(
                "⚠️ 检测到上传文件存在" + "；".join(problems) +
                "。pandas 会自动改写这些列名，请按照“数据预览”中显示的列名来选择映射列。")

    # 不同文件／模式的列映射分别保存，避免误用上一次文件的映射。
    namespace = f"{prefix}:{mode}:{file_tag}"
    
    # 3. 通用基本信息 + 该共识自己的输入面板；两种模式共用同一份 render_form。
    context = render_context(consensus, batch, columns, namespace)
    ctx = FormContext(consensus, batch, columns, namespace)
    measurements = renderer_for(consensus)(ctx)
    selections = ctx.selections
    # 展开两个字典，合并为完整输入；方案选择另存于 selections，不混入测量值。
    payload = {**context, **measurements}
    result_key = f"{prefix}:{mode}:result"
    
    # 4. 只有点击诊断按钮才计算，单纯编辑控件不会悄悄生成新诊断。
    if st.button("🩺 开始诊断", type="primary", width="stretch", key=f"{prefix}:diagnose"):
        # 新诊断开始前移除旧结果，避免本次校验失败时还显示上次成功结果。
        st.session_state.pop(result_key, None)
        with st.spinner("正在计算诊断结果，请稍候…"):
            if batch and frame is not None:
                try:
                    # 批量控件返回列名或 None；列名可能是数字、带空格等 pandas 原样结果。
                    mapping = {field: value for field, value in payload.items()
                               if value is not None}
                    output = diagnose_batch(consensus, frame, mapping, selections)
                    # session_state 在脚本重运行之间保留结果：结果表与 Excel 字节。
                    st.session_state[result_key] = (output, export_excel(output))
                except ValueError as exc:
                    st.error(f"无法评估：{exc}")
            else:
                # 单人直接使用相同引擎；下载文件在单人模式下不需要，使用 None 占位。
                st.session_state[result_key] = (evaluate(consensus, payload, selections), None)

    # 5. 程序重运行时继续显示本次模式最近一次诊断的结果。
    cached = st.session_state.get(result_key)
    if cached is None:
        return
    result, excel_bytes = cached
    if isinstance(result, pd.DataFrame):
        st.success(f"批量诊断完成，共 {len(result)} 条记录；请同时查看评估说明。")
        display_table(result)
        # 下载回调只负责记录点击，重运行后再显示提示，避免中断下载。
        st.download_button("📥 下载诊断结果 Excel", data=excel_bytes,
                           file_name=f"{file_name}_{consensus.title}_Results.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           on_click=mark_download_clicked, width="stretch",
                           key=f"{prefix}:download")
        if st.session_state.pop(DOWNLOAD_NOTICE_KEY, False):
            st.toast("下载成功", icon="✅")
    else:
        show_result(result)
