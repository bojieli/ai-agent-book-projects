import unittest

from run_experiment_8_7 import describe


class CampaignStatisticsTest(unittest.TestCase):
    def test_repeated_run_statistics_report_t_interval(self):
        result = describe([0.0, 0.5, 1.0])
        self.assertEqual(3, result["n"])
        self.assertEqual(0.5, result["mean"])
        self.assertGreater(result["sample_stdev"], 0)
        self.assertLess(result["ci95_t"][0], result["mean"])
        self.assertGreater(result["ci95_t"][1], result["mean"])


if __name__ == "__main__":
    unittest.main()
