"""Scientific numerical precision and measurement uncertainty formatting utilities.

Prevents false precision across kinematic, geometric, and temporal measurements,
guaranteeing that displayed figures are grounded in sensor resolution and physical uncertainty.
"""

import math
from typing import Optional, Tuple


def calculate_combined_uncertainty(sigma_a: float, sigma_b: float) -> float:
    """Calculate quadratic combined standard uncertainty: sqrt(sigma_a^2 + sigma_b^2)."""
    return math.sqrt(sigma_a**2 + sigma_b**2)


def is_statistically_distinguishable(
    observed_delta: float,
    combined_uncertainty: float,
) -> Tuple[bool, str]:
    """Determine whether an observed difference exceeds combined measurement uncertainty.

    Returns:
        (is_distinguishable, assessment_label)
    """
    abs_delta = abs(observed_delta)
    if abs_delta <= combined_uncertainty:
        return False, "NOT_CLEARLY_DISTINGUISHABLE_WITHIN_UNCERTAINTY"
    return True, "DISTINGUISHABLE_BEYOND_UNCERTAINTY"


def format_spatial_distance(
    meters: Optional[float],
    uncertainty_m: float = 0.20,
    include_uncertainty: bool = True,
) -> str:
    """Format spatial distance with physical GPS/Cartesian resolution (±0.20m).

    Prevents false precision like '0.42381729 m'.
    """
    if meters is None:
        return "N/A"
    rounded_val = round(meters, 2)
    if include_uncertainty:
        return f"{rounded_val:.2f} m (±{uncertainty_m:.2f} m)"
    return f"{rounded_val:.2f} m"


def format_velocity(
    kmh: Optional[float],
    uncertainty_kmh: float = 2.0,
    include_uncertainty: bool = True,
) -> str:
    """Format velocity with wheel speed transducer resolution (±2.0 km/h).

    Prevents false precision like '231.84719 km/h'.
    """
    if kmh is None:
        return "N/A"
    rounded_val = round(kmh, 1)
    if include_uncertainty:
        return f"{rounded_val:.1f} km/h (±{uncertainty_kmh:.1f} km/h)"
    return f"{rounded_val:.1f} km/h"


def format_time_delta(
    seconds: Optional[float],
    uncertainty_sec: float = 0.040,
    include_uncertainty: bool = True,
) -> str:
    """Format time interval with 25Hz resampling cadence resolution (±0.040s)."""
    if seconds is None:
        return "N/A"
    rounded_val = round(seconds, 3)
    if include_uncertainty:
        return f"{rounded_val:+.3f} s (±{uncertainty_sec:.3f} s)"
    return f"{rounded_val:+.3f} s"


def format_measurement_with_uncertainty(
    value: Optional[float],
    uncertainty: Optional[float] = None,
    unit: str = "",
    decimals: int = 2,
) -> str:
    """Generic formatter ensuring value is not displayed with unwarranted precision."""
    if value is None:
        return "N/A"
    val_str = f"{value:.{decimals}f}"
    if uncertainty is not None:
        unc_str = f"±{uncertainty:.{decimals}f}"
        if unit:
            return f"{val_str} {unit} ({unc_str} {unit})"
        return f"{val_str} ({unc_str})"
    if unit:
        return f"{val_str} {unit}"
    return val_str
