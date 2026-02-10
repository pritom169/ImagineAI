import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.factories import AnalysisResultFactory


class TestClassificationPipeline:
    def test_analysis_result_factory(self):
        result = AnalysisResultFactory()
        assert result.id is not None
        assert result.model_version == "efficientnet-b4-v1"
        assert result.status == "completed"
        assert 0.5 <= result.classification_confidence <= 0.99
        assert result.classification_label in ["electronics", "clothing", "footwear"]

    def test_analysis_result_scores_are_dict(self):
        result = AnalysisResultFactory()
        assert isinstance(result.classification_scores, dict)

    def test_analysis_result_processing_time(self):
        result = AnalysisResultFactory()
        assert 500 <= result.processing_time_ms <= 5000

    def test_multiple_analysis_results_unique_ids(self):
        results = [AnalysisResultFactory() for _ in range(5)]
        ids = [r.id for r in results]
        assert len(set(ids)) == 5

    @patch("ml.models.classifier.ImageClassifier")
    def test_classifier_mock(self, mock_classifier):
        mock_instance = MagicMock()
        mock_instance.predict.return_value = {
            "label": "electronics",
            "confidence": 0.95,
            "scores": {"electronics": 0.95, "clothing": 0.03, "footwear": 0.02},
        }
        mock_classifier.return_value = mock_instance

        classifier = mock_classifier()
        result = classifier.predict("dummy_image_path")

        assert result["label"] == "electronics"
        assert result["confidence"] == 0.95
        assert "scores" in result
        mock_instance.predict.assert_called_once_with("dummy_image_path")


class TestExtractedAttributes:
    def test_attribute_factory(self):
        from tests.factories import ExtractedAttributeFactory

        attr = ExtractedAttributeFactory()
        assert attr.id is not None
        assert attr.attribute_name in ["color", "material", "condition"]
        assert attr.attribute_value in ["blue", "leather", "new"]
        assert 0.4 <= attr.confidence <= 0.95


class TestDetectedDefects:
    def test_defect_factory(self):
        from tests.factories import DetectedDefectFactory

        defect = DetectedDefectFactory()
        assert defect.id is not None
        assert defect.defect_type in ["scratch", "dent", "discoloration"]
        assert defect.severity in ["low", "medium", "high"]
        assert 0.3 <= defect.confidence <= 0.9
        assert "x" in defect.bounding_box
        assert "y" in defect.bounding_box
        assert "width" in defect.bounding_box
        assert "height" in defect.bounding_box

    def test_bounding_box_values(self):
        from tests.factories import DetectedDefectFactory

        defect = DetectedDefectFactory()
        bbox = defect.bounding_box
        assert 0 <= bbox["x"] <= 1
        assert 0 <= bbox["y"] <= 1
        assert 0 < bbox["width"] <= 1
        assert 0 < bbox["height"] <= 1
