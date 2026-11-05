"""Offline checks using the bundled models; provider requests are mocked."""
import os
import unittest
from unittest import mock

import numpy as np
import requests
from PIL import Image

# Import against an inert endpoint, without using any developer's RPC credential.
with mock.patch.dict(os.environ, {"RPC_URL_DAS": "https://provider.invalid"}):
    import server


class ModelCompatibilityTests(unittest.TestCase):
    def test_image_model_runs_on_the_expected_input(self):
        self.assertEqual(server.image_model.input_shape, (None, 256, 256, 3))
        confidence, label = server.predict_from_image(
            server.image_model, Image.new("RGB", (256, 256), "white")
        )
        self.assertIn(label, {"legit", "scam"})
        self.assertTrue(0 <= confidence <= 1)

    def test_all_five_metadata_models_run(self):
        self.assertEqual(len(server.metadata_models), 5)
        for model, features in server.metadata_models:
            with self.subTest(feature_count=len(features)):
                prediction = model.predict(np.zeros((1, len(features))))[0]
                self.assertIn(int(prediction), {0, 1})


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_homepage_and_original_styles_are_served(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        response = self.client.get("/static/style.css")
        self.assertEqual(response.status_code, 200)
        response.close()

    def test_missing_mint_returns_400(self):
        response = self.client.post("/fetch_nft", data={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "No mint address provided"})

    def test_image_only_fallback(self):
        with mock.patch.object(server, "fetch_nft_metadata", return_value={"image": "https://images.invalid/nft.png"}), \
             mock.patch.object(server, "download_image", return_value=Image.new("RGB", (1, 1))), \
             mock.patch.object(server, "predict_from_image", return_value=(0.9, "legit")), \
             mock.patch.object(server, "predict_from_metadata", return_value=None):
            response = self.client.post("/fetch_nft", data={"nft_mint": "example-mint"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["prediction"], "legit")
        self.assertEqual(response.json["probability"], 0.9)

    def test_real_metadata_only_fallback(self):
        metadata = {feature: 0 for _, features in server.metadata_models for feature in features}
        with mock.patch.object(server, "fetch_nft_metadata", return_value=metadata):
            response = self.client.post("/fetch_nft", data={"nft_mint": "example-mint"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json["prediction"], {"legit", "scam"})
        self.assertIsNone(response.json["image_url"])

    def test_provider_errors_do_not_expose_details(self):
        marker = "provider-detail-must-not-be-shared"
        with mock.patch.object(server.requests, "post", side_effect=requests.RequestException(marker)), \
             self.assertLogs(server.app.logger, level="ERROR") as logs:
            response = self.client.post("/fetch_nft", data={"nft_mint": "example-mint"})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(marker, response.get_data(as_text=True))
        self.assertNotIn(marker, "\n".join(logs.output))

    def test_provider_response_is_not_logged_and_request_has_timeout(self):
        marker = "response-detail-must-not-be-logged"
        upstream = mock.Mock(status_code=200)
        upstream.json.return_value = {"result": {"detail": marker}}
        with mock.patch.object(server.requests, "post", return_value=upstream) as post, \
             self.assertLogs(server.app.logger, level="INFO") as logs:
            result = server.fetch_nft_metadata("example-mint")
        self.assertEqual(result["detail"], marker)
        self.assertNotIn(marker, "\n".join(logs.output))
        self.assertEqual(post.call_args.kwargs["timeout"], 15)
        upstream.raise_for_status.assert_called_once()

    def test_image_download_errors_do_not_expose_url_details(self):
        marker = "image-request-detail-must-not-be-shared"
        with mock.patch.object(server.requests, "get", side_effect=requests.RequestException(marker)), \
             self.assertLogs(server.app.logger, level="ERROR") as logs:
            result = server.download_image("https://images.invalid/nft.png")
        self.assertIsNone(result)
        self.assertNotIn(marker, "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
