from types import SimpleNamespace

import numpy as np
import pytest

from engine.pose.types import Landmark, PoseExtractionResult
from engine.pose.recovery import recover_pose_gaps


def make_extraction(indices=(0, 2)):
    frame = [Landmark(.5, .5, 0, 1) for _ in range(33)]
    frame[0] = Landmark(.2, .2, 0, 1)
    frame[1] = Landmark(.8, .8, 0, 1)
    return PoseExtractionResult([frame, frame], list(indices), indices[-1] + 1, (100, 100), 30)


def setup_detector(monkeypatch, outputs):
    import mediapipe as mp
    import engine.pose.recovery as module
    state = {"reads": [], "closed": False, "released": False}

    class Capture:
        def set(self, prop, index):
            self.index = index

        def read(self):
            state["reads"].append(self.index)
            return True, np.zeros((100, 100, 3), dtype=np.uint8)

        def release(self):
            state["released"] = True

    class Detector:
        def __init__(self, **kwargs):
            state["settings"] = kwargs
            self.results = iter(outputs)

        def process(self, image):
            points = next(self.results)
            return SimpleNamespace(pose_landmarks=None if points is None else SimpleNamespace(landmark=points))

        def close(self):
            state["closed"] = True

    monkeypatch.setattr(module.cv2, "VideoCapture", lambda path: Capture())
    monkeypatch.setattr(mp.solutions.pose, "Pose", Detector)
    return state


def test_full_image_recovery_preserves_source_mapping_and_original_detections(monkeypatch):
    original = make_extraction()
    points = [Landmark(.5, .5, .1, 1) for _ in range(33)]
    state = setup_detector(monkeypatch, [points, None])
    recovered = recover_pose_gaps("fake.mp4", original)
    assert recovered.source_frame_indices == [0, 1, 2]
    assert recovered.recovered_frame_indices == [1]
    assert recovered.pose_sequence[0] is original.pose_sequence[0]
    assert recovered.pose_sequence[2] is original.pose_sequence[1]
    assert original.source_frame_indices == [0, 2]
    assert recovered.pose_sequence[1][23].x == .5
    assert state["reads"] == [1]
    assert state["settings"]["min_detection_confidence"] == .5
    assert state["closed"] and state["released"]


def test_crop_predictions_map_back_to_source_coordinates(monkeypatch):
    points = [Landmark(.55, .5, .1, 1) for _ in range(33)]
    setup_detector(monkeypatch, [None, points])
    recovered = recover_pose_gaps("fake.mp4", make_extraction())
    point = recovered.pose_sequence[1][23]
    assert point.x == pytest.approx(.545)
    assert point.y == pytest.approx(.5)
    assert point.z == pytest.approx(.09)


def test_distant_person_or_low_visibility_is_not_accepted(monkeypatch):
    distant = [Landmark(.95, .95, 0, 1) for _ in range(33)]
    invisible = [Landmark(.5, .5, 0, .1) for _ in range(33)]
    setup_detector(monkeypatch, [distant, invisible])
    recovered = recover_pose_gaps("fake.mp4", make_extraction())
    assert recovered.source_frame_indices == [0, 2]
    assert recovered.recovered_frame_indices == []


def test_failed_detection_keeps_gap_instead_of_inventing_coordinates(monkeypatch):
    setup_detector(monkeypatch, [None, None])
    recovered = recover_pose_gaps("fake.mp4", make_extraction())
    assert recovered.source_frame_indices == [0, 2]


def test_long_gap_is_not_processed():
    recovered = recover_pose_gaps("does-not-exist.mp4", make_extraction((0, 8)))
    assert recovered.source_frame_indices == [0, 8]


def test_unknown_timing_metadata_is_rejected():
    extraction = make_extraction()
    extraction.fps = None
    with pytest.raises(ValueError, match="requires source FPS"):
        recover_pose_gaps("fake.mp4", extraction)


def test_recovery_provenance_requires_real_result_indices():
    with pytest.raises(ValueError, match="sorted unique source indices"):
        PoseExtractionResult([], [], 0, recovered_frame_indices=[1])


def test_recovery_provenance_marks_metrics_as_review_required():
    from tests.test_squat_remaining_metrics import analyze, sample_extraction
    extraction = sample_extraction()
    extraction.recovered_frame_indices = [3]
    metrics = analyze(extraction).repetitions[0].metrics
    assert metrics["depth"].quality.status == "partial"
    assert metrics["depth"].quality.recovered_frames == 1
    assert metrics["depth"].quality.coverage == 1
    assert "re-detections" in metrics["depth"].quality.reason
