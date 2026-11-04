"""Frame-boundary timing for constant-frame-rate video."""

from dataclasses import dataclass

from engine.pose.types import PoseExtractionResult
from engine.squat.phases import SquatPhase
from engine.squat.reps import SquatRep


@dataclass
class RepTimingResult:
    descent_seconds: float
    bottom_seconds: float
    ascent_seconds: float
    total_seconds: float
    start_source_frame: int
    end_source_frame: int


def calculate_rep_timing(
    extraction: PoseExtractionResult, phases: list[SquatPhase], rep: SquatRep,
) -> RepTimingResult:
    """Measure [rep.start, rep.end) intervals; end is the return-to-standing boundary.

    Require contiguous source frames and DESCENDING -> BOTTOM -> ASCENDING.
    Missing frames or unknown phases cannot be assigned invented durations.
    FPS timing assumes constant frame rate; variable-frame-rate PTS is deferred.
    """
    if extraction.fps is None:
        raise ValueError("video FPS is unavailable")
    if len(phases) != len(extraction.pose_sequence):
        raise ValueError("phases must align with the pose sequence")
    if rep.start_index < 0 or rep.end_index >= len(phases) or rep.start_index >= rep.end_index:
        raise ValueError("invalid repetition timing range")
    source = extraction.source_frame_indices[rep.start_index:rep.end_index + 1]
    if any(b - a != 1 for a, b in zip(source, source[1:])):
        raise ValueError("missing source frames prevent phase timing")
    if phases[rep.end_index] not in (SquatPhase.STANDING, SquatPhase.LOCKOUT):
        raise ValueError("repetition must end at a standing or lockout boundary")
    segment = phases[rep.start_index:rep.end_index]
    runs = [phase for index, phase in enumerate(segment) if index == 0 or phase != segment[index - 1]]
    expected = [SquatPhase.DESCENDING, SquatPhase.BOTTOM, SquatPhase.ASCENDING]
    if runs != expected:
        raise ValueError("timing requires ordered descent, bottom, and ascent phases")
    durations = [segment.count(phase) / extraction.fps for phase in expected]
    return RepTimingResult(*durations, (source[-1] - source[0]) / extraction.fps, source[0], source[-1])
