"""让测试能 import 实验根目录下的模块。

模块名（``tools``、``providers`` 等）在本仓库的其他章节里也出现过，整仓一起跑
pytest 时可能先被别的章节占了位，所以这里顺手把不属于本目录的同名模块清掉。
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _name in ("neutral_trace", "providers", "renderers", "streaming", "tools"):
    _mod = sys.modules.get(_name)
    if _mod is not None and not str(getattr(_mod, "__file__", "")).startswith(str(ROOT)):
        del sys.modules[_name]
