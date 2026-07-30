from campaign import missing_extraction_rows


def test_missing_extraction_rows_finds_omissions_across_batches():
    rows = [{"id": "case-a"}, {"id": "case-b"}, {"id": "case-c"}]
    outputs = [
        {"cases": [{"id": "case-a"}]},
        {"cases": [{"id": "case-c"}]},
    ]

    assert missing_extraction_rows(rows, outputs) == [{"id": "case-b"}]


def test_missing_extraction_rows_ignores_null_ids_and_empty_outputs():
    rows = [{"id": "case-a"}]
    outputs = [{"cases": [{"id": None}]}, {}, {"cases": None}]

    assert missing_extraction_rows(rows, outputs) == rows
