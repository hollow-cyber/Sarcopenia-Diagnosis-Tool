"""共识规则与诊断结果的精简数据结构。

本模块只描述“规范限定”，不包含任何 Streamlit 代码，总共 6 个类型：

- Compare：数值与阈值的比较关系。
- State：维度评估的三种状态。
- Rule：一项测量（输入字段、单位、比较符、男女阈值、有效范围）。
- Domain：一个评估维度；规则可互斥（选一种）或替代（任一有效即算）。
- Consensus：一个共识（年龄分层、评估维度、分级函数与原文信息）。
- Result：一次诊断的结论、逐项依据和输入问题。

阈值统一写成“年龄组 → (男性, 女性)”的字典，键与 Consensus.age_bands 一致。
每个共识文件再用这些类型组装自己的规则，并在同一文件里写分级函数和输入界面。
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
import operator
from typing import NamedTuple


# 稳定的结果代码：页面据此选择颜色，不依赖中文结论文字。
NEGATIVE = "negative"
POSSIBLE = "possible"
PROBABLE = "probable"
SARCOPENIA = "sarcopenia"
SEVERE = "severe"
UNASSESSABLE = "unassessable"


class Compare(str, Enum):
    """数值与阈值的比较关系；成员值同时用作页面显示的符号。

    Attributes:
        LT: 小于阈值算低下。
        LE: 小于等于阈值算低下。
        GT: 大于阈值算低下。
        GE: 大于等于阈值算低下。
    """

    LT = "<"
    LE = "≤"
    GT = ">"
    GE = "≥"

    def matches(
            self,
            value: float,
            cutoff: float,
    ) -> bool:
        """判断测量值是否达到该项“低下”标准。

        Args:
            value: 有效测量值。
            cutoff: 当前年龄组、性别对应的阈值。

        Returns:
            测量值是否符合该比较关系。
        """
        # 用函数表避免 if/elif 分支；dict 的键是枚举成员，值是 operator 函数。
        operations = {
            Compare.LT: operator.lt,
            Compare.LE: operator.le,
            Compare.GT: operator.gt,
            Compare.GE: operator.ge,
        }
        return operations[self](value, cutoff)


class State(str, Enum):
    """维度的三种评估状态；缺测不等同于正常。

    Attributes:
        LOW: 该维度至少一项有效测量低于阈值。
        NORMAL: 该维度有有效测量，且都不低于阈值。
        MISSING: 没有能参与判断的有效测量。
    """

    LOW = "low"
    NORMAL = "normal"
    MISSING = "missing"


@dataclass(frozen=True)
class Rule:
    """一项完整的测量：怎么输入、怎么判低下、阈值与有效范围。

    Attributes:
        key: 共识内唯一的方案编号。
        field: 受试者记录中的字段名；互斥方案可以共用一个字段。
        label: 页面输入框名称，例如 ASM/身高²。
        unit: 输入值的单位，必须与阈值单位一致。
        compare: 哪一种比较关系表示该项低下。
        cutoffs: 年龄组编号 → (男性阈值, 女性阈值)。
        source: 原文表格或页码定位。
        instrument: 测量仪器；None 表示不区分仪器。
        adjustment: 校正方式说明；页面据此提示输入已校正比值。
        recommendation: “推荐／备选”等方案标记；空字符串表示不标记。
        integer: 是否只接受整数（例如 SPPB）。
        minimum: 有效下限；多数测量必须大于零。
        include_minimum: 下限本身是否属于有效范围。
        maximum: 有效上限；None 表示不另设上限。
        placeholder: 数字输入框留空时的提示。
        column_weight: 该控件在同一行中占据的相对宽度。
    """

    key: str
    field: str
    label: str
    unit: str
    compare: Compare
    cutoffs: Mapping[str, tuple[float, float]]
    source: str
    instrument: str | None = None
    adjustment: str = "无"
    recommendation: str = ""
    integer: bool = False
    minimum: float = 0.0
    include_minimum: bool = False
    maximum: float | None = None
    placeholder: str = "请输入数值"
    column_weight: float = 1.0

    def cutoff_for(
            self,
            age_band: str,
            gender: str,
    ) -> float:
        """取得指定年龄组与性别的阈值。

        Args:
            age_band: 年龄组编号，必须出现在 cutoffs 中。
            gender: 标准化性别，M 或 F。

        Returns:
            该年龄组、性别对应的阈值。
        """
        male, female = self.cutoffs[age_band]
        return male if gender == "M" else female


@dataclass(frozen=True)
class Domain:
    """一个评估维度（肌肉力量、肌肉质量或体力表现）。

    Attributes:
        key: 内部维度编号，例如 strength、mass、performance。
        label: 页面和缺测提示使用的中文名称。
        rules: 该维度允许使用的全部测量方案。
        any_of: True 表示替代测量（任一有效异常即低下）；
            False 表示互斥方案（页面选择仪器／校正方式后只用一个）。
        default_rule: 互斥方案的默认编号；替代测量维度不使用。
    """

    key: str
    label: str
    rules: tuple[Rule, ...]
    any_of: bool = False
    default_rule: str = ""

    def active_rules(
            self,
            selected: str | None = None,
    ) -> tuple[Rule, ...]:
        """解析当前实际参与评估的规则。

        Args:
            selected: 互斥方案编号；未提供时使用默认方案。

        Returns:
            一个互斥方案，或全部可替代测量。

        Raises:
            ValueError: 调用了未定义的方案。
        """
        if self.any_of:
            # 替代测量的含义是保留全部规则，不指定互斥方案。
            return self.rules
        key = selected or self.default_rule
        matches = tuple(rule for rule in self.rules if rule.key == key)
        if len(matches) != 1:
            raise ValueError(f"{self.label}的方案无效：{key}")
        return matches


@dataclass(frozen=True)
class Consensus:
    """可被页面、单人评估及批量处理共同消费的完整共识定义。

    Attributes:
        key: 共识内部编号，用于注册和区分页面状态。
        title: 页面上的共识名称。
        doi: 原文 DOI；界面由此生成文献链接。
        source_pdf: ref 目录中的原文 PDF 文件名。
        images: img 目录中按显示顺序排列的截图文件名。
        domains: 参与评估的维度；页面也按此顺序生成板块。
        classify: 接收各维度 State、返回 Result 的函数。
        notes: 展示在原文折叠框中的适用说明。
        age_bands: 年龄组编号 → (最小年龄, 上界不含)；无上限用 None。
        requires_age: 是否必须输入年龄并按年龄组选择阈值。
        image_captions: 与 images 按位置对应的图注；空元组表示不提供。
    """

    key: str
    title: str
    doi: str
    source_pdf: str
    images: tuple[str, ...]
    domains: tuple[Domain, ...]
    classify: Callable[[Mapping[str, State]], "Result"]
    notes: tuple[str, ...] = ()
    age_bands: Mapping[str, tuple[int, int | None]] = field(
        default_factory=lambda: {"all": (0, None)})
    requires_age: bool = False
    image_captions: tuple[str | None, ...] = ()

    def domain(
            self,
            key: str,
    ) -> Domain:
        """按编号取出一个评估维度。

        Args:
            key: 维度编号。

        Returns:
            对应的维度定义。

        Raises:
            KeyError: 该共识没有此维度。
        """
        for domain in self.domains:
            if domain.key == key:
                return domain
        raise KeyError(f"{self.title} 没有编号为 {key} 的评估维度")

    def age_band_for(
            self,
            age: float,
    ) -> str | None:
        """返回年龄所属的年龄组编号。

        Args:
            age: 完整年龄，单位为岁。

        Returns:
            年龄组编号；年龄不在任何组内时返回 None。
        """
        # age_bands 按年龄递增书写，区间左闭右开：[50, 65) 与 [65, +∞)。
        for key, (minimum, maximum) in self.age_bands.items():
            if age >= minimum and (maximum is None or age < maximum):
                return key
        return None

    @property
    def context_fields(self) -> tuple[str, ...]:
        """返回页面和批量映射需要的基本信息字段。

        Returns:
            性别；需要年龄分层时再加上年龄字段。
        """
        return ("gender", "age") if self.requires_age else ("gender",)

    @property
    def age_range_label(self) -> str:
        """从年龄区间生成适用范围文字。

        Returns:
            例如 ≥50 岁，或 50–79 岁。
        """
        bands = list(self.age_bands.values())
        first_minimum = bands[0][0]
        last_maximum = bands[-1][1]
        return ("≥{} 岁".format(first_minimum) if last_maximum is None else
                "{}–{} 岁".format(first_minimum, last_maximum - 1))


class Result(NamedTuple):
    """一次诊断的结论、逐项比较依据和输入问题。

    Attributes:
        code: 稳定的结果代码（NEGATIVE、SARCOPENIA 等模块常量）。
        label: 给使用者看的结论文字。
        notes: 与当前结论有关的补充说明。
        evidence: 每个有效比较的字典（domain、rule、value、cutoff、compare、state、source）。
        issues: 非法数值、无效性别等输入错误。
    """

    code: str
    label: str
    notes: tuple[str, ...] = ()
    evidence: tuple[dict[str, object], ...] = ()
    issues: tuple[str, ...] = ()


def unavailable(*labels: str) -> Result:
    """生成必要维度缺测时的“无法评估”结论。

    Args:
        *labels: 当前结论必需、但没有任何有效数据的维度名称。

    Returns:
        无法评估的结果，说明所缺维度。
    """
    return Result(UNASSESSABLE, "无法评估", notes=tuple(
        f"{label}项目无有效数据，无法评估" for label in labels))
