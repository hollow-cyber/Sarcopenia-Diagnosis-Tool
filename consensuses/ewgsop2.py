"""EWGSOP2：Table 1 定义、Table 3 阈值、Figure 1 F-A-C-S 分级。

本文件包含该共识的全部内容：阈值与测量规则（SPEC）、分级函数（classify）
和输入界面（render_form）。阈值来源：Table 3；PDF 第9页，期刊页24。
分级顺序为力量 → 肌量 → 体力表现：力量低而肌量未证实为“可能肌少症”，
力量与肌量均低为肌少症，再合并体力表现低下为严重肌少症。
"""

from collections.abc import Mapping

from models import (Compare, Consensus, Domain, NEGATIVE, PROBABLE,
                    Rule, SARCOPENIA, SEVERE, State, Result, unavailable)
from ui_controls import FormContext


SOURCE = "Table 3；PDF 第9页，期刊页24"


def classify(states: Mapping[str, State]) -> Result:
    """按力量、肌量、体力表现依次确定当前能够支持的阶段。

    Args:
        states: strength、mass、performance 的正常／低下／缺测状态；
            具体测量值已由引擎按 SPEC 中的阈值比较完成。

    Returns:
        疑似、确诊、严重肌少症或其他测量结论。
    """
    strength = states["strength"]
    mass = states["mass"]
    performance = states["performance"]

    # 层级与分级流程一致：力量 → 肌量 → 体力表现。
    if strength == State.MISSING:
        return unavailable("肌肉力量")
    elif strength == State.NORMAL:
        return Result(NEGATIVE, "非肌少症")
    else:
        if mass == State.MISSING:
            return Result(PROBABLE, "可能肌少症", notes=(
                "肌肉质量未测试，尚不能确认诊断。",))
        elif mass == State.NORMAL:
            return Result(PROBABLE, "可能肌少症")
        else:
            # 进入此层时力量与肌量均低，确诊已成立；继续评估严重程度。
            if performance == State.MISSING:
                return Result(SARCOPENIA, "肌少症", notes=(
                    "体力表现项目均未测试，严重程度未评估。",))
            elif performance == State.NORMAL:
                return Result(SARCOPENIA, "肌少症")
            else:
                return Result(SEVERE, "严重肌少症")


def render_form(ctx: FormContext) -> dict[str, object]:
    """绘制 EWGSOP2 的输入界面（手动数值或批量列名）。

    三个维度各一个折叠面板；力量与体力表现是替代测量，全部并排显示；
    肌肉质量按仪器／校正方式在四个互斥方案中选择一个。

    Args:
        ctx: 表单上下文，提供面板、方案选择和输入控件。

    Returns:
        字段名到输入值（或批量列名）的映射。
    """
    values: dict[str, object] = {}
    strength = SPEC.domain("strength")
    with ctx.panel(strength):
        # 替代测量：握力与 5 次起坐并排显示，任一有效即可参与判断。
        values.update(ctx.inputs(strength.rules))
    mass = SPEC.domain("mass")
    with ctx.panel(mass):
        rule = ctx.select_indicator(mass)
        values.update(ctx.inputs((rule,)))
    performance = SPEC.domain("performance")
    with ctx.panel(performance):
        # 替代测量：四项都显示，使用者只填其中一项或多项也可以。
        values.update(ctx.inputs(performance.rules))
    return values


# 规则定义：阈值、比较符、单位都集中在这里；修改阈值只需改本文件。
# 阈值与运算符来自Table 3；项目对400米非数值情况的处理另在notes中说明。
SPEC = Consensus(
    key="ewgsop2",
    title="EWGSOP2",
    doi="10.1093/ageing/afy169",
    source_pdf="Sarcopenia revised European consensus on definition and diagnosis.pdf",
    images=("EWGSOP2 cutoff.png", "EWGSOP2 algorithm.png"),
    classify=classify,
    # notes=("肌量使用 Table 3 的 ASM 或 ASM/身高²，不使用未列出阈值的其他校正方案。",
    #        "多个替代测量同时提供时，本工具以任一有效测量异常判定该维度低下。",
    #        "400米测试仅接收有效完成用时；未完成或未填写不据此推断体力低下。"),
    domains=(
        # 握力与起坐是力量的替代测量。注意起坐严格 >15秒，等于15秒不算低下。
        Domain("strength", "肌肉力量", any_of=True, rules=(
            Rule(key="handgrip", field="hgs", label="握力", unit="kg",
                 compare=Compare.LT, cutoffs={"all": (27, 16)}, source=SOURCE),
            Rule(key="chair_stand", field="chair_stand", label="5次起坐用时", unit="秒",
                 compare=Compare.GT, cutoffs={"all": (15, 15)}, source=SOURCE),
        )),
        # 肌量分为身高²校正指数和绝对ASM；只有选定方案的单位及阈值会参与计算。
        # DXA/BIA方案输入均为四肢肌量，不把BIA全身肌量直接当作ASM。
        Domain("mass", "肌肉质量", default_rule="dxa_height", rules=(
            Rule(key="dxa_height", field="muscle_mass", label="ASM/身高²", unit="kg/m²",
                 instrument="DXA", adjustment="身高²", compare=Compare.LT,
                 cutoffs={"all": (7.0, 5.5)}, source=SOURCE),
            Rule(key="bia_height", field="muscle_mass", label="ASM/身高²", unit="kg/m²",
                 instrument="BIA", adjustment="身高²", compare=Compare.LT,
                 cutoffs={"all": (7.0, 5.5)}, source=SOURCE),
            Rule(key="dxa_absolute", field="muscle_mass", label="四肢肌肉质量 ASM", unit="kg",
                 instrument="DXA", compare=Compare.LT,
                 cutoffs={"all": (20, 15)}, source=SOURCE),
            Rule(key="bia_absolute", field="muscle_mass", label="四肢肌肉质量 ASM", unit="kg",
                 instrument="BIA", compare=Compare.LT,
                 cutoffs={"all": (20, 15)}, source=SOURCE),
        )),
        # 四项任一有效异常即为低下；页面依据数量自动排成两行两列。
        # 400米使用秒作为输入单位，因此原表6分钟在此写成360秒。
        Domain("performance", "体力表现", any_of=True, rules=(
            Rule(key="gait_speed", field="gait_speed", label="步速", unit="m/s",
                 compare=Compare.LE, cutoffs={"all": (0.8, 0.8)}, source=SOURCE),
            Rule(key="sppb", field="sppb", label="简易躯体功能评分 SPPB", unit="分",
                 compare=Compare.LE, cutoffs={"all": (8, 8)}, source=SOURCE,
                 integer=True, include_minimum=True, maximum=12,
                 placeholder="请输入0–12分"),
            Rule(key="tug", field="tug", label="起立行走测试 TUG", unit="秒",
                 compare=Compare.GE, cutoffs={"all": (20, 20)}, source=SOURCE),
            # 按项目要求只处理数值，不把“未完成”编码为零或任意超阈值时间。
            Rule(key="walk_400", field="walk_400", label="400米步行完成用时", unit="秒",
                 compare=Compare.GE, cutoffs={"all": (360, 360)}, source=SOURCE),
        )),
    ),
)
