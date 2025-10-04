"""
Default constants for uniqueness evaluation configuration.

Collected in a class with class variables as requested.
"""

from __future__ import annotations


class Defaults:
    """Default values for UniquenessConfig."""

    MATCHER_ENGINE: str = "auto"
    WEIGHTS: dict[str, int] = {"domain": 25, "appfollow": 25, "play": 20, "google": 30}
    THRESHOLDS: dict[str, int] = {"distinct": 80, "likely": 60, "border": 40}

