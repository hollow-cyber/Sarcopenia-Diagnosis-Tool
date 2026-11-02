"""不依赖页面的统一输入检查与诊断计算。

引擎只认识 Rule / Domain / Consensus 三个规则类型：它负责数值校验、
按阈值比较出各维度的 State，最后调用共识自己的 classify 函数得到结论。
各共识的阈值、比较符和分级逻辑都在 consensuses/<共识>.py 中。
"""

import math
from collections.abc import Mapping
from numbers import Real

from models import Consensus, Result, Rule, State, UNASSESSABLE


def is_missing(value: object) -> bool:
    """识别缺测；零值不是缺测，字符串 NaN 也不会伪装成空白。

    Args:
        value: 单个输入值。

    Returns:
        是否为 None、空字符串或数值 NaN。
    """
    # 先检查类型再调用 strip/isnan，利用 and 的短路行为避免对错误类型调用方法。
    # bool 是 int 的子类，因此不能把 True/False 当作普通数值处理。
    return (value is None or isinstance(value, str) and not value.strip()
            or isinstance(value, Real) and not isinstance(value, bool) and math.isnan(value))


def normalize_gender(value: object) -> str | None:
    """统一界面和文件中的性别表示，0 为男、1 为女。

    Args:
        value: M/F、男/女、male/female 或数值 0/1。

    Returns:
        M、F，或无效输入对应的 None。
    """
    if is_missing(value) or isinstance(value, bool):
        return None
    # 统一前后空白与英文大小写；文件中的数值 0.0/1.0 也使用同一套别名表。
    text = str(value).strip().upper()
    if text in ("M", "MALE", "男", "0", "0.0"):
        return "M"
    if text in ("F", "FEMALE", "女", "1", "1.0"):
        return "F"
    return None


def numeric_value(
        raw: object,
        rule: Rule,
) -> float:
    """检查数值类型、有限性、有效范围和整数约束。

    Args:
        raw: 非空的原始测量值。
        rule: 包含有效范围的测量定义。

    Returns:
        未经四舍五入的有效数值。

    Raises:
        ValueError: 测量值无效。
    """
    try:
        # float(True) 会得到 1.0，但这不是有效测量，所以转换前单独拒绝布尔值。
        if isinstance(raw, bool):
            raise ValueError
        value = float(raw)
    except (TypeError, ValueError, OverflowError):
        # 将不同来源的转换错误统一为可向使用者展示的提示。
        raise ValueError(f"{rule.label}必须为有效数值") from None
    if not math.isfinite(value):
        raise ValueError(f"{rule.label}必须为有限数值")
    # 有效范围与诊断阈值是两回事：例如握力需 >0 才能参与后续的 <28 判断。
    too_small = value < rule.minimum if rule.include_minimum else value <= rule.minimum
    if too_small or rule.maximum is not None and value > rule.maximum:
        relation = "≥" if rule.include_minimum else ">"
        upper = f"且 ≤ {rule.maximum:g}" if rule.maximum is not None else ""
        raise ValueError(f"{rule.label}需 {relation} {rule.minimum:g}{upper}")
    if rule.integer and not value.is_integer():
        raise ValueError(f"{rule.label}必须为整数")
    return value


def resolve_rules(
        consensus: Consensus,
        selections: Mapping[str, str] | None = None,
) -> dict[str, tuple[Rule, ...]]:
    """校验方案选择并解析参与测量的规则。

    Args:
        consensus: 共识定义。
        selections: 维度编号到互斥方案编号的映射。

    Returns:
        各维度当前使用的规则。

    Raises:
        ValueError: 维度或方案不存在。
    """
    selections = selections or {}
    # 方案解析交给维度定义：互斥项选一个，替代测量项全部保留。
    return {domain.key: domain.active_rules(selections.get(domain.key))
            for domain in consensus.domains}


def evaluate(
        consensus: Consensus,
        record: Mapping[str, object],
        selections: Mapping[str, str] | None = None,
) -> Result:
    """使用同一入口完成单人和批量诊断。

    缺测由各共识的分级函数判断是否妨碍结论；填写了非法值则明确报错，
    即使其他替代项目有效，也不会悄悄忽略非法输入继续给出正常结果。

    Args:
        consensus: 完整共识定义。
        record: 性别、可选年龄及已校正的测量值。
        selections: 各互斥维度使用的测量方案。

    Returns:
        诊断结论、计算依据及输入错误。

    Raises:
        ValueError: 共识配置或方案选择错误。
    """
    # 1. 先检查规则选择。配置错误直接抛出，不能伪装成某名受试者“资料不足”。
    active = resolve_rules(consensus, selections)
    issues: list[str] = []
    
    # 2. 标准化基本信息；只有确定性别和适用年龄组后，才能选出正确阈值。
    gender = normalize_gender(record.get("gender"))
    if gender is None:
        issues.append("性别未填写或无效，请使用男/女、M/F 或 0/1（0男，1女）")
        
    band = next(iter(consensus.age_bands))
    if consensus.requires_age:
        try:
            raw_age = record.get("age")
            # 排除布尔值；None、非数字文本等会在转换时进入下方异常处理。
            age = float(raw_age) if not isinstance(raw_age, bool) else math.nan
            if not math.isfinite(age) or not age.is_integer():
                raise ValueError
            matched = consensus.age_band_for(int(age))
            if matched is None:
                raise ValueError
            band = matched
        except (TypeError, ValueError, OverflowError):
            issues.append(f"年龄未填写或无效；本共识仅评估 {consensus.age_range_label}的整数年龄")

    # 在测量检查开始前记录“基本信息是否有效”。随后发现的测量错误不会改变
    # 这个标志，这样仍可继续检查其他项目，一次收集更多有用的输入错误。
    context_valid = not issues
    states: dict[str, State] = {}
    evidence: list[dict[str, object]] = []
    # 3. 按维度逐项检查数值，并保存有依据的正常／低下状态。
    for domain in consensus.domains:
        measured: list[State] = []
        for rule in active[domain.key]:
            raw = record.get(rule.field)
            if is_missing(raw):
                # 空白先保留为缺测，不在这里决定能否诊断；不同共识要求不同。
                continue
            try:
                value = numeric_value(raw, rule)
            except ValueError as exc:
                # 填写了无效值要明确报错；继续循环以便检查其余项目。
                issues.append(str(exc))
                continue
            if not context_valid:
                # 仍检查数值是否合法，但不在性别／年龄无效时猜测阈值。
                continue
            cutoff = rule.cutoff_for(band, gender)
            state = State.LOW if rule.compare.matches(value, cutoff) else State.NORMAL
            measured.append(state)
            evidence.append({
                "domain": domain.key,
                "rule": rule.key,
                "value": value,
                "cutoff": cutoff,
                "compare": rule.compare.value,
                "state": state.value,
                "source": rule.source,
            })
        # 无有效比较结果 → 缺测；任一有效项目异常 → 低下；否则 → 正常。
        states[domain.key] = (State.MISSING if not measured else
                              State.LOW if State.LOW in measured else State.NORMAL)
    if issues:
        # 4. 只要有已填写但非法的输入，整条记录就不输出确定诊断。
        return Result(UNASSESSABLE, "无法评估", evidence=tuple(evidence),
                      issues=tuple(issues))
    # 5. 维度状态组合交给共识自己的分级函数；引擎不按共识名称写分支。
    return consensus.classify(states)._replace(evidence=tuple(evidence))
