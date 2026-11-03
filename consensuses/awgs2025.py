"""AWGS 2025：按力量与肌量两项判断，不增加体力表现或严重程度分级。

本文件包含该共识的全部内容：阈值与测量规则（SPEC）、分级函数（classify）
和输入界面（render_form）。阈值来源：Table 2；PDF 第4页，期刊页2167。
"""

from collections.abc import Mapping

from models import (Compare, Consensus, Domain, NEGATIVE, POSSIBLE, Rule,
                    SARCOPENIA, State, Result, unavailable)
from ui_controls import FormContext


# 下方只纳入诊断需要的力量和肌量；原表中的体力表现指标不生成诊断控件。
SOURCE = "Table 2；PDF 第4页，期刊页2167"


def classify(states: Mapping[str, State]) -> Result:
    """区分未测肌量与实测肌量正常，不沿用旧版的混合标签。

    Args:
        states: strength、mass 到 State 的映射；不包含体力表现维度。

    Returns:
        测量结论；可能肌少症仅为无肌量测量时的进一步评估提示。
    """
    strength = states["strength"]
    mass = states["mass"]

    # 第一层只判断力量；所有肌量分支都明确放在“力量低下”的节点中。
    if strength == State.MISSING:
        return unavailable("肌肉力量")
    elif strength == State.NORMAL:
        return Result(NEGATIVE, "非肌少症")
    else:
        if mass == State.MISSING:
            # 力量低下、肌量未测：只能给出进一步评估提示。
            return Result(POSSIBLE, "可能肌少症", notes=("握力低下、肌量无效或未测。",))
        elif mass == State.NORMAL:
            # 力量低下、肌量正常：不满足两者均低的诊断条件。
            return Result(NEGATIVE, "非肌少症", notes=("握力低下，但肌量未低于诊断阈值。",))
        else:
            # 力量与肌量均低：确诊
            return Result(SARCOPENIA, "肌少症")


def render_form(ctx: FormContext) -> dict[str, object]:
    """绘制 AWGS 2025 的输入界面（手动数值或批量列名）。

    两个维度各一个折叠面板；肌肉质量按仪器与校正方式从四个互斥方案中选择一个，
    输入已经按所选方案校正，无法再加一次校正。

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
    return values


# 规则定义：阈值、比较符、单位都集中在这里；修改阈值只需改本文件。
# 左闭右开：[50,65)、[65,+∞)，因此65岁会自动使用第二套阈值。
SPEC = Consensus(
    key="awgs_2025",
    title="AWGS 2025",
    doi="10.1038/s43587-025-01004-y",
    source_pdf="A focus shift from sarcopenia to muscle health in the Asian Working Group for Sarcopenia 2025 Consensus Update.pdf",
    images=("AWGS 2025 cutoff.png", "AWGS 2025 algorithm.png"),
    classify=classify,
    age_bands={"50-64": (50, 65), "65+": (65, None)},
    requires_age=True,
    notes=("仅评估 ≥50 岁人群；体力表现为结局指标，不参与本版诊断。",
           "可能肌少症仅用于握力低下且肌量未测的情况，不是严重程度分级。"),
    domains=(
        # 每项阈值按年龄组编号匹配，依次给出男性、女性阈值。
        Domain("strength", "肌肉力量", default_rule="handgrip", rules=(
            Rule(key="handgrip", field="hgs", label="握力", unit="kg", compare=Compare.LT,
                 cutoffs={"50-64": (34, 20), "65+": (28, 18)}, source=SOURCE),
        )),
        # 仪器×校正方式组成四个互斥方案；输入已经校正，不能再按身高或BMI除一次。
        # 四个方案共用muscle_mass字段；页面切换方案时会使用不同控件key避免误用旧值。
        Domain("mass", "肌肉质量", default_rule="bia_height", rules=(
            Rule(key="dxa_height", field="muscle_mass", label="ASM/身高²", unit="kg/m²",
                 instrument="DXA", adjustment="身高²", compare=Compare.LT,
                 cutoffs={"50-64": (7.2, 5.5), "65+": (7.0, 5.4)}, source=SOURCE),
            Rule(key="bia_height", field="muscle_mass", label="ASM/身高²", unit="kg/m²",
                 instrument="BIA", adjustment="身高²", compare=Compare.LT,
                 cutoffs={"50-64": (7.6, 5.7), "65+": (7.0, 5.7)}, source=SOURCE),
            Rule(key="dxa_bmi", field="muscle_mass", label="ASM/BMI", unit="m²",
                 instrument="DXA", adjustment="BMI", compare=Compare.LT,
                 cutoffs={"50-64": (0.80, 0.55), "65+": (0.73, 0.52)}, source=SOURCE),
            Rule(key="bia_bmi", field="muscle_mass", label="ASM/BMI", unit="m²",
                 instrument="BIA", adjustment="BMI", compare=Compare.LT,
                 cutoffs={"50-64": (0.90, 0.63), "65+": (0.83, 0.57)}, source=SOURCE),
        )),
    ),
)
