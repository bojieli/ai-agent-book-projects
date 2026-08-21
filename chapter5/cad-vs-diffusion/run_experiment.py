"""实验 5-7 主流程：CAD 代码生成 vs 3D 生成模型，正式运行并落盘 manifest。

用法：
    python run_experiment.py            # 全流程（打真实外部 API）
产物：
    output/                             网格、图片、生成的源码
    validation/runs/<run_id>/           manifest.json + receipts/*.json
"""
from __future__ import annotations

import datetime
import json
import sys
import traceback
from pathlib import Path

import control_plant
import gemini_image
import measure
import route_a_codegen
import route_b_gen3d
from flange_spec import (CHANGE_REQUEST_TEXT, FLANGE_SPEC_TEXT, PLANT_PROMPT,
                         SPEC_M5, SPEC_M6)
from receipts import ReceiptBook, sha256_file, utc_now
from validate_manifest import validate_manifest

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"

# 路线 A 验收公差（mm）：CadQuery 精确建模应远小于此
ROUTE_A_TOL_MM = 0.05


def _artifact_entry(path: Path) -> dict:
    return {"sha256": sha256_file(path), "bytes": path.stat().st_size}


def _collect_artifacts(paths) -> dict:
    return {str(p.relative_to(ROOT)): _artifact_entry(p) for p in paths if p.exists()}


def _drift(before: dict, after: dict, keys=None) -> dict:
    """变更请求前后，其余尺寸的漂移量（键为测量字段名）。"""
    keys = keys or ["outer_diameter_mm", "thickness_mm", "hole_count_detected",
                    "hole_circle_diameter_mm", "hole_diameter_mm"]
    out = {}
    for k in keys:
        b, a = before.get(k), after.get(k)
        out[k] = {"before": b, "after": a,
                  "drift": (round(a - b, 4) if isinstance(a, (int, float))
                            and isinstance(b, (int, float)) else None)}
    return out


def run_route_a(book: ReceiptBook) -> dict:
    out_a = OUT / "route_a"
    out_a.mkdir(parents=True, exist_ok=True)

    src_m5 = route_a_codegen.generate_cadquery_code(book, out_a)
    step_m5, stl_m5 = out_a / "flange_m5.step", out_a / "flange_m5.stl"
    route_a_codegen.execute_cadquery(src_m5, step_m5, stl_m5, book, "route-a-execute-m5")
    m5 = measure.measure_flange(measure.load_mesh(str(stl_m5)), SPEC_M5)

    # 变更请求：单参数修补，零次 LLM 调用
    src_m6 = out_a / "flange_m6.py"
    patch = route_a_codegen.patch_hole_diameter(
        src_m5, src_m6, SPEC_M6["hole_diameter_mm"])
    step_m6, stl_m6 = out_a / "flange_m6.step", out_a / "flange_m6.stl"
    route_a_codegen.execute_cadquery(src_m6, step_m6, stl_m6, book, "route-a-execute-m6")
    m6 = measure.measure_flange(measure.load_mesh(str(stl_m6)), SPEC_M6)

    within_tol = all(
        abs(d["abs_error_mm"]) <= ROUTE_A_TOL_MM
        for d in (m5["deviations"]["outer_diameter_mm"],
                  m5["deviations"]["thickness_mm"],
                  m5["deviations"]["hole_diameter_mm"],
                  m5["deviations"]["hole_circle_diameter_mm"])
    ) and m5["deviations"]["hole_count"]["match"]

    return {
        "status": "completed",
        "approach": f"Kimi ({route_a_codegen.llm.CODEGEN_MODEL}) 生成 CadQuery 代码，本地真实执行导出 STEP/STL",
        "initial": {
            "source_code": str(src_m5.relative_to(ROOT)),
            "artifacts": [str(p.relative_to(ROOT)) for p in (step_m5, stl_m5)],
            "measurement": m5,
        },
        "after_change": {
            "source_code": str(src_m6.relative_to(ROOT)),
            "artifacts": [str(p.relative_to(ROOT)) for p in (step_m6, stl_m6)],
            "measurement": m6,
        },
        "change_cost": patch,
        "drift_on_unchanged_dims": _drift(m5, m6),
        "_within_tol": within_tol,
        "_files": [src_m5, src_m6, step_m5, stl_m5, step_m6, stl_m6,
                   out_a / "_cq_driver.py"],
    }


def run_route_b(book: ReceiptBook) -> dict:
    out_b = OUT / "route_b"
    out_b.mkdir(parents=True, exist_ok=True)

    img_m5 = gemini_image.generate_image(
        route_b_gen3d.FLANGE_IMAGE_PROMPT_M5, out_b / "flange_m5_input.png",
        book, "route-b-text2image-m5")
    glb_m5 = route_b_gen3d.hunyuan_image_to_3d(
        img_m5, out_b / "flange_m5.glb", book, "route-b-shape-gen-m5")
    m5 = measure.measure_flange(measure.load_mesh(str(glb_m5)), SPEC_M5)

    # 变更请求：只能改提示词整体重新生成
    img_m6 = gemini_image.generate_image(
        route_b_gen3d.FLANGE_IMAGE_PROMPT_M6, out_b / "flange_m6_input.png",
        book, "route-b-text2image-m6")
    glb_m6 = route_b_gen3d.hunyuan_image_to_3d(
        img_m6, out_b / "flange_m6.glb", book, "route-b-shape-gen-m6")
    m6 = measure.measure_flange(measure.load_mesh(str(glb_m6)), SPEC_M6)

    return {
        "status": "completed",
        "approach": (
            f"两段式 text-to-3D：Gemini ({gemini_image.IMAGE_MODEL}) 由规格文本生成零件图，"
            f"再经 Hugging Face 公共 Space {route_b_gen3d.HF_SPACE} 的 /shape_generation 图生 3D（GLB）"
        ),
        "initial": {
            "input_image": str(img_m5.relative_to(ROOT)),
            "artifacts": [str(glb_m5.relative_to(ROOT))],
            "measurement": m5,
        },
        "after_change": {
            "input_image": str(img_m6.relative_to(ROOT)),
            "artifacts": [str(glb_m6.relative_to(ROOT))],
            "measurement": m6,
        },
        "change_cost": {
            "description": "修改提示词后两条流水线（文生图 + 图生 3D）整体重跑",
            "llm_calls": 2, "parameter_patch": None,
        },
        "drift_on_unchanged_dims": _drift(m5, m6),
        "_files": [img_m5, glb_m5, img_m6, glb_m6],
    }


def run_control_group(book: ReceiptBook) -> dict:
    out_c = OUT / "control"
    out_c.mkdir(parents=True, exist_ok=True)
    proc_png = control_plant.draw_procedural_plant(out_c / "plant_procedural.png")
    gen_png = gemini_image.generate_image(
        PLANT_PROMPT + "，照片级真实感", out_c / "plant_generative.png",
        book, "control-plant-text2image")
    verdict = control_plant.judge_plants(proc_png, gen_png, book)
    return {
        "task": PLANT_PROMPT,
        "procedural_image": str(proc_png.relative_to(ROOT)),
        "generative_image": str(gen_png.relative_to(ROOT)),
        "vision_review": verdict,
        "_files": [proc_png, gen_png],
    }


def main() -> int:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_id = f"exp5-7-cad-vs-diffusion-{ts}-v1"
    run_dir = ROOT / "validation" / "runs" / run_id
    book = ReceiptBook(run_dir / "receipts")
    print(f"[run] {run_id}")

    route_a = run_route_a(book)
    print("[route-a] done")

    try:
        route_b = run_route_b(book)
        print("[route-b] done")
    except Exception as e:
        traceback.print_exc()
        route_b = {"status": "incomplete", "reason": repr(e),
                   "note": "3D 生成路线失败，如实记录；未 mock 任何网格"}
        print(f"[route-b] INCOMPLETE: {e!r}")

    control = run_control_group(book)
    print("[control] done")

    files = (route_a.pop("_files", []) + route_b.pop("_files", [])
             + control.pop("_files", []))
    a_within_tol = route_a.pop("_within_tol", False)

    gates = {
        "route_a_llm_generated_code_executed": route_a["status"] == "completed",
        "route_a_step_and_stl_exported": route_a["status"] == "completed",
        "route_a_dimensions_within_tolerance": bool(a_within_tol),
        "route_b_real_external_generation": route_b["status"] == "completed",
        "route_b_mesh_measured_as_is": route_b["status"] == "completed",
        "change_request_route_a_single_param_patch":
            route_a.get("change_cost", {}).get("lines_changed") == 1
            and route_a.get("change_cost", {}).get("llm_calls") == 0,
        "change_request_route_b_full_regeneration":
            route_b["status"] == "completed"
            and route_b.get("change_cost", {}).get("llm_calls") == 2,
        "control_group_both_images_real": True,
        "control_group_vision_judge_real":
            not control["vision_review"]["parsed"].get("parse_error", False),
        "receipts_complete": len(book.calls) > 0
            and all(c["status"] == "ok" for c in book.calls),
    }

    manifest = {
        "schema_version": "1.0",
        "experiment": "5-7",
        "run_id": run_id,
        "generated_at_utc": utc_now(),
        "python": sys.version.split()[0],
        "spec": {"text": FLANGE_SPEC_TEXT, "m5": SPEC_M5},
        "change_request": {"text": CHANGE_REQUEST_TEXT, "m6": SPEC_M6},
        "route_a": route_a,
        "route_b": route_b,
        "control_group": control,
        "receipts": book.calls,
        "gates": gates,
        "artifacts": _collect_artifacts(files),
    }
    validate_manifest(manifest)

    run_dir.mkdir(parents=True, exist_ok=True)
    mpath = run_dir / "manifest.json"
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    (ROOT / "validation" / "latest.json").write_text(json.dumps(
        {"run_id": run_id, "manifest": f"validation/runs/{run_id}/manifest.json",
         "manifest_sha256": sha256_file(mpath)}, ensure_ascii=False, indent=2))
    print(f"[done] manifest: {mpath}")
    print(json.dumps(gates, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
