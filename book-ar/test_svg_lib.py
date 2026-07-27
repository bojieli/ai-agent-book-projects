import unittest

from svg_lib import _char_w, _text_width, _wrap_line


class ArabicTextWidthTests(unittest.TestCase):
    def test_combining_marks_have_zero_width(self):
        self.assertEqual(_char_w('\u064e'), 0)  # Fatha
        self.assertEqual(_char_w('\u0651'), 0)  # Shadda

    def test_harakat_do_not_force_an_extra_wrapped_line(self):
        text = 'مُدير ذكي'
        width_without_harakat = _text_width('مدير ذكي', 20)

        self.assertEqual(_wrap_line(text, width_without_harakat, 20), [text])

    def test_arabic_letters_keep_the_existing_width_estimate(self):
        self.assertEqual(_char_w('م'), 450)


if __name__ == '__main__':
    unittest.main()
