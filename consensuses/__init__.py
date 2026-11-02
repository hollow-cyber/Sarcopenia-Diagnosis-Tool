"""五个共识的注册表。

每个共识模块（awgs2014.py 等）在自己的文件里定义 SPEC（规则与阈值）、
classify（分级函数）和 render_form（输入界面）。本模块只按页面顺序注册，
并提供“共识 → 输入界面函数”的查找。
"""

from collections.abc import Callable

from consensuses import awgs2014, awgs2019, awgs2025, ewgsop2, fnih
from models import Consensus
from ui_controls import FormContext


# 此元组顺序就是页面上的共识顺序；默认选择第一个。
MODULES = (awgs2025, awgs2019, awgs2014, ewgsop2, fnih)
CONSENSUSES = tuple(module.SPEC for module in MODULES)


def renderer_for(consensus: Consensus) -> Callable[[FormContext], dict[str, object]]:
    """返回该共识自己的输入界面函数。

    Args:
        consensus: 已注册的共识。

    Returns:
        接收 FormContext、返回字段值映射的 render_form 函数。

    Raises:
        KeyError: 共识未注册。
    """
    for module in MODULES:
        if module.SPEC.key == consensus.key:
            return module.render_form
    raise KeyError(f"未注册的共识：{consensus.key}")
