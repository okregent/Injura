import numpy as np
import pytest

from apps.api import service
from tests.test_e3_workflow import three_cycle_extraction


class Capture:
    def __init__(self, frames):
        self.frames, self.closed = iter(frames), False
    def isOpened(self):
        return True
    def read(self):
        frame = next(self.frames, None)
        return frame is not None, frame
    def release(self):
        self.closed = True


@pytest.mark.parametrize('count,width,code', [(0, 10, 'invalid_video'), (3, 10, 'video_limits_exceeded'),
                                            (1, 21, 'video_limits_exceeded')])
def test_preflight_enforces_actual_frames_and_dimensions(monkeypatch, count, width, code):
    capture = Capture([np.zeros((10, width, 3), dtype=np.uint8)] * count)
    monkeypatch.setattr(service.cv2, 'VideoCapture', lambda _: capture)
    with pytest.raises(service.AnalysisError) as error:
        service.inspect_video('fixture', service.Limits(frames=2, width=20))
    assert error.value.code == code and capture.closed


def test_default_engine_response_retains_unknown_capture_and_closes_model(tmp_path, monkeypatch):
    source = tmp_path / 'fixture.mp4'
    source.write_bytes(b'synthetic-source')
    monkeypatch.setattr(service, 'inspect_video', lambda *args: None)
    instances = []
    class Estimator:
        def __init__(self, model_complexity):
            assert model_complexity == 1
            self.closed = False
            instances.append(self)
        def extract_with_metadata(self, path):
            return three_cycle_extraction()
        def close(self):
            self.closed = True
    monkeypatch.setattr(service, 'MediaPipePoseEstimator', Estimator)
    result = service.analyze_video(source, 'left', 'left')
    assert result['overview']['state'] == 'capture_review'
    assert result['overview']['coaching_status'] == 'pending_validation'
    assert result['overview']['detected_cycles'] == 3
    assert instances[0].closed
