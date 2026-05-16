
from abc import ABC, abstractmethod

from .types import PoseSequence

class BasePoseEstimator(ABC):
    @abstractmethod
    def extract(self, video_pat: str) -> PoseSequence:
        pass
