import unittest
import tempfile
import os
import json
import main

class TestMain(unittest.TestCase):
    def test_compute_forecast_short(self):
        # length <= 31 -> d30=0, d60=0 -> forecast = L
        prices = [100.0] * 20
        forecast = main.compute_forecast(prices, horizon_minutes=10)
        self.assertEqual(forecast, 100.0)

    def test_compute_forecast_medium(self):
        # length = 40 (> 31, <= 61) -> d30 computed, d60 = 0
        # prices where last 30 minutes increase by 30 (so d30 = 1.0)
        prices = [100.0] * 10 + [100.0 + i for i in range(1, 31)]
        # L = prices[-1] = 130.0
        # prices[-31] is index 40 - 31 = 9 (price 100.0)
        # d30 = (130 - 100) / 30 = 1.0
        # d60 = 0.0
        # d = 0.5 * 1.0 + 0.5 * 0.0 = 0.5
        # horizon = 10, factor = 0.4 -> adjustment = 0.5 * 10 * 0.4 = 2.0
        # max_adj = 0.004 * 130 = 0.52 (adjustment 2.0 exceeds max_adj, so clamped to 0.52)
        # forecast = 130 + 0.52 = 130.52
        forecast = main.compute_forecast(prices, horizon_minutes=10)
        self.assertAlmostEqual(forecast, 130.52)

    def test_compute_forecast_long(self):
        # length = 70 (> 61) -> both d30 and d60 computed
        prices = [100.0 + i for i in range(70)]
        # L = prices[-1] = 169.0
        # prices[-61] = index 70 - 61 = 9 (price = 109.0)
        # d60 = (169 - 109) / 60 = 60 / 60 = 1.0
        # prices[-31] = index 70 - 31 = 39 (price = 139.0)
        # d30 = (169 - 139) / 30 = 30 / 30 = 1.0
        # d = 0.5 * 1.0 + 0.5 * 1.0 = 1.0
        # horizon = 10, adjustment = 1.0 * 10 * 0.4 = 4.0
        # max_adj = 0.004 * 169 = 0.676
        # clamped adjustment = 0.676
        # forecast = 169 + 0.676 = 169.676
        forecast = main.compute_forecast(prices, horizon_minutes=10)
        self.assertAlmostEqual(forecast, 169.676)

    def test_process_inputs(self):
        with tempfile.TemporaryDirectory() as tmp_in, tempfile.TemporaryDirectory() as tmp_out:
            os.environ["MAKEFUN_INPUT_DIR"] = tmp_in
            os.environ["MAKEFUN_OUTPUT_DIR"] = tmp_out

            case_data = {
                "schema": "btc-forecast",
                "competition": "makefun",
                "case": "case_test_001",
                "at": "2026-11-14T00:00:00Z",
                "horizon_minutes": 10,
                "markets": [
                    {
                        "id": "btc-usd",
                        "name": "Bitcoin",
                        "start": "2026-11-13T00:00:00Z",
                        "prices": [10000.0] * 50
                    }
                ]
            }

            in_file_path = os.path.join(tmp_in, "case_test_001.in")
            with open(in_file_path, "w", encoding="utf-8") as f:
                json.dump(case_data, f)

            main.process_inputs()

            out_file_path = os.path.join(tmp_out, "case_test_001.out")
            self.assertTrue(os.path.exists(out_file_path))

            with open(out_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Check trailing newline
                self.assertTrue(content.endswith("\n"))
                data = json.loads(content)
                self.assertIn("forecasts", data)
                self.assertEqual(len(data["forecasts"]), 1)
                self.assertEqual(data["forecasts"][0]["case"], "case_test_001")
                self.assertAlmostEqual(data["forecasts"][0]["price"], 10000.0)

if __name__ == "__main__":
    unittest.main()
