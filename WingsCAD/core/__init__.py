# core/__init__.py

from .naca4 import generate_naca4_full
from .naca5 import generate_naca5_full
from .naca6 import generate_naca6_full

__all__ = [
    "generate_naca4_full",
    "generate_naca5_full",
    "generate_naca6_full",
]
