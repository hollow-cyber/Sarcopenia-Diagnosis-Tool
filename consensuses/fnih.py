"""FNIH：Table 3 推荐／备选阈值，未把概念框架作为额外诊断条件。

本文件包含该共识的全部内容：阈值与测量规则（SPEC）、分级函数（classify）
和输入界面（render_form）。阈值来源：Table 3；PDF 第8页，期刊页554。
判定只要求低握力与低肌量同时成立，不增加 FNIH 原文未给出的严重程度分级。
"""

from collections.abc import Mapping

from models import (Compare, Consensus, Domain, NEGATIVE, Rule, SARCOPENIA,
                    State, Result, unavailable)
from ui_controls import FormContext


SOURCE = "Table 3；PDF 第8页，期刊页554"


def classify(states: Mapping[str, State]) -> Result:
    """判断所选 FNIH 方案下是否同时存在低握力与低肌量。

    Args:
        states: strength、mass 到 State 的映射；握力和肌量已按各自所选方案比较。

    Returns:
        是否符合联合条件；不增加 FNIH 原文未给出的严重程度分级。
    """
    strength = states["strength"]
    mass = states["mass"]

    # 本工具要求力量与肌量都有有效结果，按力量状态分支后再检查肌量。
    if strength == State.MISSING:
        if mass == State.MISSING:
            return unavailable("肌肉力量", "肌肉质量")
        else:
            return unavailable("肌肉力量")
    elif strength == State.NORMAL:
        if mass == State.MISSING:
            return unavailable("肌肉质量")
        else:
            # 力量正常、肌量已有结果：不满足两者均低的联合条件。
            return Result(NEGATIVE, "不符合 FNIH 低握力合并低肌量条件")
    else:
        if mass == State.MISSING:
            return unavailable("肌肉质量")
        elif mass == State.NORMAL:
            return Result(NEGATIVE, "不符合 FNIH 低握力合并低肌量条件")
        else:
            return Result(SARCOPENIA, "符合 FNIH 低握力合并低肌量条件")


def render_form(ctx: FormContext) -> dict[str, object]:
    """绘制 FNIH 的输入界面（手动数值或批量列名）。

    两个维度各一个折叠面板；力量与肌量都是互斥方案，按仪器／校正方式
    选择一项，推荐／备选标记由方案选择控件显示。

    Args:
        ctx: 表单上下文，提供面板、方案选择和输入控件。

    Returns:
        字段名到输入值（或批量列名）的映射。
    """
    values: dict[str, object] = {}
    strength = SPEC.domain("strength")
    with ctx.panel(strength):
        # 校正方式与握力输入并排两列，比上下两行更紧凑。
        values.update(ctx.select_and_input(strength))
    mass = SPEC.domain("mass")
    with ctx.panel(mass):
        rule = ctx.select_indicator(mass)
        values.update(ctx.inputs((rule,)))
    return values


# 规则定义：阈值、比较符、单位都集中在这里；修改阈值只需改本文件。
# Recommended与Alternate属于不同方案，不能在未切换输入含义的情况下混用阈值。
SPEC = Consensus(
    key="fnih",
    title="FNIH",
    doi="10.1093/gerona/glu010",
    source_pdf="The FNIH Sarcopenia Project Rationale, Study Description, Conference Recommendations, and Final Estimates.pdf",
    images=("FNIH cutoff.png", "FNIH algorithm.png"),
    classify=classify,
    image_captions=(None, "原文临床评估框架"),
    notes=("本工具默认采用 Table 3 的 Recommended 项，其他选项标明为 Alternate。",
           "由于原文的 ALM 阈值研究基于 DXA 测量，因此本工具限定 DXA。"),
    domains=(
        # 默认未校正握力（推荐）；切换BMI校正后输入必须是已计算的握力/BMI。
        Domain("strength", "肌肉力量", default_rule="grip_absolute", rules=(
            Rule(key="grip_absolute", field="hgs", label="握力", unit="kg",
                 compare=Compare.LT, cutoffs={"all": (26, 16)}, source=SOURCE,
                 recommendation="推荐"),
            Rule(key="grip_bmi", field="hgs", label="握力/BMI", unit="m²",
                 adjustment="BMI", compare=Compare.LT,
                 cutoffs={"all": (1.0, 0.56)}, source=SOURCE,
                 recommendation="备选"),
        )),
        # 默认DXA测量的ALM/BMI（推荐）；绝对ALM只作为明确标记的备选项。
        # Cutoff的两个数值始终依次为男、女；严格小于阈值才达到低肌量标准。
        Domain("mass", "肌肉质量", default_rule="dxa_bmi", rules=(
            Rule(key="dxa_bmi", field="muscle_mass", label="ALM/BMI", unit="m²",
                 instrument="DXA", adjustment="BMI", compare=Compare.LT,
                 cutoffs={"all": (0.789, 0.512)}, source=SOURCE,
                 recommendation="推荐"),
            Rule(key="dxa_absolute", field="muscle_mass", label="四肢瘦体重 ALM", unit="kg",
                 instrument="DXA", compare=Compare.LT,
                 cutoffs={"all": (19.75, 15.02)}, source=SOURCE,
                 recommendation="备选"),
        )),
    ),
)
