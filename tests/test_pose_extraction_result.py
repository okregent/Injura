import pytest

from engine.pose.types import Landmark, PoseExtractionResult


def make_frame():
    return [Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0)]


def test_pose_extraction_result_preserves_source_frame_mapping():
    result = PoseExtractionResult(
        pose_sequence=[make_frame(), make_frame()],
        source_frame_indices=[1, 3],
        source_frame_count=4,
    )

    assert result.source_frame_indices == [1, 3]
    assert result.source_frame_count == 4


def test_pose_extraction_result_rejects_mapping_length_mismatch():
    with pytest.raises(ValueError, match="must have the same length"):
        PoseExtractionResult(
            pose_sequence=[make_frame()],
            source_frame_indices=[],
            source_frame_count=1,
        )


def test_pose_extraction_result_rejects_unsorted_mapping():
    with pytest.raises(ValueError, match="strictly increasing"):
        PoseExtractionResult(
            pose_sequence=[make_frame(), make_frame()],
            source_frame_indices=[2, 1],
            source_frame_count=3,
        )


def test_pose_extraction_result_keeps_image_size():
    result = PoseExtractionResult([], [], 0, image_size=(1920, 1080))
    assert result.image_size == (1920, 1080)


@pytest.mark.parametrize("image_size", [(0, 1080), (1920, -1), (1.5, 2), (True, 2), (1,)])
def test_pose_extraction_result_rejects_invalid_image_size(image_size):
    with pytest.raises(ValueError, match="positive integer width and height"):
        PoseExtractionResult([], [], 0, image_size=image_size)


@pytest.mark.parametrize("has_pose", [True, False])
def test_estimator_extracts_size_from_decoded_frames(monkeypatch, has_pose):
    from types import SimpleNamespace

    import numpy as np
    import engine.pose.mediapipe_estimator as module

    class FakeCapture:
        def __init__(self):
            self.frames = iter([np.zeros((108, 192, 3), dtype=np.uint8)])
            self.released = False

        def isOpened(self):
            return True

        def get(self, property_id):
            return 30.0

        def read(self):
            frame = next(self.frames, None)
            return frame is not None, frame

        def release(self):
            self.released = True

    capture = FakeCapture()
    monkeypatch.setattr(module.cv2, "VideoCapture", lambda path: capture)
    monkeypatch.setattr(module.cv2, "destroyAllWindows", lambda: None)
    estimator = module.MediaPipePoseEstimator.__new__(module.MediaPipePoseEstimator)
    pose = SimpleNamespace(landmark=make_frame()) if has_pose else None
    estimator.pose = SimpleNamespace(
        process=lambda frame: SimpleNamespace(pose_landmarks=pose),
    )

    result = estimator.extract_with_metadata("fake.mp4")
    assert result.image_size == (192, 108)
    assert result.fps == 30.0
    assert result.source_frame_count == 1
    assert result.source_frame_indices == ([0] if has_pose else [])
    assert capture.released

