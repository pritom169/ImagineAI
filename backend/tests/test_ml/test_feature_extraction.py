from unittest.mock import MagicMock, patch

import pytest


class TestFeatureExtraction:
    @patch("ml.models.feature_extractor.FeatureExtractor")
    def test_feature_extractor_returns_vector(self, mock_extractor):
        mock_instance = MagicMock()
        mock_instance.extract.return_value = [0.1] * 512
        mock_extractor.return_value = mock_instance

        extractor = mock_extractor()
        features = extractor.extract("dummy_image_path")

        assert len(features) == 512
        assert all(isinstance(f, float) for f in features)
        mock_instance.extract.assert_called_once()

    @patch("ml.models.feature_extractor.FeatureExtractor")
    def test_feature_similarity(self, mock_extractor):
        mock_instance = MagicMock()
        mock_instance.compute_similarity.return_value = 0.85
        mock_extractor.return_value = mock_instance

        extractor = mock_extractor()
        similarity = extractor.compute_similarity(
            [0.1] * 512, [0.2] * 512
        )

        assert 0 <= similarity <= 1
        assert similarity == 0.85

    @patch("ml.models.feature_extractor.FeatureExtractor")
    def test_batch_extraction(self, mock_extractor):
        mock_instance = MagicMock()
        mock_instance.extract_batch.return_value = [[0.1] * 512 for _ in range(3)]
        mock_extractor.return_value = mock_instance

        extractor = mock_extractor()
        results = extractor.extract_batch(["img1.jpg", "img2.jpg", "img3.jpg"])

        assert len(results) == 3
        assert all(len(vec) == 512 for vec in results)


class TestDefectDetection:
    @patch("ml.models.defect_detector.DefectDetector")
    def test_defect_detector_returns_detections(self, mock_detector):
        mock_instance = MagicMock()
        mock_instance.detect.return_value = [
            {
                "defect_type": "scratch",
                "confidence": 0.87,
                "severity": "medium",
                "bounding_box": {"x": 0.2, "y": 0.3, "width": 0.1, "height": 0.05},
            }
        ]
        mock_detector.return_value = mock_instance

        detector = mock_detector()
        detections = detector.detect("image_path")

        assert len(detections) == 1
        assert detections[0]["defect_type"] == "scratch"
        assert detections[0]["confidence"] == 0.87
        assert "bounding_box" in detections[0]

    @patch("ml.models.defect_detector.DefectDetector")
    def test_no_defects_detected(self, mock_detector):
        mock_instance = MagicMock()
        mock_instance.detect.return_value = []
        mock_detector.return_value = mock_instance

        detector = mock_detector()
        detections = detector.detect("clean_image.jpg")

        assert detections == []

    @patch("ml.models.defect_detector.DefectDetector")
    def test_multiple_defects(self, mock_detector):
        mock_instance = MagicMock()
        mock_instance.detect.return_value = [
            {"defect_type": "scratch", "confidence": 0.9, "severity": "high",
             "bounding_box": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.1}},
            {"defect_type": "dent", "confidence": 0.7, "severity": "low",
             "bounding_box": {"x": 0.5, "y": 0.6, "width": 0.2, "height": 0.15}},
        ]
        mock_detector.return_value = mock_instance

        detector = mock_detector()
        detections = detector.detect("damaged_image.jpg")

        assert len(detections) == 2
        types = [d["defect_type"] for d in detections]
        assert "scratch" in types
        assert "dent" in types
