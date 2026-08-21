"""离线测试：测量函数、manifest 模式校验。不打任何外部 API。

网格 fixture（tests/fixtures/flange_m5.stl）由 CadQuery 本地按规格生成：
外径 80 / 厚 10 / 4 孔均布 / 孔径 5.5 / 孔位圆直径 60。
"""
import copy
import sys
from pathlib import Path

import pytest
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import measure  # noqa: E402
from flange_spec import SPEC_M5  # noqa: E402
from validate_manifest import validate_manifest  # noqa: E402

FIXTURE = Path(__file__).parent / "tests" / "fixtures" / "flange_m5.stl"


@pytest.fixture(scope="module")
def flange_measurement():
    mesh = measure.load_mesh(str(FIXTURE))
    return measure.measure_flange(mesh, SPEC_M5)


def test_fixture_dimensions_accurate(flange_measurement):
    dev = flange_measurement["deviations"]
    for key in ("outer_diameter_mm", "thickness_mm", "hole_diameter_mm",
                "hole_circle_diameter_mm"):
        assert abs(dev[key]["abs_error_mm"]) < 0.5, f"{key}: {dev[key]}"
    assert dev["hole_count"]["measured"] == 4
    assert dev["hole_count"]["match"] is True


def test_fixture_flat_face(flange_measurement):
    assert flange_measurement["mounting_face_flatness_rms_mm"] < 0.01
    assert flange_measurement["mesh_watertight"] is True


def test_box_mesh_has_no_holes():
    box = trimesh.creation.box(extents=[80, 80, 10])
    m = measure.measure_flange(box, SPEC_M5)
    assert m["hole_count_detected"] == 0
    assert m["hole_diameter_mm"] is None
    assert m["deviations"]["hole_diameter_mm"]["measured"] is None
    assert m["deviations"]["hole_count"]["match"] is False


def _minimal_valid_manifest():
    meas = {
        "outer_diameter_mm": 80.0, "thickness_mm": 10.0,
        "hole_count_detected": 4, "hole_diameter_mm": 5.5,
        "hole_circle_diameter_mm": 60.0,
        "mounting_face_flatness_rms_mm": 0.001,
        "deviations": {
            "outer_diameter_mm": {}, "thickness_mm": {},
            "hole_diameter_mm": {}, "hole_circle_diameter_mm": {},
            "hole_count": {"match": True},
        },
    }
    route = {"status": "completed",
             "initial": {"measurement": copy.deepcopy(meas)},
             "after_change": {"measurement": copy.deepcopy(meas)}}
    return {
        "schema_version": "1.0", "experiment": "5-7", "run_id": "t",
        "generated_at_utc": "2026-01-01T00:00:00Z",
        "spec": {}, "change_request": {},
        "route_a": route, "route_b": copy.deepcopy(route),
        "control_group": {},
        "receipts": [{"name": "x", "path": "p", "sha256": "s",
                      "status": "ok", "latency_ms": 1}],
        "gates": {
            "route_a_llm_generated_code_executed": True,
            "route_a_step_and_stl_exported": True,
            "route_a_dimensions_within_tolerance": True,
            "route_b_real_external_generation": True,
            "route_b_mesh_measured_as_is": True,
            "change_request_route_a_single_param_patch": True,
            "change_request_route_b_full_regeneration": True,
            "control_group_both_images_real": True,
            "control_group_vision_judge_real": True,
            "receipts_complete": True,
        },
        "artifacts": {"output/x.stl": {"sha256": "s", "bytes": 1}},
    }


def test_validate_manifest_ok():
    validate_manifest(_minimal_valid_manifest())


def test_validate_manifest_missing_gate():
    m = _minimal_valid_manifest()
    del m["gates"]["receipts_complete"]
    with pytest.raises(AssertionError):
        validate_manifest(m)


def test_validate_manifest_incomplete_route_allowed():
    m = _minimal_valid_manifest()
    m["route_b"] = {"status": "incomplete", "reason": "公共 Space 排队超时"}
    validate_manifest(m)
