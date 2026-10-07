# © 2026 Curtis Ray Dyess · Crimson Rose LLC
"""Pandora — pluggable scare platform (DLC tier).

Levels 1 (atmosphere) and 2 (dread) only. Level 3 (startle) ships later,
behind Curtis's consent gate.
"""

from .core import Engine, armed
from .guardrails import (
    Guardrails,
    GuardrailError,
    curtis_approval_code,
)
from .biometrics import BiometricTrip, SimulatedCuff, CuffReader

__version__ = "0.3.0"

__all__ = ["Engine", "armed", "Guardrails", "GuardrailError",
           "curtis_approval_code", "BiometricTrip", "SimulatedCuff",
           "CuffReader", "__version__"]
