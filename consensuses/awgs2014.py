"""AWGS 2014：低肌量且力量或体力表现低下即诊断肌少症，不增加严重程度分级。

本文件包含该共识的全部内容：阈值与测量规则（SPEC）、分级函数（classify）
和输入界面（render_form）。阈值来源：PDF 第2页摘要、第3页 Figure 1。
"""

from collections.abc import Mapping

from models import (Compare, Consensus, Domain, NEGATIVE, Rule, SARCOPENIA,
                    State, Result, unavailable)
from ui_controls import FormContext


# SOURCE 只记录原文定位；阈值与运算符在下面各个 Rule 中一同声明。
SOURCE = "PDF 第2页摘要、第3页 Figure 1"


def classify(states: Mapping[str, State]) -> Result:
    """按低肌量且力量或体力表现低下判断，不增加严重程度分级。

    Args:
        states: mass、strength、performance 到 State 的映射，由统一引擎生成；
            不接收原始测量值，因此本函数不重复处理阈值或数值有效性。

    Returns:
        肌少症、非肌少症，或必要项目缺测的提示。
    """
    mass = states["mass"]
    strength = states["strength"]
    performance = states["performance"]

    # 第一层先区分肌量状态；只有进入LOW分支后，才联合力量与体力表现判断。
    if mass == State.MISSING:
        return unavailable("肌肉质量")
    elif mass == State.NORMAL:
        return Result(NEGATIVE, "非肌少症")
    else:
        # 肌量低＋力量低已满足诊断，无需依赖体力表现结果。
        if strength == State.LOW:
            return Result(SARCOPENIA, "肌少症")
        elif strength == State.NORMAL:
            # 肌量低、力量正常时，体力表现决定是否满足诊断。
            if performance == State.LOW:
                return Result(SARCOPENIA, "肌少症")
            elif performance == State.NORMAL:
                return Result(NEGATIVE, "非肌少症")
            else:
                return unavailable("体力表现")
        else:
            # 力量未测时，体力表现低仍足以确诊；否则需补充力量等缺测项目。
            if performance == State.LOW:
                return Result(SARCOPENIA, "肌少症")
            elif performance == State.NORMAL:
                return unavailable("肌肉力量")
            else:
                return unavailable("肌肉力量", "体力表现")


def render_form(ctx: FormContext) -> dict[str, object]:
    """绘制 AWGS 2014 的输入界面（手动数值或批量列名）。

    三个维度各一个折叠面板；肌肉质量按仪器选择 DXA 或 BIA 一种方案；
    体力表现只收集步速，作为替代测量显示。

    Args:
        ctx: 表单上下文，提供面板、方案选择和输入控件。

    Returns:
        字段名到输入值（或批量列名）的映射。
    """
    values: dict[str, object] = {}
    strength = SPEC.domain("strength")
    with ctx.panel(strength):
        rule = ctx.select_indicator(strength)
        values.update(ctx.inputs((rule,)))
    mass = SPEC.domain("mass")
    with ctx.panel(mass):
        rule = ctx.select_indicator(mass)
        values.update(ctx.inputs((rule,)))
    performance = SPEC.domain("performance")
    with ctx.panel(performance):
        # 替代测量：本共识只有步速一项，仍按替代测量接口绘制。
        values.update(ctx.inputs(performance.rules))
    return values


# 规则定义：阈值、比较符、单位都集中在这里；修改阈值只需改本文件。
# classify=classify 是把函数交给共识对象，等引擎算出维度状态后再调用。
SPEC = Consensus(
    key="awgs_2014",
    title="AWGS 2014",
    doi="10.1016/j.jamda.2013.11.025",
    source_pdf="Sarcopenia in Asia Consensus Report of the Asian Working Group for Sarcopenia.pdf",
    images=("AWGS 2014 cutoff.png", "AWGS 2014 algorithm.png"),
    classify=classify,
    domains=(
        # all 表示不做年龄分层；阈值写成 (男性, 女性)。
        Domain("strength", "肌肉力量", default_rule="handgrip", rules=(
            Rule(key="handgrip", field="hgs", label="握力", unit="kg",
                 compare=Compare.LT, cutoffs={"all": (26, 18)}, source=SOURCE),
        )),
        # 肌量每次只选择DXA或BIA的一种方案；两个方案共用输入字段但阈值各自独立。
        Domain("mass", "肌肉质量", default_rule="bia_height", rules=(
            Rule(key="dxa_height", field="muscle_mass", label="ASM/身高²", unit="kg/m²",
                 instrument="DXA", adjustment="身高²", compare=Compare.LT,
                 cutoffs={"all": (7.0, 5.4)}, source=SOURCE),
            Rule(key="bia_height", field="muscle_mass", label="ASM/身高²", unit="kg/m²",
                 instrument="BIA", adjustment="身高²", compare=Compare.LT,
                 cutoffs={"all": (7.0, 5.7)}, source=SOURCE),
        )),
        # 本共识只收集步速；严格小于0.8才低下，等于0.8不满足该项低下标准。
        Domain("performance", "体力表现", any_of=True, rules=(
            Rule(key="gait_speed", field="gait_speed", label="步速", unit="m/s",
                 compare=Compare.LT, cutoffs={"all": (0.8, 0.8)}, source=SOURCE),
        )),
    ),
)
