"""
Fennec AI CLI Banner

Animated banner with simultaneous effects for fennec art and FENNEC title.
Fennec animation is slower and finishes after the title.
"""

import sys
import time
import random
import re
from typing import Optional, List

# Try to import generated ASCII art from image
try:
    from .generated_art import FENNEC_ART
    HAS_GENERATED_ART = True
except ImportError:
    HAS_GENERATED_ART = False
    FENNEC_ART = None


# ANSI Color codes
class COLORS:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    CORAL = "\033[38;5;203m"
    ORANGE = "\033[38;2;255;140;0m"
    DARK_ORANGE = "\033[38;2;200;100;50m"
    WARM_RED = "\033[38;2;220;80;60m"
    YELLOW = "\033[38;2;255;200;0m"
    BROWN = "\033[38;2;139;90;43m"
    CLEAR_LINE = "\033[2K"
    CURSOR_UP = "\033[1A"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"
    CLEAR_SCREEN = "\033[2J"
    HOME = "\033[H"


# Big FENNEC ASCII art title
FENNEC_TITLE = r"""
███████╗███████╗███╗   ██╗███╗   ██╗███████╗ ██████╗
██╔════╝██╔════╝████╗  ██║████╗  ██║██╔════╝██╔════╝
█████╗  █████╗  ██╔██╗ ██║██╔██╗ ██║█████╗  ██║
██╔══╝  ██╔══╝  ██║╚██╗██║██║╚██╗██║██╔══╝  ██║
██║     ███████╗██║ ╚████║██║ ╚████║███████╗╚██████╗
╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚═════╝
""".strip()

# Glitch characters for effect
GLITCH_CHARS = "█▓▒░╔╗╚╝║═╬╣╠╩╦"
GLITCH_CHARS_SIMPLE = "▓▒░·.,"

# Fallback text-only banner if no generated art
FALLBACK_BANNER = """
No fennec art generated yet!

To generate the ASCII art from your fennec image, run:
    python branding/generate_art.py /path/to/fennec_image.png

"""


def _supports_color() -> bool:
    """Check if terminal supports color."""
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def get_line_color(line_idx: int, use_color: bool = True) -> str:
    """Get color for a specific line index (gradient effect)."""
    if not use_color:
        return ""
    if line_idx < 2:
        return COLORS.ORANGE
    elif line_idx < 4:
        return COLORS.DARK_ORANGE
    else:
        return COLORS.WARM_RED


def get_title_art(use_color: bool = True) -> str:
    """Get the big FENNEC title."""
    title = FENNEC_TITLE

    if use_color:
        colored_lines = []
        lines = title.split('\n')
        for i, line in enumerate(lines):
            color = get_line_color(i, use_color)
            colored_lines.append(f"{color}{line}{COLORS.RESET}")
        return '\n'.join(colored_lines)

    return title


def get_subtitle(use_color: bool = True) -> str:
    """Get the subtitle text."""
    subtitle = "          Red Team Autonomous Penetration Testing AI"
    if use_color:
        return f"{COLORS.DIM}{subtitle}{COLORS.RESET}"
    return subtitle


def get_fennec_art() -> str:
    """Get the fennec fox ASCII art."""
    if HAS_GENERATED_ART and FENNEC_ART:
        return FENNEC_ART
    return FALLBACK_BANNER


def get_banner(use_color: Optional[bool] = None, include_border: bool = True) -> str:
    """Get the complete Fennec AI banner (static version)."""
    if use_color is None:
        use_color = _supports_color()

    fennec_art = get_fennec_art()
    title = get_title_art(use_color)
    subtitle = get_subtitle(use_color)

    if include_border:
        if use_color:
            border = f"{COLORS.WARM_RED}{'═' * 72}{COLORS.RESET}"
        else:
            border = '═' * 72

        banner = f"""
{border}

{fennec_art}
{title}
{subtitle}

{border}
"""
    else:
        banner = f"""
{fennec_art}
{title}
{subtitle}
"""

    return banner


def move_cursor_up(lines: int) -> None:
    """Move cursor up N lines."""
    if lines > 0:
        sys.stdout.write(f"\033[{lines}A")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def get_visible_length(text: str) -> int:
    """Get the visible length of text (excluding ANSI codes)."""
    return len(strip_ansi(text))


def render_fennec_frame(lines: List[str], progress: float, use_color: bool = True) -> List[str]:
    """Render a single frame of the fennec animation at given progress (0.0 to 1.0)."""
    result = []

    for line_idx, line in enumerate(lines):
        if not line.strip():
            result.append("")
            continue

        if progress < 0.2:
            # Early phase: mostly empty with very sparse glitches
            visible = strip_ansi(line)
            output = ""
            for char in visible:
                if char != ' ' and random.random() < progress * 3:
                    glitch = random.choice(GLITCH_CHARS_SIMPLE)
                    output += f"{COLORS.DIM}{COLORS.BROWN}{glitch}{COLORS.RESET}"
                else:
                    output += ' '
            result.append(output)

        elif progress < 0.6:
            # Middle phase: mix of glitches and partial reveal
            output = ""
            i = 0
            current_color = ""

            while i < len(line):
                if line[i] == '\033':
                    end = i + 1
                    while end < len(line) and line[end] not in 'mHJK':
                        end += 1
                    if end < len(line):
                        end += 1
                    current_color = line[i:end]
                    i = end
                else:
                    char = line[i]
                    if char != ' ':
                        reveal_chance = (progress - 0.2) / 0.4
                        if random.random() < reveal_chance:
                            output += current_color + char
                        else:
                            glitch = random.choice(GLITCH_CHARS_SIMPLE)
                            output += f"{COLORS.DIM}{glitch}"
                    else:
                        output += ' '
                    i += 1
            result.append(f"{output}{COLORS.RESET}")

        elif progress < 0.95:
            # Late phase: mostly revealed with occasional flicker
            reveal_chance = (progress - 0.6) / 0.35
            if random.random() < reveal_chance * 0.9:
                result.append(line)
            else:
                visible = strip_ansi(line)
                output = ""
                for char in visible:
                    if char != ' ' and random.random() < 0.2:
                        output += f"{COLORS.DIM}{random.choice(GLITCH_CHARS_SIMPLE)}{COLORS.RESET}"
                    elif char != ' ':
                        output += f"{COLORS.BROWN}{char}{COLORS.RESET}"
                    else:
                        output += ' '
                result.append(output)
        else:
            # Final: show actual line
            result.append(line)

    return result


def render_title_frame(lines: List[str], progress: float, style: str, use_color: bool = True) -> List[str]:
    """Render a single frame of the title animation at given progress (0.0 to 1.0)."""
    result = []
    width = max(len(line) for line in lines)
    lines = [line.ljust(width) for line in lines]

    if style == "glitch":
        for y, line in enumerate(lines):
            color = get_line_color(y, use_color)
            output = ""
            for char in line:
                if char == ' ':
                    output += ' '
                elif random.random() < progress:
                    output += f"{color}{char}"
                else:
                    glitch = random.choice(GLITCH_CHARS)
                    glitch_color = random.choice([COLORS.ORANGE, COLORS.YELLOW, COLORS.WARM_RED, COLORS.DIM])
                    output += f"{glitch_color}{glitch}"
            result.append(f"{output}{COLORS.RESET}")

    elif style == "scanline":
        col = int(progress * (width + 3))
        for y, line in enumerate(lines):
            color = get_line_color(y, use_color)
            output = ""
            for x, char in enumerate(line):
                if x < col - 2:
                    output += f"{color}{char}"
                elif x == col - 1 or x == col:
                    if char != ' ':
                        output += f"{COLORS.YELLOW}{COLORS.BOLD}█{COLORS.RESET}"
                    else:
                        output += f"{COLORS.YELLOW}░{COLORS.RESET}"
                else:
                    output += " "
            result.append(f"{output}{COLORS.RESET}")

    elif style == "matrix":
        # For matrix, we need to track revealed positions
        num_chars = sum(1 for line in lines for char in line if char != ' ')
        chars_to_reveal = int(progress * num_chars)

        # Get positions and shuffle deterministically based on progress
        random.seed(42)  # Fixed seed for consistent reveal pattern
        positions = [(y, x) for y, line in enumerate(lines) for x, char in enumerate(line) if char != ' ']
        random.shuffle(positions)
        random.seed()  # Reset to random

        revealed = set(positions[:chars_to_reveal])

        for y, line in enumerate(lines):
            color = get_line_color(y, use_color)
            output = ""
            for x, char in enumerate(line):
                if (y, x) in revealed:
                    output += f"{color}{char}"
                elif char != ' ' and random.random() < 0.3:
                    glitch = random.choice(GLITCH_CHARS)
                    output += f"{COLORS.DIM}{glitch}"
                else:
                    output += " "
            result.append(f"{output}{COLORS.RESET}")

    else:
        # No animation
        for y, line in enumerate(lines):
            color = get_line_color(y, use_color)
            result.append(f"{color}{line}{COLORS.RESET}")

    return result


def print_simultaneous_animation(use_color: bool = True, animation_style: str = "glitch") -> None:
    """
    Print both fennec and title animations simultaneously.
    Fennec animation is slower and finishes after the title.
    """
    fennec_art = get_fennec_art()
    if fennec_art == FALLBACK_BANNER:
        print(fennec_art)
        print(get_title_art(use_color))
        return

    fennec_lines = fennec_art.split('\n')
    title_lines = FENNEC_TITLE.split('\n')

    fennec_height = len(fennec_lines)
    title_height = len(title_lines)
    total_height = fennec_height + title_height

    sys.stdout.write(COLORS.HIDE_CURSOR)
    sys.stdout.flush()

    try:
        # Print empty placeholder lines
        for i in range(total_height):
            print()

        # Animation parameters
        # Title finishes at 60% of total time, fennec continues until 100%
        total_frames = 50
        title_finish_frame = 30  # Title completes faster

        for frame in range(total_frames + 1):
            # Calculate progress for each animation
            # Title: 0 to 1 over first 30 frames, then stays at 1
            title_progress = min(1.0, frame / title_finish_frame)

            # Fennec: 0 to 1 over all 50 frames (slower)
            fennec_progress = frame / total_frames

            move_cursor_up(total_height)

            # Render fennec frame
            fennec_frame = render_fennec_frame(fennec_lines, fennec_progress, use_color)
            for line in fennec_frame:
                print(line)

            # Render title frame
            if title_progress >= 1.0:
                # Title animation complete, show final
                for y, line in enumerate(title_lines):
                    color = get_line_color(y, use_color)
                    print(f"{color}{line}{COLORS.RESET}")
            else:
                title_frame = render_title_frame(title_lines, title_progress, animation_style, use_color)
                for line in title_frame:
                    print(line)

            sys.stdout.flush()

            # Timing: slower for fennec to be more dramatic
            if frame < 10:
                time.sleep(0.08)
            elif frame < 30:
                time.sleep(0.06)
            else:
                time.sleep(0.10)  # Slower at the end for fennec finale

        # Final clean render
        move_cursor_up(total_height)
        for line in fennec_lines:
            print(line)
        for y, line in enumerate(title_lines):
            color = get_line_color(y, use_color)
            print(f"{color}{line}{COLORS.RESET}")

    finally:
        sys.stdout.write(COLORS.SHOW_CURSOR)
        sys.stdout.flush()


def print_banner(use_color: Optional[bool] = None, include_border: bool = True,
                 animated: bool = True, animation_style: str = "glitch", file=None) -> None:
    """
    Print the Fennec AI banner to terminal.

    animation_style options: "glitch", "matrix", "scanline", "none"
    """
    if file is None:
        file = sys.stdout

    if use_color is None:
        use_color = _supports_color()

    is_interactive = animated and file == sys.stdout and _supports_color()

    # Border
    if include_border:
        if use_color:
            border = f"{COLORS.WARM_RED}{'═' * 72}{COLORS.RESET}"
        else:
            border = '═' * 72
        print(f"\n{border}\n", file=file)

    # Simultaneous animation for both fennec and title
    if is_interactive:
        print_simultaneous_animation(use_color, animation_style)
    else:
        fennec_art = get_fennec_art()
        print(fennec_art, file=file)
        title = get_title_art(use_color)
        print(title, file=file)

    # Subtitle
    subtitle = get_subtitle(use_color)
    print(f"\n{subtitle}", file=file)

    # Bottom border
    if include_border:
        print(f"\n{border}\n", file=file)


def print_startup_message(version: str = "1.0.0", target: Optional[str] = None,
                          animated: bool = True, animation_style: str = "glitch") -> None:
    """Print startup message with banner and info."""
    use_color = _supports_color()
    print_banner(use_color=use_color, animated=animated, animation_style=animation_style)

    if use_color:
        print(f"  {COLORS.DIM}Version:{COLORS.RESET} {COLORS.ORANGE}{version}{COLORS.RESET}")
        if target:
            print(f"  {COLORS.DIM}Target:{COLORS.RESET}  {COLORS.BRIGHT_GREEN}{target}{COLORS.RESET}")
    else:
        print(f"  Version: {version}")
        if target:
            print(f"  Target:  {target}")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--style", "-s", choices=["glitch", "matrix", "scanline", "none"],
                        default="glitch", help="Animation style for title")
    args = parser.parse_args()
    print_banner(animation_style=args.style)
