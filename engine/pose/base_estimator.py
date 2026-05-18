
from abc import ABC, abstractmethod

from .types import PoseSequence

class BasePoseEstimator(ABC):
    @abstractmethod
    def extract(self, video_path: str) -> PoseSequence:
        pass
    @abstractmethod
    def close(self):
        pass
