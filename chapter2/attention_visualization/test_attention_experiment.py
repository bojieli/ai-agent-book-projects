import numpy as np

from run_attention_experiment import matrix_metrics, region_indices, resolve_layer


def test_resolve_negative_layer():
    assert resolve_layer(-1, 28) == 27
    assert resolve_layer(13, 28) == 13


def test_region_indices_separates_thinking_and_answer():
    tokens = ["prompt", "<think>", "work", "</think>", "answer"]
    assert region_indices(tokens, 1) == {"thinking": [1, 2, 3], "answer": [4]}


def test_matrix_metrics_detects_causal_triangle_and_sink():
    matrix = np.asarray([[1.0, 0.0], [0.75, 0.25]])
    metrics = matrix_metrics(matrix)
    assert metrics["causal_upper_triangle_max"] == 0.0
    assert metrics["attention_sink_mean"] == 0.875
