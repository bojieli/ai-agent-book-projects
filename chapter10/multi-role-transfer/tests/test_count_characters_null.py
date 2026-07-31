from tools import count_characters


def test_count_characters_null_text():
    result = count_characters(None)
    assert result == "总字符数=0, 其中中文字符=0"


def test_count_characters_normal():
    result = count_characters("你好hi")
    assert "总字符数=4" in result
    assert "中文字符=2" in result
