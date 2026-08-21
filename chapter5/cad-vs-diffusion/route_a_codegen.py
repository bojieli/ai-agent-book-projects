"""路线 A：Agent（Kimi）编写 CadQuery 代码 → 真实执行 → 导出 STEP/STL。

变更请求（M5→M6）时只需程序化修补 PARAMS 中的一个参数并重新执行，
无需再次调用 LLM——这正是代码生成路线要展示的修改成本。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

import llm
from flange_spec import FLANGE_SPEC_TEXT, SPEC_M5
from receipts import utc_now

CODEGEN_PROMPT = f"""你是机械 CAD 工程师。请用 Python CadQuery 库编写代码，构造如下零件：

规格：{FLANGE_SPEC_TEXT}

硬性要求：
1. 文件顶部用一个名为 PARAMS 的 dict 集中全部尺寸参数（单位 mm），键名固定为：
   outer_diameter、thickness、hole_count、hole_diameter、hole_circle_diameter。
   值分别为 {SPEC_M5["outer_diameter_mm"]}、{SPEC_M5["thickness_mm"]}、{SPEC_M5["hole_count"]}、{SPEC_M5["hole_diameter_mm"]}、{SPEC_M5["hole_circle_diameter_mm"]}。
2. 零件轴线为 Z 轴且过原点，底面在 z=0 平面。
3. 安装孔为通孔，绕 Z 轴在孔位圆上均布。
4. 最终实体赋值给变量 result（cq.Workplane 或 cq.Shape 均可）。
5. 只做建模：不要读写文件、不要导出、不要打印，只 import cadquery 及标准库。

只输出一个 ```python 代码块，不要任何其他解释。"""

_CQ_DRIVER = '''import sys, runpy
import cadquery as cq
src, step_path, stl_path = sys.argv[1:4]
ns = runpy.run_path(src)
result = ns["result"]
cq.exporters.export(result, step_path)
cq.exporters.export(result, stl_path)
print("exported", step_path, stl_path)
'''


def generate_cadquery_code(book, out_dir: Path) -> Path:
    """调用 Kimi 生成 CadQuery 源码并落盘，返回源码路径。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    content, _usage = llm.kimi_chat(
        [{"role": "user", "content": CODEGEN_PROMPT}],
        book, name="route-a-codegen-m5")
    code = llm.extract_code_block(content)
    src = out_dir / "flange_m5.py"
    src.write_text(code)
    return src


def execute_cadquery(src: Path, step_path: Path, stl_path: Path, book=None,
                     name: str = "route-a-execute") -> None:
    """在子进程中真实执行 CadQuery 代码并导出 STEP/STL。"""
    driver = src.parent / "_cq_driver.py"
    driver.write_text(_CQ_DRIVER)
    started = utc_now()
    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, str(driver), str(src), str(step_path), str(stl_path)],
        capture_output=True, text=True, timeout=300,
    )
    ended = utc_now()
    if book is not None:
        book.record(name, provider="local", endpoint="subprocess:cadquery",
                    model=f"cadquery-exec",
                    request={"source": str(src), "step": str(step_path), "stl": str(stl_path)},
                    response={"returncode": proc.returncode,
                              "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]},
                    started_utc=started, ended_utc=ended,
                    latency_ms=int((time.time() - t0) * 1000),
                    status="ok" if proc.returncode == 0 else "error")
    if proc.returncode != 0:
        raise RuntimeError(f"CadQuery 执行失败: {proc.stderr[-2000:]}")


def patch_hole_diameter(src_m5: Path, dst_m6: Path, new_diameter: float) -> dict:
    """变更请求的实现：只改 PARAMS 中 hole_diameter 一个参数。返回修补记录。"""
    code = src_m5.read_text()
    pattern = re.compile(r"(hole_diameter[\"']?\s*:\s*)([\d.]+)")
    m = pattern.search(code)
    if not m:
        raise RuntimeError("生成的代码中找不到 PARAMS.hole_diameter 参数，无法单点修补")
    old = m.group(2)
    patched = pattern.sub(rf"\g<1>{new_diameter}", code, count=1)
    dst_m6.write_text(patched)
    return {"file": str(dst_m6), "parameter": "PARAMS.hole_diameter",
            "old_value": old, "new_value": new_diameter, "lines_changed": 1,
            "llm_calls": 0}
