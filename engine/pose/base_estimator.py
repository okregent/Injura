
from abc import ABC, abstractmethod

from .types import PoseExtractionResult, PoseSequence

class BasePoseEstimator(ABC):
    @abstractmethod
    def extract(self, video_path: str) -> PoseSequence:
        pass

    @abstractmethod
    def extract_with_metadata(self, video_path: str) -> PoseExtractionResult:
        pass

    @abstractmethod
    def close(self):
        pass
