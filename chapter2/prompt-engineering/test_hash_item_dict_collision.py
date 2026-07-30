import pytest
from tau_bench.model_utils.api.cache import hash_item


def test_hash_item_dict_different_values():
    dict1 = {"a": 1}
    dict2 = {"a": 2}
    assert hash_item(dict1) != hash_item(dict2)


def test_hash_item_dict_different_key_value_pairs():
    dict1 = {"a": 1, "b": 2}
    dict2 = {"a": 2, "b": 1}
    assert hash_item(dict1) != hash_item(dict2)
