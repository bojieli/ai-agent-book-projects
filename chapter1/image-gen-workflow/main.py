"""
实验 1-4 正式运行入口：让每句口语化需求分别走两条路线并落盘留证。

用法：
    python main.py                      # 全部 3 句需求 × 2 条路线
    python main.py --route workflow     # 只跑工作流路线
    python main.py --requirement windowsill-plant

产物：
    outputs/<run_id>/images/            生成的图片
    outputs/<run_id>/calls/             每次 API 调用的请求/响应留证
    validation/real_<run_id>/evidence.json   evidence manifest
    validation/latest.json              最近一次 manifest 的副本
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from config import Config
from evidence import build_manifest, sha256_bytes, sha256_file, validate_manifest
from pipeline import ROUTE_RUNNERS

PROJECT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PROJECT_DIR.parents[1]

# 测试需求：口语化中文描述，分两类对照（见书稿实验 1-4 的调整后设计）
# - 具体需求（specific）：已指定场景/文案细节，考察执行的忠实度
# - 宽泛需求（broad）：只给主题不给细节，考察改写节点的场景具象化带来的信息增益
REQUIREMENTS: List[Dict[str, str]] = [
    {
        "id": "programmer-overtime",
        "category": "specific",
        "text": "帮我画一个周末加班的程序员，风格丧一点",
    },
    {
        "id": "windowsill-plant",
        "category": "specific",
        "text": "帮我画一盆放在窗台上的绿植，早晨的阳光刚好照进来",
    },
    {
        "id": "headphone-poster",
        "category": "specific",
        "text": "帮我做一张新款降噪耳机的产品海报，主打“深夜独处也清净”这句文案，风格简约高级",
    },
    {
        "id": "agi-programmer",
        "category": "broad",
        "text": "帮我画一个 AGI 实现以后程序员的工作场景",
    },
    {
        "id": "future-city-morning",
        "category": "broad",
        "text": "帮我画一幅“未来城市的早晨”的画",
    },
]

# 模型选型实录（正式运行写入 manifest.notes，与 README 一致）
SELECTION_NOTES = [
    "原生路线 A（native）：gemini-3-pro-image（书稿所称 Nano Banana 2），"
    "使用官方 google-genai SDK 直接出图（response_modalities=[IMAGE]）；"
    "ListModels 实测可用，偶发内容过滤（content=None），重跑即恢复。",
    "原生路线 B（native_gptimage）：gpt-image-2（GPT-Image 2），OpenAI images.generations 接口，"
    "全部 5 句需求均一次成功；该账户此前 GPT-5.x 的 credit_balance_exhausted 未影响图像接口。",
    "工作流路线生图工具：首选 SiliconFlow 托管 FLUX/SD，实测 black-forest-labs/FLUX.1-schnell 与 "
    "stabilityai/stable-diffusion-3-5-large 返回 Model disabled，账户余额为 0；OpenRouter 仅提供"
    "视觉理解模型，不支持文本转图像生成；改用 DashScope 国际站通义万相 wan2.2-t2i-flash"
    "（经典扩散式文生图，接受 SD 风格提示词）。",
    "改写节点 LLM：Moonshot kimi-k3（OpenAI 兼容接口）；kimi-k3 只允许 temperature=1，"
    "显式传其他值被 400 拒绝（见第 1 轮失败记录）。",
]

MIME_EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def run_one(requirement: Dict[str, str], route: str, run_dir: Path) -> Dict[str, Any]:
    req_id, text = requirement["id"], requirement["text"]
    print(f"\n=== [{route}] {req_id}: {text}")
    run_record: Dict[str, Any] = {
        "requirement_id": req_id,
        "route": route,
        "input": text,
        "rewrite": None,
        "nodes": [],
        "image": None,
        "error": None,
    }
    calls_dir = run_dir / "calls"
    try:
        result = ROUTE_RUNNERS[route](text)
        run_record["rewrite"] = result["rewrite"]
        run_record["nodes"] = [
            {k: v for k, v in node.items()} for node in result["nodes"]
        ]
        # 每次调用的请求/响应单独落盘
        for node in result["nodes"]:
            calls = node.get("calls") or [node.get("call")]
            for call in calls:
                if call:
                    save_json(
                        calls_dir / f"{req_id}_{route}_{node['node']}_{call['call_id']}.json",
                        call,
                    )
        ext = MIME_EXT.get(result["mime"], ".bin")
        image_path = run_dir / "images" / f"{req_id}_{route}{ext}"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(result["image_bytes"])
        run_record["image"] = {
            "path": str(image_path.relative_to(PROJECT_DIR)),
            "sha256": sha256_bytes(result["image_bytes"]),
            "bytes": len(result["image_bytes"]),
            "mime": result["mime"],
        }
        print(f"    -> {image_path.relative_to(PROJECT_DIR)} "
              f"({len(result['image_bytes'])} bytes)")
    except Exception as e:
        run_record["error"] = f"{type(e).__name__}: {e}"
        print(f"    !! 失败: {run_record['error']}")
    return run_record


ALL_ROUTES = ["workflow", "native", "native_gptimage"]


def main() -> int:
    parser = argparse.ArgumentParser(description="实验 1-4 对照运行")
    parser.add_argument(
        "--route",
        choices=ALL_ROUTES + ["all"],
        default="all",
        help="只跑某条路线（默认 all：全部三条路线）",
    )
    parser.add_argument(
        "--requirement",
        action="append",
        choices=[r["id"] for r in REQUIREMENTS],
        help="只跑指定需求（可重复，默认全部）",
    )
    args = parser.parse_args()

    if not Config.validate():
        return 1

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = PROJECT_DIR / "outputs" / run_id
    routes = ALL_ROUTES if args.route == "all" else [args.route]
    requirements = [
        r for r in REQUIREMENTS if not args.requirement or r["id"] in args.requirement
    ]

    print(f"run_id={run_id}  需求 {len(requirements)} 句 × 路线 {routes}")
    runs: List[Dict[str, Any]] = []
    for requirement in requirements:
        for route in routes:
            runs.append(run_one(requirement, route, run_dir))

    manifest = build_manifest(
        requirements=requirements,
        runs=runs,
        project_root=PROJECT_ROOT,
        notes=SELECTION_NOTES,
    )
    problems = validate_manifest(manifest)
    if problems:
        print("\nmanifest 校验发现问题:")
        for p in problems:
            print(f"  - {p}")

    val_dir = PROJECT_DIR / "validation" / f"real_{run_id}"
    save_json(val_dir / "evidence.json", manifest)
    digest = sha256_file(val_dir / "evidence.json")
    (val_dir / "evidence.sha256").write_text(
        f"{digest}  evidence.json\n", encoding="utf-8"
    )
    save_json(PROJECT_DIR / "validation" / "latest.json", manifest)

    ok = sum(1 for r in runs if r["error"] is None)
    print(f"\n完成: {ok}/{len(runs)} 次运行成功")
    print(f"manifest: {val_dir / 'evidence.json'}")
    print(f"sha256:   {digest}")
    return 0 if not problems else 2


if __name__ == "__main__":
    sys.exit(main())
