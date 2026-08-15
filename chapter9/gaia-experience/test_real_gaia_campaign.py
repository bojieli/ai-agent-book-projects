import unittest

from real_gaia_campaign import gaia_component_score, outcome_label


class RealGAIACampaignTest(unittest.TestCase):
    def test_official_exact_and_partial_list_score_are_separate(self):
        partial = gaia_component_score("Yoshida", "Yoshida, Uehara")
        self.assertFalse(partial["official_exact"])
        self.assertEqual(0.5, partial["component_score"])
        self.assertEqual("partial", outcome_label(partial["component_score"]))

    def test_numeric_and_formatted_answers_match_aworld_semantics(self):
        self.assertTrue(gaia_component_score("5,876", "5876")["official_exact"])
        self.assertTrue(gaia_component_score("Saint Petersburg", "Saint Petersburg")["official_exact"])
        self.assertFalse(gaia_component_score("Petersburg", "Saint Petersburg")["official_exact"])


if __name__ == "__main__":
    unittest.main()
