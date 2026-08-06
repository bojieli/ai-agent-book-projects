from main import _completed


def test_completed_field_is_authoritative_over_legacy_success_alias():
    assert _completed({"completed": False, "success": True}) is False
    assert _completed({"completed": True, "success": False}) is True


def test_completed_falls_back_for_old_result_artifacts():
    assert _completed({"success": True}) is True
    assert _completed({"success": False}) is False
