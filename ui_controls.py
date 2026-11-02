"""共识文件共享的输入控件与分列工具。

每个共识文件在自己的模块里编写 ``render_form(ctx)`` 描述输入界面；
这里提供它需要的小工具：折叠面板、互斥方案选择、测量输入框和自动分列。

批量模式下同样的调用会返回“源列名”，因此每个共识的 render_form
同时适用于手动输入和批量列映射，不需要再写一套批量界面。
"""

import json
import math
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from typing import TypeVar

import streamlit as st

from models import Consensus, Domain, Rule


# 每个评估维度的固定图标；新增维度时可在这里补充。
DOMAIN_ICONS = {"strength": "🏋️", "mass": "💪", "performance": "🚶"}
# 仪器显示全称：定义里仍用 DXA / BIA 作为数据键，界面只改显示文字。
INSTRUMENT_LABELS = {
    "DXA": "DXA（双能X线吸收法）",
    "BIA": "BIA（生物电阻抗分析法）",
}
# 替代测量维度的统一提示，放在维度面板标题下方。
ANY_OF_CAPTION = "任一评估项目达到诊断阈值，即认为该维度低下"
T = TypeVar("T")


def render_in_columns(
        items: Sequence[T],
        draw: Callable[[T], None],
        *,
        weights: Sequence[float] | None = None,
        max_columns: int = 3,
) -> None:
    """根据控件数量和定义宽度自动分列，四项自动排成两行两列。

    Args:
        items: 按显示顺序排列的控件描述。
        draw: 绘制单个控件的回调。
        weights: 各控件相对宽度，未指定时等宽。
        max_columns: 一行允许的最多列数。
    """
    if not items:
        return
    widths = list(weights) if weights is not None else [1.0] * len(items)
    # 先按最多列数算出至少需要几行，再均衡每行列数：
    # 3项、最多3列 → 1行3列；4项、最多3列 → 2行2列，而不是3+1。
    row_count = math.ceil(len(items) / max_columns)
    column_count = math.ceil(len(items) / row_count)
    for start in range(0, len(items), column_count):
        row = items[start:start + column_count]
        cols_list = widths[start:start + len(row)]
        cols = st.columns(cols_list)
        for column, item in zip(cols, row):
            with column:
                draw(item)


def format_option(
        axis: str,
        value: str | None,
        recommendation: str,
) -> str:
    """把方案属性值转换为页面显示文字。

    Args:
        axis: 属性名，instrument 或 adjustment。
        value: 方案属性值；None 表示不区分仪器。
        recommendation: 原文推荐／备选标记，仅校正方式使用。

    Returns:
        页面显示文字。
    """
    if axis == "instrument":
        return INSTRUMENT_LABELS.get(value or "", value or "不区分仪器")
    text = value or "不区分仪器"
    return f"{text}（{recommendation}）" if recommendation else text


class FormContext:
    """一次表单渲染的上下文：命名空间、模式、列名和已选方案。

    同一个实例既用于手动输入，也用于批量列映射：``batch`` 为 True 时，
    控件返回的是“记录该项的列名”，而不是受试者的测量数值。

    Attributes:
        consensus: 当前共识定义。
        batch: 是否处于批量列映射模式。
        columns: 批量模式下可选择的源列名。
        namespace: 控件 key 的命名空间，用于区分共识、模式与文件。
        selections: 互斥维度选择了哪个方案，供引擎解析规则。
    """

    def __init__(
            self,
            consensus: Consensus,
            batch: bool,
            columns: Sequence[str],
            namespace: str,
    ) -> None:
        """保存本次渲染的基本参数。

        Args:
            consensus: 当前共识定义。
            batch: 是否处于批量列映射模式。
            columns: 批量模式下可选择的源列名。
            namespace: 控件 key 的命名空间。
        """
        self.consensus = consensus
        self.batch = batch
        self.columns = list(columns)
        self.namespace = namespace
        self.selections: dict[str, str] = {}

    @contextmanager
    def panel(
            self,
            domain: Domain,
    ) -> Iterator[None]:
        """为一个评估维度打开折叠面板。

        Args:
            domain: 当前维度。

        Yields:
            面板上下文；在 with 块内绘制的控件会进入该面板。
        """
        icon = DOMAIN_ICONS.get(domain.key, "📋")
        with st.expander(f"{icon} 受试者{domain.label}信息", expanded=True):
            # 替代测量且不止一项时才提示“任一项目”，单项维度提示没有意义。
            if domain.any_of and len(domain.rules) > 1:
                st.caption(ANY_OF_CAPTION)
            yield

    def select_indicator(
            self,
            domain: Domain,
    ) -> Rule:
        """绘制仪器／校正方式选择，并返回唯一的活动规则。

        Args:
            domain: 使用互斥测量方案的维度。

        Returns:
            当前选中的规则，同时记录到 selections。
        """
        default = domain.active_rules()[0]
        if len(domain.rules) == 1:
            # 只有一个方案时无需额外显示选择控件。
            self.selections[domain.key] = default.key
            return default
        # 存在仪器信息时先选仪器，然后选校正方式；choices 保存当前已选项。
        axes = ["instrument"] if any(rule.instrument for rule in domain.rules) else []
        axes.append("adjustment")
        choices: dict[str, str | None] = {}

        def draw(axis: str) -> None:
            """绘制一个仪器或校正方式控件。

            Args:
                axis: 属性名，instrument 或 adjustment。
            """
            # 只保留与前面选择相符的规则，例如已选 BIA 后不出现 DXA 专有方案。
            candidates = [rule for rule in domain.rules
                          if all(getattr(rule, name) == value for name, value in choices.items())]
            # dict.fromkeys 按定义中的首次出现顺序去重。
            options = list(dict.fromkeys(getattr(rule, axis) for rule in candidates))
            preferred = getattr(default, axis)

            def label(value: str | None) -> str:
                """为选项补充显示文字与原文推荐／备选标记。

                Args:
                    value: 方案属性值。

                Returns:
                    页面显示文字。
                """
                matches = [rule for rule in candidates if getattr(rule, axis) == value]
                recommendation = matches[0].recommendation if axis == "adjustment" else ""
                return format_option(axis, value, recommendation)

            title = (f"{domain.label}的测量仪器：" if axis == "instrument"
                     else f"{domain.label}的校正方式：")
            # 把前序选择写进 key，切换仪器时不沿用已失效的校正选项。
            prior = json.dumps(choices, sort_keys=True, ensure_ascii=False)
            # 只有一个可选值时仍展示该属性，但禁用操作，明确当前测量方式。
            choices[axis] = st.selectbox(
                title, options, format_func=label,
                index=options.index(preferred) if preferred in options else 0,
                disabled=len(options) == 1,
                key=f"{self.namespace}:{domain.key}:axis:{axis}:{prior}")

        render_in_columns(axes, draw, max_columns=2)
        selected = next(rule for rule in domain.rules
                        if all(getattr(rule, name) == value for name, value in choices.items()))
        self.selections[domain.key] = selected.key
        return selected

    def select_and_input(
            self,
            domain: Domain,
    ) -> dict[str, object]:
        """把方案选择与测量输入并排放置为两列。

        Args:
            domain: 需要选择方案并输入数值的互斥维度。

        Returns:
            字段名到输入值（或批量列名）的映射。
        """
        left, right = st.columns(2)
        with left:
            rule = self.select_indicator(domain)
        with right:
            return self.inputs((rule,))

    def number(
            self,
            rule: Rule,
    ) -> float | int | str | None:
        """生成一个测量输入控件或对应的列映射控件。

        Args:
            rule: 当前测量规则。

        Returns:
            手动模式返回数值；批量模式返回列名；未填写时返回 None。
        """
        label = f"{rule.label}（{rule.unit}）"
        # key 含方案编号：切换校正方案时产生新控件，避免把旧校正值当成新方案输入。
        key = f"{self.namespace}:indicator:{rule.key}"
        if self.batch:
            return st.selectbox(f"记录{label}的列名：", self.columns, index=None,
                                placeholder="请选择列名", key=key)
        help_text = "请输入已按所选方案校正的比值。" if rule.adjustment != "无" else None
        if rule.integer:
            # 整数项目使用整数边界和 step=1，保证 SPPB 不会被输入成 8.5 分。
            return st.number_input(f"{label}：", min_value=int(rule.minimum),
                                   max_value=int(rule.maximum) if rule.maximum is not None else None,
                                   value=None, step=1, placeholder=rule.placeholder,
                                   help=help_text, key=key)
        # 小数项目统一显示三位小数；有效范围之外的值交给引擎给出明确提示。
        return st.number_input(f"{label}：", min_value=float(rule.minimum),
                               max_value=rule.maximum, value=None, step=0.001, format="%.3f",
                               placeholder=rule.placeholder, help=help_text, key=key)

    def inputs(
            self,
            rules: Sequence[Rule],
    ) -> dict[str, object]:
        """并排绘制一组测量输入，返回字段名到输入值的映射。

        Args:
            rules: 需要绘制的测量规则。

        Returns:
            字段名到数值（或批量列名）的映射。
        """
        values: dict[str, object] = {}

        def draw(rule: Rule) -> None:
            """绘制并保存一个测量控件。

            Args:
                rule: 当前规则。
            """
            values[rule.field] = self.number(rule)

        # 宽度来自规则定义，不按指标名称硬编码。
        render_in_columns(rules, draw, weights=[rule.column_weight for rule in rules])
        return values
