from engine.squat.metrics import (
    BottomJointAnglesResult,
    calculate_bottom_joint_angles,
    KneeTravelResult,
    KneeTravelRecordingConditions,
    KneeTravelNormalizationUnavailable,
    NormalizedKneeTravelResult,
    SquatDepthResult,
    TorsoLeanResult,
    calculate_knee_travel,
    calculate_normalized_knee_travel,
    calculate_knee_travel_from_features,
    calculate_squat_depth,
    calculate_squat_depth_from_features,
    calculate_torso_lean,
    calculate_torso_lean_from_features,
)


def test_squat_metrics_package_exports_public_api():
    assert BottomJointAnglesResult is not None
    assert callable(calculate_bottom_joint_angles)
    assert KneeTravelResult is not None
    assert KneeTravelRecordingConditions is not None
    assert issubclass(KneeTravelNormalizationUnavailable, ValueError)
    assert NormalizedKneeTravelResult is not None
    assert callable(calculate_normalized_knee_travel)
    assert SquatDepthResult is not None
    assert TorsoLeanResult is not None
    assert callable(calculate_knee_travel)
    assert callable(calculate_squat_depth)
    assert callable(calculate_torso_lean)
    assert callable(calculate_knee_travel_from_features)
    assert callable(calculate_squat_depth_from_features)
    assert callable(calculate_torso_lean_from_features)

