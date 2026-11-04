from types import SimpleNamespace

import pytest

import engine.pose.mediapipe_estimator as module
from engine.pose.types import Landmark, PoseExtractionResult


@pytest.mark.parametrize("complexity", [0, 1, 2])
def test_model_selection_is_explicit_without_loading_weights(monkeypatch, complexity):
    settings = {}

    def factory(**kwargs):
        settings.update(kwargs)
        return SimpleNamespace(close=lambda: None)

    monkeypatch.setattr(module.mp.solutions.pose, "Pose", factory)
    estimator = module.MediaPipePoseEstimator(model_complexity=complexity)
    assert settings["model_complexity"] == complexity
    assert settings["min_detection_confidence"] == .5
    assert settings["min_tracking_confidence"] == .5
    estimator.close()


@pytest.mark.parametrize("value", [None, "2", True, 3, -1, 1.0])
def test_invalid_model_selection_is_rejected(value):
    with pytest.raises(ValueError, match="model_complexity"):
        module.MediaPipePoseEstimator(model_complexity=value)


def test_model_caches_are_separate_and_source_change_invalidates_them(monkeypatch, tmp_path):
    import tools.review_samples as review
    video = tmp_path / "source.mp4"
    video.write_bytes(b"first")
    calls = []

    class FakeEstimator:
        def __init__(self, model_complexity):
            calls.append(model_complexity)

        def extract_with_metadata(self, video_path):
            return PoseExtractionResult([[Landmark(.5, .5, 0, 1)] * 33], [0], 1, (100, 100), 30)

        def close(self):
            pass

    monkeypatch.setattr(review, "MediaPipePoseEstimator", FakeEstimator)
    for model in (1, 2, 1, 2):
        result = review.load_extraction(video, tmp_path, reuse=True, model_complexity=model)
        assert result.source_frame_indices == [0]
    assert calls == [1, 2]
    video.write_bytes(b"source changed")
    review.load_extraction(video, tmp_path, reuse=True, model_complexity=2)
    assert calls == [1, 2, 2]
