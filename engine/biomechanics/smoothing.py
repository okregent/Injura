import math
from dataclasses import dataclass
from typing import Optional
from engine.pose.types import Landmark

# One Euro Filter — a low-latency noise filter for noisy real-time signals.
# Adapts its smoothing strength based on the speed of the signal:
#   - slow / still  → more smoothing (reduces jitter)
#   - fast moving   → less smoothing (reduces lag)
# Reference: https://gery.casiez.net/1euro/

def smoothing_factor(
        cutoff: float,  # cutoff frequency (Hz) — higher = less smoothing, lower = more smoothing
        dt: float,      # time delta between frames (seconds)
) -> float:
    # Converts cutoff frequency and time delta into an alpha blending factor (0 to 1)
    r = 2 * math.pi * cutoff * dt
    return r / (r + 1)

def exponential_smoothing(
        alpha: float,           # blending factor: 0 = keep old value entirely, 1 = take new value entirely
        current_value: float,   # new raw value from the current frame
        previous_value: float,  # smoothed value from the previous frame
) -> float:
    # Blends the new value with the previous smoothed value
    return alpha * current_value + (1 - alpha) * previous_value

@dataclass
class OneEuroFilter:
    # Controls smoothing at rest — lower value = more smoothing when the signal is slow
    min_cutoff: float = 1.0
    # Speed coefficient — higher value = less lag when the signal moves fast
    beta: float = 0.0
    # Cutoff frequency used when smoothing the derivative (velocity estimate)
    derivative_cutoff: float = 1.0

    # Last smoothed output value — None on the first frame
    previous_value: Optional[float] = None
    # Last smoothed derivative (velocity estimate)
    previous_derivative: float = 0.0

    def filter(
            self,
            value: float,  # raw input value from the current frame
            dt: float,     # time elapsed since the last frame (seconds)
    ) -> float:
        # On the first call, initialise and return the raw value unchanged
        if self.previous_value is None:
            self.previous_value = value
            return value

        # Estimate the rate of change (velocity) from the previous smoothed value
        derivative = (value - self.previous_value) / dt
        derivative_alpha = smoothing_factor(self.derivative_cutoff, dt)

        # Smooth the velocity estimate to reduce noise in the speed signal
        smoothed_derivative = exponential_smoothing(
            derivative_alpha,
            derivative,
            self.previous_derivative,
            )

        # Raise the cutoff when the signal is moving fast — reduces lag during motion
        cutoff = self.min_cutoff + self.beta * abs(smoothed_derivative)
        alpha = smoothing_factor(cutoff, dt)

        # Smooth the input value using the adaptive cutoff
        smoothed_value = exponential_smoothing(
            alpha,
            value,
            self.previous_value,
        )

        # Store state for the next frame
        self.previous_value = smoothed_value
        self.previous_derivative = smoothed_derivative

        return smoothed_value


@dataclass
class LandmarkOneEuroFilter:
    # Each spatial axis and visibility gets its own independent filter
    # because they are independent signals with potentially different noise characteristics
    x_filter: OneEuroFilter           # filters the horizontal position
    y_filter: OneEuroFilter           # filters the vertical position
    z_filter: OneEuroFilter           # filters the depth position
    visibility_filter: OneEuroFilter  # filters the detection confidence score

    @classmethod
    def create(
        cls,
        min_cutoff: float = 1.0,
        beta: float = 0.0,
        derivative_cutoff: float = 1.0,
    ) -> "LandmarkOneEuroFilter":
        # Convenience constructor — creates four filters with identical parameters
        return cls(
            x_filter=OneEuroFilter(min_cutoff, beta, derivative_cutoff),
            y_filter=OneEuroFilter(min_cutoff, beta, derivative_cutoff),
            z_filter=OneEuroFilter(min_cutoff, beta, derivative_cutoff),
            visibility_filter=OneEuroFilter(min_cutoff, beta, derivative_cutoff),
        )

    def filter(
        self,
        landmark: Landmark,  # raw landmark from the current frame
        dt: float,           # time elapsed since the last frame (seconds)
    ) -> Landmark:
        # Apply each axis filter independently and return a new smoothed Landmark
        return Landmark(
            x=self.x_filter.filter(landmark.x, dt),
            y=self.y_filter.filter(landmark.y, dt),
            z=self.z_filter.filter(landmark.z, dt),
            visibility=self.visibility_filter.filter(landmark.visibility, dt),
        )