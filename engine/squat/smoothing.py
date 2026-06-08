from engine.squat.phases import SquatPhase


def smooth_squat_phases(
        phases: list[SquatPhase],
        min_duration: int = 3,
) -> list[SquatPhase]:
    if not phases:
        return []

    if min_duration <= 1:
        return phases.copy()

    smoothed = phases.copy()

    segments = []
    start = 0
    current_phase = phases[0]

    for i in range(1, len(phases)):
        if phases[i] != current_phase:
            segments.append((start, i - 1, current_phase))
            start = i
            current_phase = phases[i]

    segments.append((start, len(phases) - 1, current_phase))

    for idx, (start, end, phase) in enumerate(segments):
        duration = end - start + 1

        if duration >= min_duration:
            continue

        if idx == 0 or idx == len(segments) - 1:
            continue

        prev_phase = segments[idx - 1][2]
        next_phase = segments[idx + 1][2]

        if prev_phase != next_phase:
            continue

        for frame_idx in range(start, end + 1):
            smoothed[frame_idx] = prev_phase

    return smoothed
