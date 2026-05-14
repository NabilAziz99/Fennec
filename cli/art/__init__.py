"""
Fennec AI Branding Module

Provides ASCII art banners and landing page for the Fennec AI CLI.

To generate ASCII art from your fennec image:
    python -m branding.generate_art /path/to/fennec_image.png
"""

from .banner import (
    print_banner,
    print_startup_message,
    get_banner,
    COLORS,
)
from .landing import show_landing

__all__ = [
    "print_banner",
    "print_startup_message",
    "get_banner",
    "COLORS",
    "show_landing",
]
