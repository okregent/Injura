from dataclasses import dataclass
from engine.squat.phases import SquatPhase


@dataclass
class SquatRep:
    """Inclusive analysis indices for one detected repetition.

    ``bottom_index`` is the final frame classified as ``BOTTOM``. It is not
    guaranteed to be the frame with the maximum hip y-value; metrics that need
    the physical deepest point must calculate it from their input signal.
    """

    start_index: int
    bottom_index: int
    end_index: int


def detect_squat_reps(phases: list[SquatPhase]) -> list[SquatRep]:
    reps = []

    in_rep = False
    start_index = None
    bottom_index = None

    for i, phase in enumerate(phases):
        if not in_rep and phase == SquatPhase.DESCENDING:
            in_rep = True
            start_index = i
            bottom_index = None

        elif in_rep and phase == SquatPhase.BOTTOM:
            bottom_index = i

        elif in_rep and phase in (SquatPhase.ASCENDING, SquatPhase.LOCKOUT, SquatPhase.STANDING):
            if bottom_index is not None and phase in (SquatPhase.LOCKOUT, SquatPhase.STANDING):
                reps.append(
                    SquatRep(
                        start_index=start_index,
                        bottom_index=bottom_index,
                        end_index=i,
                    )
                )
                in_rep = False
                start_index = None
                bottom_index = None

    return reps
