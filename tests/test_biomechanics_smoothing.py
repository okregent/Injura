from engine.biomechanics.smoothing import (
    OneEuroFilter,
    LandmarkOneEuroFilter,
    smoothing_factor,
    exponential_smoothing,
)
from engine.pose.types import Landmark

DT = 1 / 30  # 30fps — standard frame delta throughout tests


# ---------------------------------------------------------------------------
# smoothing_factor
# ---------------------------------------------------------------------------

def test_smoothing_factor_is_between_zero_and_one():
    # alpha must always be a valid blending factor
    alpha = smoothing_factor(cutoff=1.0, dt=DT)
    assert 0 < alpha < 1

def test_smoothing_factor_increases_with_cutoff():
    # Higher cutoff = less smoothing = larger alpha
    alpha_low = smoothing_factor(cutoff=0.5, dt=DT)
    alpha_high = smoothing_factor(cutoff=5.0, dt=DT)
    assert alpha_low < alpha_high


# ---------------------------------------------------------------------------
# exponential_smoothing
# ---------------------------------------------------------------------------

def test_exponential_smoothing_alpha_one_returns_current():
    # alpha=1: trust the new value entirely, discard history
    result = exponential_smoothing(alpha=1.0, current_value=5.0, previous_value=0.0)
    assert result == 5.0

def test_exponential_smoothing_alpha_zero_returns_previous():
    # alpha=0: ignore the new value, keep history entirely
    result = exponential_smoothing(alpha=0.0, current_value=5.0, previous_value=2.0)
    assert result == 2.0

def test_exponential_smoothing_midpoint():
    # alpha=0.5: output is the midpoint of current and previous
    result = exponential_smoothing(alpha=0.5, current_value=4.0, previous_value=2.0)
    assert result == 3.0


# ---------------------------------------------------------------------------
# OneEuroFilter
# ---------------------------------------------------------------------------

def test_one_euro_filter_first_frame_passthrough():
    # First frame has no history — raw value must be returned unchanged
    f = OneEuroFilter()
    result = f.filter(value=3.14, dt=DT)
    assert result == 3.14

def test_one_euro_filter_state_initialised_after_first_frame():
    # After the first frame, previous_value should be set
    f = OneEuroFilter()
    f.filter(value=1.0, dt=DT)
    assert f.previous_value is not None

def test_one_euro_filter_reduces_noise():
    # A noisy signal oscillating around a constant should produce
    # a smoother output with a smaller range than the input.
    f = OneEuroFilter(min_cutoff=1.0, beta=0.0)

    noisy = [1.0, 1.2, 0.8, 1.2, 0.8, 1.15, 0.85, 1.1, 0.9, 1.0]
    smoothed = [f.filter(v, DT) for v in noisy]

    input_range = max(noisy) - min(noisy)
    output_range = max(smoothed) - min(smoothed)

    assert output_range < input_range

def test_one_euro_filter_stable_input_stays_stable():
    # A constant input should produce a stable output after the first frame
    f = OneEuroFilter()
    outputs = [f.filter(1.0, DT) for _ in range(10)]

    # All outputs after the first should be very close to 1.0
    assert all(abs(v - 1.0) < 0.01 for v in outputs[1:])

def test_one_euro_filter_beta_increases_responsiveness():
    # beta > 0 allows the filter to respond faster during fast movement.
    # After a large step change, a filter with beta should track the new
    # value more closely than one without.
    dt = DT

    f_no_beta  = OneEuroFilter(min_cutoff=1.0, beta=0.0)
    f_with_beta = OneEuroFilter(min_cutoff=1.0, beta=2.0)

    # Initialise both at 0.0
    f_no_beta.filter(0.0, dt)
    f_with_beta.filter(0.0, dt)

    # Step to 10.0 and run for several frames
    for _ in range(15):
        out_no_beta   = f_no_beta.filter(10.0, dt)
        out_with_beta = f_with_beta.filter(10.0, dt)

    # The filter with beta should have tracked the step more closely
    assert out_with_beta > out_no_beta


# ---------------------------------------------------------------------------
# LandmarkOneEuroFilter
# ---------------------------------------------------------------------------

def test_landmark_filter_first_frame_passthrough():
    # First frame: all axes should pass through unchanged
    lf = LandmarkOneEuroFilter.create()
    landmark = Landmark(x=0.5, y=0.3, z=0.1, visibility=0.9)
    result = lf.filter(landmark, dt=DT)

    assert result.x == landmark.x
    assert result.y == landmark.y
    assert result.z == landmark.z
    assert result.visibility == landmark.visibility

def test_landmark_filter_returns_landmark_type():
    # Output must be a Landmark instance, not a raw tuple or other type
    lf = LandmarkOneEuroFilter.create()
    result = lf.filter(Landmark(x=0.5, y=0.3, z=0.1, visibility=0.9), dt=DT)
    assert isinstance(result, Landmark)

def test_landmark_filter_axes_are_independent():
    # Noise on one axis must not bleed into another axis.
    # x is held constant while y oscillates wildly — x output should remain stable.
    lf = LandmarkOneEuroFilter.create(min_cutoff=1.0, beta=0.0)

    noisy_y = [0.0, 1.0, -1.0, 1.0, -1.0, 1.0]
    x_outputs = [
        lf.filter(Landmark(x=1.0, y=y, z=0.0, visibility=1.0), DT).x
        for y in noisy_y
    ]

    x_range = max(x_outputs) - min(x_outputs)
    assert x_range < 0.05

def test_landmark_filter_create_applies_params_to_all_axes():
    # create() should apply custom parameters to all four internal filters
    lf = LandmarkOneEuroFilter.create(min_cutoff=2.0, beta=0.5, derivative_cutoff=1.5)

    for axis_filter in [lf.x_filter, lf.y_filter, lf.z_filter, lf.visibility_filter]:
        assert axis_filter.min_cutoff == 2.0
        assert axis_filter.beta == 0.5
        assert axis_filter.derivative_cutoff == 1.5

def test_landmark_filter_reduces_noise_on_x():
    # Noisy x values should be smoothed — output range should be smaller than input range
    lf = LandmarkOneEuroFilter.create(min_cutoff=1.0, beta=0.0)

    noisy_x = [0.5, 0.7, 0.3, 0.7, 0.3, 0.65, 0.35, 0.6, 0.4, 0.5]
    x_outputs = [
        lf.filter(Landmark(x=x, y=0.0, z=0.0, visibility=1.0), DT).x
        for x in noisy_x
    ]

    input_range = max(noisy_x) - min(noisy_x)
    output_range = max(x_outputs) - min(x_outputs)

    assert output_range < input_range
