import sys
from unittest.mock import MagicMock

# Mock heavy optional ML packages if not installed
for mod in ["torchaudio", "torchaudio.transforms", "unsloth", "snac"]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

from inference import OrpheusInference


def test_redistribute_codes_non_multiple_of_seven():
    class DummyInference(OrpheusInference):
        def __init__(self):
            self.snac_model = MagicMock()

    dummy = DummyInference()
    # 6 elements (less than 7)
    code_list = [100000, 104096, 108192, 112288, 116384, 120480]
    audio = dummy._redistribute_codes(code_list)
    assert audio is not None
    # 13 elements (7 + 6, incomplete 2nd frame)
    code_list13 = [100000, 104096, 108192, 112288, 116384, 120480, 124576, 100000, 104096, 108192, 112288, 116384, 120480]
    audio13 = dummy._redistribute_codes(code_list13)
    assert audio13 is not None
