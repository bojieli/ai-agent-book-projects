from compare import compare


def test_compare_empty_texts():
    result = compare(
        prompt_template="Classify: {text}",
        texts=[],
        teacher_labels={},
        eval_results=None,
        count_tokens=lambda s: max(1, len(s) // 4),
        token_method="test",
        num_examples=3,
    )
    assert result["teacher_input_avg"] == 0.0
    assert result["student_input_avg"] == 0.0
    assert result["input_token_reduction_pct"] == 0.0
