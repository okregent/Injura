"""Shared entry point for exercise analysis of extracted pose data."""

from abc import ABC, abstractmethod
from engine.pose.types import PoseExtractionResult


class ExerciseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, extraction: PoseExtractionResult, **options):
        """Return exercise measurements and explicit availability information."""
        raise NotImplementedError
