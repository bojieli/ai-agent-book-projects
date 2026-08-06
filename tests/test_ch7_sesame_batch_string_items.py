import sys
from types import ModuleType
from pathlib import Path
from unittest.mock import MagicMock
import torch

stubs = {
    "datasets": {"load_dataset": MagicMock(), "Audio": MagicMock()},
    "unsloth": {"FastModel": MagicMock()},
    "transformers": {"CsmForConditionalGeneration": MagicMock()},
    "peft": {"PeftModel": MagicMock()},
    "soundfile": {"write": lambda file, data, samplerate: Path(file).write_bytes(b"fake wav")},
    "tqdm": {"tqdm": lambda iterable, **kwargs: iterable},
}

for mod_name, attrs in stubs.items():
    if mod_name not in sys.modules:
        m = ModuleType(mod_name)
        for k, v in attrs.items():
            setattr(m, k, v)
        sys.modules[mod_name] = m

sesame_dir = Path(__file__).resolve().parent.parent / "chapter7" / "sesame"
if str(sesame_dir) not in sys.path:
    sys.path.insert(0, str(sesame_dir))

import batch_inference as bi


def test_generate_speech_batch_handles_string_items(tmp_path):
    model = MagicMock()
    model.generate.return_value = torch.zeros((1, 100))
    processor = MagicMock()
    processor.return_value.to.return_value = {"input_ids": torch.zeros((1, 10), dtype=torch.long)}

    texts = ["hello world"]
    bi.generate_speech_batch(model, processor, texts, str(tmp_path))
    assert len(list(tmp_path.glob("*.wav"))) == 1
