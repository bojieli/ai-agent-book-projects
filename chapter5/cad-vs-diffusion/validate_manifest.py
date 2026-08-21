"""正式运行 manifest 的模式校验（离线，供 run_experiment 与 pytest 共用）。"""

REQUIRED_TOP_KEYS = [
    "schema_version", "experiment", "run_id", "generated_at_utc",
    "spec", "change_request", "route_a", "route_b", "control_group",
    "receipts", "gates", "artifacts",
]

REQUIRED_MEASURE_KEYS = [
    "outer_diameter_mm", "thickness_mm", "hole_count_detected",
    "hole_diameter_mm", "hole_circle_diameter_mm",
    "mounting_face_flatness_rms_mm", "deviations",
]

REQUIRED_DEVIATION_KEYS = [
    "outer_diameter_mm", "thickness_mm", "hole_diameter_mm",
    "hole_circle_diameter_mm", "hole_count",
]

REQUIRED_GATES = [
    "route_a_llm_generated_code_executed",
    "route_a_step_and_stl_exported",
    "route_a_dimensions_within_tolerance",
    "route_b_real_external_generation",
    "route_b_mesh_measured_as_is",
    "change_request_route_a_single_param_patch",
    "change_request_route_b_full_regeneration",
    "control_group_both_images_real",
    "control_group_vision_judge_real",
    "receipts_complete",
]


def validate_manifest(m: dict) -> None:
    """缺键或结构不符即抛 AssertionError。"""
    for k in REQUIRED_TOP_KEYS:
        assert k in m, f"manifest 缺顶层键: {k}"
    for route in ("route_a", "route_b"):
        r = m[route]
        assert "status" in r, f"{route} 缺 status"
        if r["status"] != "completed":
            continue  # 未完成的路线如实标注即可，不强求测量字段
        for phase in ("initial", "after_change"):
            assert phase in r, f"{route} 缺 {phase}"
            meas = r[phase]["measurement"]
            for k in REQUIRED_MEASURE_KEYS:
                assert k in meas, f"{route}.{phase}.measurement 缺 {k}"
            for k in REQUIRED_DEVIATION_KEYS:
                assert k in meas["deviations"], f"{route}.{phase}.deviations 缺 {k}"
    for g in REQUIRED_GATES:
        assert g in m["gates"], f"gates 缺 {g}"
        assert isinstance(m["gates"][g], bool), f"gate {g} 不是 bool"
    assert m["receipts"], "receipts 为空"
    for rec in m["receipts"]:
        for k in ("name", "path", "sha256", "status", "latency_ms"):
            assert k in rec, f"receipt 缺 {k}"
    for path, info in m["artifacts"].items():
        assert isinstance(path, str) and path, "artifact 路径为空"
        for k in ("sha256", "bytes"):
            assert k in info, f"artifact {path} 缺 {k}"
