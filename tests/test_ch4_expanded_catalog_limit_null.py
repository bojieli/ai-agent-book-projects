import sys, os

sys.path.insert(0, os.path.abspath("chapter4/perception-tools/src"))
from expanded_catalog import _limit


def test_expanded_catalog_limit_null_option_handled():
    # Options dict with "limit": None (e.g. parsed from JSON '{"limit": null}')
    limit = _limit({"limit": None}, default=10)
    assert limit == 10

    # Non-integer / string limit handled cleanly
    limit_invalid = _limit({"limit": "invalid"}, default=15)
    assert limit_invalid == 15
