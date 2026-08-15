import importlib.util
from pathlib import Path

import torch


HERE = Path(__file__).parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sesame_tag_categories_are_explicit():
    sesame = load("run_sesame")
    assert sesame.category("hello <laughs> there") == "laugh"
    assert sesame.category("hello <giggle> there") == "giggle"
    assert sesame.category("hello <sighs> there") == "sigh"
    assert sesame.category("hello there") == "neutral"


def test_orpheus_collator_masks_label_padding():
    orpheus = load("run_orpheus")
    rows = [
        {"input_ids": [1, 2], "labels": [1, 2], "attention_mask": [1, 1]},
        {"input_ids": [3], "labels": [3], "attention_mask": [1]},
    ]
    batch = orpheus.PadCollator(9)(rows)
    assert batch["input_ids"].tolist() == [[1, 2], [3, 9]]
    assert batch["labels"].tolist() == [[1, 2], [3, -100]]
    assert batch["attention_mask"].tolist() == [[1, 1], [1, 0]]


def test_sesame_collator_stacks_all_model_inputs():
    sesame = load("run_sesame")
    rows = [{"input_ids": torch.tensor([1, 2]), "labels": torch.tensor([3, 4])}] * 2
    batch = sesame.TensorCollator()(rows)
    assert batch["input_ids"].shape == (2, 2)
    assert batch["labels"].shape == (2, 2)


def test_sha256_is_stable(tmp_path):
    analysis = load("analyze_campaign")
    path = tmp_path / "artifact"
    path.write_bytes(b"experiment-7-6")
    assert analysis.sha256(path) == "2318feba157d85bc6dfb79317ded3c820f3ef8ffb9ddc0951aa1aea644a9829b"
