"""AWGS 2019：临床确诊分级及社区／基层初评的可能肌少症识别。

本文件包含该共识的全部内容：阈值与测量规则（SPEC）、分级函数（classify）
和输入界面（render_form）。阈值来源：PDF 第2页摘要、第3页 Figure 1。
"""

from collections.abc import Mapping

from models import (Compare, Consensus, Domain, NEGATIVE, POSSIBLE, Rule,
                    SARCOPENIA, SEVERE, State, Result, unavailable)
from ui_controls import FormContext


SOURCE = "PDF 第2页摘要、第3页 Figure 1"


def classify(states: Mapping[str, State]) -> Result:
    """优先识别确诊分级，未达到确诊条件时保留可能肌少症提示。

    肌量低且力量或体力表现低为确诊，三者均低为严重肌少症。
    肌量正常或未测、但力量或体力表现已低下时，输出“可能肌少症”。

    Args:
        states: mass、strength、performance 的低下／正常／缺测状态；
            具体测量值已由引擎按 SPEC 中的阈值比较完成。

    Returns:
        严重肌少症、肌少症、可能肌少症、非肌少症或必要项目缺测提示。
    """
    mass = states["mass"]
    strength = states["strength"]
    performance = states["performance"]

    # 第一层明确肌量状态：未测／正常时识别可能肌少症，低下时进入确诊分级。
    if mass == State.MISSING:
        if strength == State.LOW or performance == State.LOW:
            return Result(POSSIBLE, "可能肌少症", notes=(
                "肌量无效或未测，建议补充肌量测量以明确诊断。",))
        return unavailable("肌肉质量")
    elif mass == State.NORMAL:
        if strength == State.LOW or performance == State.LOW:
            return Result(POSSIBLE, "可能肌少症", notes=(
                "肌量已测，但未低于所选方案阈值。",))
        return Result(NEGATIVE, "非肌少症")
    else:
        # 肌量低下：肌量与力量均低已确诊，体力表现决定是否升级为严重。
        if strength == State.LOW:
            if performance == State.LOW:
                return Result(SEVERE, "严重肌少症")
            elif performance == State.NORMAL:
                return Result(SARCOPENIA, "肌少症")
            else:
                return Result(SARCOPENIA, "肌少症", notes=(
                    "体力表现项目均无效或未测试，肌少症严重程度未完全评估",))
        elif strength == State.NORMAL:
            if performance == State.LOW:
                return Result(SARCOPENIA, "肌少症")
            elif performance == State.NORMAL:
                return Result(NEGATIVE, "非肌少症")
            else:
                return unavailable("体力表现")
        else:
            # 力量未测：肌量与体力表现均低也能确诊；否则不能完成严重程度评估。
            if performance == State.LOW:
                return Result(SARCOPENIA, "肌少症", notes=(
                    "肌肉力量项目无效或未测试，肌少症严重程度未完全评估",))
            elif performance == State.NORMAL:
                return unavailable("肌肉力量")
            else:
                return unavailable("肌肉力量", "体力表现")


def render_form(ctx: FormContext) -> dict[str, object]:
    """绘制 AWGS 2019 的输入界面（手动数值或批量列名）。

    三个维度各一个折叠面板；肌肉质量按仪器／校正方式选择一种方案；
    体力表现三项为替代测量，全部并排显示。

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
        # 替代测量：三项都显示，使用者只填其中一项或多项也可以。
        # 手动输入保持三列；批量映射时列名标签较长，改为两列避免标签换行。
        values.update(ctx.inputs(performance.rules,
                                 max_columns=2 if ctx.batch else 3))
    return values


# 规则定义：阈值、比较符、单位都集中在这里；修改阈值只需改本文件。
SPEC = Consensus(
    key="awgs_2019",
    title="AWGS 2019",
    doi="10.1016/j.jamda.2019.12.012",
    source_pdf="Asian Working Group for Sarcopenia 2019 Consensus Update on Sarcopenia Diagnosis and Treatment.pdf",
    images=("AWGS 2019 algorithm.png",),
    classify=classify,
    # notes=("‘可能肌少症’用于社区／基层初评：力量或体力表现低下、尚未达到肌少症确诊条件；"
    #        "肌量未测或所测肌量正常时均可输出此提示。",),
    domains=(
        # all 年龄组不强制收集年龄；每项阈值写成 (男性, 女性)。
        Domain("strength", "肌肉力量", default_rule="handgrip", rules=(
            Rule(key="handgrip", field="hgs", label="握力", unit="kg",
                 compare=Compare.LT, cutoffs={"all": (28, 18)}, source=SOURCE),
        )),
        # 默认 BIA、身高²校正；选定仪器后，方案同时决定输入标签和肌量阈值。
        Domain("mass", "肌肉质量", default_rule="bia_height", rules=(
            Rule(key="dxa_height", field="muscle_mass", label="ASM/身高²", unit="kg/m²",
                 instrument="DXA", adjustment="身高²", compare=Compare.LT,
                 cutoffs={"all": (7.0, 5.4)}, source=SOURCE),
            Rule(key="bia_height", field="muscle_mass", label="ASM/身高²", unit="kg/m²",
                 instrument="BIA", adjustment="身高²", compare=Compare.LT,
                 cutoffs={"all": (7.0, 5.7)}, source=SOURCE),
        )),
        # 三项是替代测量：至少一项有效即可评估该维度，任一异常即为低下。
        # 比较边界各不相同：步速 <1.0，起坐 ≥12，SPPB ≤9，不能统一成“小于”。
        Domain("performance", "体力表现", any_of=True, rules=(
            Rule(key="gait_speed", field="gait_speed", label="6米步速", unit="m/s",
                 compare=Compare.LT, cutoffs={"all": (1.0, 1.0)}, source=SOURCE),
            Rule(key="chair_stand", field="chair_stand", label="5次起坐用时", unit="秒",
                 compare=Compare.GE, cutoffs={"all": (12, 12)}, source=SOURCE),
            # SPPB 有效范围为 0–12 的整数，0 分是有效数据，不是“未填写”。
            Rule(key="sppb", field="sppb", label="简易躯体功能评分 SPPB", unit="分",
                 compare=Compare.LE, cutoffs={"all": (9, 9)}, source=SOURCE,
                 integer=True, include_minimum=True, maximum=12,
                 placeholder="请输入0–12分", column_weight=1.25),
        )),
    ),
)
