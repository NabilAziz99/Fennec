#!/usr/bin/env python3
"""
Pixel Art to Colored ASCII Art Converter

Specifically designed for pixel art images like the Fennec logo.
Creates colored terminal output using ANSI escape codes.
"""

import sys
from PIL import Image


# ANSI 256 color escape codes
def rgb_to_ansi256(r, g, b):
    """Convert RGB to nearest ANSI 256 color code."""
    # Check for grayscale
    if r == g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return round((r - 8) / 247 * 24) + 232

    # Color cube (6x6x6)
    return 16 + (36 * round(r / 255 * 5)) + (6 * round(g / 255 * 5)) + round(b / 255 * 5)


def get_ansi_color(r, g, b):
    """Get ANSI escape code for RGB color."""
    code = rgb_to_ansi256(r, g, b)
    return f"\033[38;5;{code}m"


RESET = "\033[0m"


def image_to_ascii(image_path, width=70, char="█", bg_threshold=40):
    """
    Convert a pixel art image to colored ASCII art.

    Args:
        image_path: Path to the image file
        width: Target width in characters
        char: Character to use for filled pixels (█ works great)
        bg_threshold: Brightness threshold below which pixels are treated as background

    Returns:
        String with ANSI color codes for terminal display
    """
    # Load image
    img = Image.open(image_path).convert("RGBA")

    # Calculate height to maintain aspect ratio
    # Terminal characters are roughly 2:1 height:width ratio
    aspect_ratio = img.height / img.width
    height = int(width * aspect_ratio * 0.5)

    # Resize image
    img = img.resize((width, height), Image.Resampling.NEAREST)

    lines = []
    for y in range(height):
        line = ""
        prev_color = None

        for x in range(width):
            r, g, b, a = img.getpixel((x, y))

            # Calculate brightness
            brightness = (r + g + b) / 3

            # Handle transparency OR dark background - use space
            if a < 128 or brightness < bg_threshold:
                if prev_color is not None:
                    line += RESET
                    prev_color = None
                line += " "
            else:
                color_code = get_ansi_color(r, g, b)
                if color_code != prev_color:
                    if prev_color is not None:
                        line += RESET
                    line += color_code
                    prev_color = color_code
                line += char

        if prev_color is not None:
            line += RESET
        lines.append(line)

    return "\n".join(lines)


def save_as_python_module(ascii_art, output_path):
    """Save the ASCII art as a Python module."""
    # We need to escape the string properly
    escaped = ascii_art.replace("\\", "\\\\").replace('"', '\\"')

    content = f'''"""
Auto-generated Fennec ASCII Art

Generated from pixel art image using pixelart_to_ascii.py
"""

FENNEC_ART = """{ascii_art}"""


def get_art():
    """Return the fennec ASCII art."""
    return FENNEC_ART
'''

    with open(output_path, 'w') as f:
        f.write(content)

    print(f"Saved to: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Convert pixel art to colored ASCII")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("-w", "--width", type=int, default=70, help="Width in characters")
    parser.add_argument("-c", "--char", default="█", help="Character to use")
    parser.add_argument("-o", "--output", help="Save to Python module")
    parser.add_argument("-p", "--preview", action="store_true", help="Preview only")

    args = parser.parse_args()

    print(f"Converting: {args.image}")
    print(f"Width: {args.width} chars")

    ascii_art = image_to_ascii(args.image, args.width, args.char)

    print("\n" + "=" * 60 + "\n")
    print(ascii_art)
    print("\n" + "=" * 60 + "\n")

    if args.output and not args.preview:
        save_as_python_module(ascii_art, args.output)


if __name__ == "__main__":
    main()
