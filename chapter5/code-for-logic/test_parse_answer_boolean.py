import sys
from pathlib import Path

# Ensure demo module can be resolved regardless of working directory
sys.path.insert(0, str(Path(__file__).parent))

from demo import parse_answer


def test_parse_answer_supports_boolean_json_values():
    """Verify parse_answer maps JSON boolean true/false to knight/knave.

    Contract: LLMs outputting JSON solutions with boolean values like {"A": true, "B": false}
    must be normalized to {"A": "knight", "B": "knave"} instead of returning None.
    Locks out KeyError or unparsed boolean JSON answers.
    """
    text = 'The solution is {"A": true, "B": false}'
    ans = parse_answer(text, ["A", "B"])
    assert ans == {"A": "knight", "B": "knave"}


def test_parse_answer_supports_numeric_and_str_boolean():
    """Verify parse_answer maps numeric 1/0 and string "true"/"false" booleans to knight/knave.

    Contract: 1 and "true" map to "knight"; 0 and "false" map to "knave".
    Locks out unparsed numeric or string boolean representation in model output.
    """
    text1 = '{"A": 1, "B": 0}'
    assert parse_answer(text1, ["A", "B"]) == {"A": "knight", "B": "knave"}

    text2 = '{"A": "true", "B": "false"}'
    assert parse_answer(text2, ["A", "B"]) == {"A": "knight", "B": "knave"}
