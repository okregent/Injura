"""Bounded local video inspection and fresh default-model analysis."""

from dataclasses import dataclass
import hashlib

import cv2

from engine.pose.mediapipe_estimator import MediaPipePoseEstimator
from engine.pose.orientation import FacingDirection
from engine.pose.side import BodySide
from engine.squat.analyzer import SquatAnalyzer
from engine.squat.response import build_squat_response


class AnalysisError(Exception):
    def __init__(self, code, message, status=422):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


@dataclass(frozen=True)
class Limits:
    file_bytes: int = 25 * 1024 * 1024
    multipart_overhead: int = 64 * 1024
    frames: int = 1800
    width: int = 1920
    height: int = 1080

    def __post_init__(self):
        if any(type(value) is not int or value <= 0 for value in vars(self).values()):
            raise ValueError('limits must be positive integers')


def inspect_video(path, limits):
    capture = cv2.VideoCapture(str(path))
    count = 0
    try:
        if not capture.isOpened():
            raise AnalysisError('invalid_video', 'The uploaded file cannot be decoded as video.')
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            count += 1
            height, width = frame.shape[:2]
            if count > limits.frames or width > limits.width or height > limits.height:
                raise AnalysisError('video_limits_exceeded', 'Video frame count or dimensions exceed the supported limits.', 413)
        if not count:
            raise AnalysisError('invalid_video', 'The uploaded video contains no decodable frames.')
    finally:
        capture.release()


def analyze_video(path, side, facing, *, limits=Limits()):
    inspect_video(path, limits)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    estimator = MediaPipePoseEstimator(model_complexity=1)
    try:
        extraction = estimator.extract_with_metadata(str(path))
    finally:
        estimator.close()
    analysis = SquatAnalyzer().analyze(extraction, side=BodySide(side), facing_direction=FacingDirection(facing))
    # Public request data cannot assert capture approval or validated coaching.
    return build_squat_response(analysis, extraction, source_sha256=digest, facing=facing, include_overlay=True)
