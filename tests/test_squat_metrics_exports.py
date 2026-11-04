from engine.squat.metrics import (
    KneeTravelResult,
    SquatDepthResult,
    TorsoLeanResult,
    calculate_knee_travel,
    calculate_squat_depth,
    calculate_torso_lean,
)


def test_squat_metrics_package_exports_public_api():
    assert KneeTravelResult is not None
    assert SquatDepthResult is not None
    assert TorsoLeanResult is not None
    assert callable(calculate_knee_travel)
    assert callable(calculate_squat_depth)
    assert callable(calculate_torso_lean)

