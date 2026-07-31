import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
import torch


def _optional_dependency_stubs():
    torchaudio = ModuleType("torchaudio")
    torchaudio.__path__ = []
    transforms = ModuleType("torchaudio.transforms")
    torchaudio.transforms = transforms

    unsloth = ModuleType("unsloth")
    unsloth.FastLanguageModel = MagicMock()
    snac = ModuleType("snac")
    snac.SNAC = MagicMock()

    return {
        "torchaudio": torchaudio,
        "torchaudio.transforms": transforms,
        "unsloth": unsloth,
        "snac": snac,
    }


OPTIONAL_DEPENDENCY_STUBS = _optional_dependency_stubs()
INFERENCE_PATH = Path(__file__).with_name("inference.py")
SPEC = importlib.util.spec_from_file_location("orpheus_inference_under_test", INFERENCE_PATH)
INFERENCE_MODULE = importlib.util.module_from_spec(SPEC)

# Keep heavyweight optional dependencies local to this import. patch.dict
# restores every prior sys.modules entry immediately after inference.py loads.
with patch.dict(sys.modules, OPTIONAL_DEPENDENCY_STUBS):
    SPEC.loader.exec_module(INFERENCE_MODULE)

OrpheusInference = INFERENCE_MODULE.OrpheusInference


class DummyInference(OrpheusInference):
    def __init__(self):
        self.snac_model = MagicMock()


@pytest.mark.parametrize("tail_length", range(7))
def test_redistribute_codes_discards_trailing_incomplete_frame(tail_length):
    dummy = DummyInference()
    expected_audio = torch.ones(1, 1, 4)
    dummy.snac_model.decode.return_value = expected_audio

    # One valid SNAC frame followed by zero to six incomplete-frame codes.
    valid_frame = [1, 4098, 8195, 12292, 16389, 20486, 24583]
    audio = dummy._redistribute_codes(valid_frame + [999] * tail_length)

    assert audio is expected_audio
    dummy.snac_model.decode.assert_called_once()
    codes = dummy.snac_model.decode.call_args.args[0]
    assert [tensor.tolist() for tensor in codes] == [
        [[1]],
        [[2, 5]],
        [[3, 4, 6, 7]],
    ]


@pytest.mark.parametrize("incomplete_length", range(1, 7))
def test_redistribute_codes_returns_silence_for_only_incomplete_codes(incomplete_length):
    dummy = DummyInference()

    audio = dummy._redistribute_codes([999] * incomplete_length)

    assert tuple(audio.shape) == (1, 1, 1000)
    assert torch.count_nonzero(audio).item() == 0
    dummy.snac_model.decode.assert_not_called()


@pytest.mark.parametrize(
    ("module_name", "stub"),
    OPTIONAL_DEPENDENCY_STUBS.items(),
    ids=OPTIONAL_DEPENDENCY_STUBS,
)
def test_optional_dependency_stubs_are_restored(module_name, stub):
    assert sys.modules.get(module_name) is not stub
