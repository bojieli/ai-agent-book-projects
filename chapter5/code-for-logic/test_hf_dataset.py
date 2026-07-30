from build_hf_puzzles import convert_expression, convert_row


def test_convert_dataset_expression_and_label():
    row = {
        "quiz": "A says B is not lying. B says B is truthful iff A is lying.",
        "names": ["A", "B"],
        "solution": [False, False],
        "statements": "(('not', ('lying', 1)), ('<=>', ('telling-truth', 1), ('lying', 0)))",
        "index": 7,
    }
    puzzle = convert_row(
        row,
        perturbation="perturbed_leaf",
        people=2,
        source_path="test/perturbed_leaf/people2_num100.jsonl",
        source_sha256="abc",
        source_row=7,
    )
    assert puzzle["solution"] == {"A": "knave", "B": "knave"}
    assert puzzle["source"]["dataset_index"] == 7


def test_convert_implication_and_biconditional():
    names = ["A", "B"]
    assert convert_expression(("->", ("lying", 0), ("telling-truth", 1)), names)[0] == "implies"
    assert convert_expression(("<=>", ("lying", 0), ("telling-truth", 1)), names)[0] == "iff"
