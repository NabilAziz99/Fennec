"""
Fennec AI Landing Page

Matrix-style CLI landing page with floating words and ASCII art.
Orange and black fennec aesthetic.
"""

import sys
import time
import random
import os
from typing import List, Tuple

# ANSI Color codes - Orange/Black fennec aesthetic
class HACKER:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Oranges (fennec colors)
    GREEN = "\033[38;2;200;100;50m"  # Actually dark orange
    BRIGHT_GREEN = "\033[38;2;255;140;0m"  # Bright orange
    DARK_GREEN = "\033[38;2;100;50;25m"  # Dark brown
    MATRIX_GREEN = "\033[38;2;255;150;50m"  # Bright orange
    LIME = "\033[38;2;220;120;40m"  # Orange

    # Accents
    CYAN = "\033[38;2;255;200;100m"  # Yellow-orange
    WHITE = "\033[97m"
    BLACK_BG = "\033[40m"

    # Control
    CLEAR_SCREEN = "\033[2J"
    HOME = "\033[H"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"
    CLEAR_LINE = "\033[2K"


# Fennec ASCII art in simple form for landing
FENNEC_SIMPLE = r"""
                    /\___/\
                   /       \
                  |  ^   ^  |
                  |    v    |
                   \  ===  /
                    \_____/
"""

# Big stylized FENNEC for landing
FENNEC_LOGO = r"""
    ███████╗███████╗███╗   ██╗███╗   ██╗███████╗ ██████╗
    ██╔════╝██╔════╝████╗  ██║████╗  ██║██╔════╝██╔════╝
    █████╗  █████╗  ██╔██╗ ██║██╔██╗ ██║█████╗  ██║
    ██╔══╝  ██╔══╝  ██║╚██╗██║██║╚██╗██║██╔══╝  ██║
    ██║     ███████╗██║ ╚████║██║ ╚████║███████╗╚██████╗
    ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚═════╝
"""

# Hacker words that float around
HACKER_WORDS = [
    "EXPLOIT", "BREACH", "PAYLOAD", "INJECT", "SCAN", "PROBE",
    "VULN", "CVE", "SHELL", "ROOT", "ACCESS", "BYPASS",
    "RECON", "ENUM", "PIVOT", "PERSIST", "EXFIL", "C2",
    "BUFFER", "OVERFLOW", "XSS", "SQLI", "RCE", "LFI",
    "NMAP", "BURP", "HYDRA", "METASPLOIT", "GOBUSTER",
    "0DAY", "APT", "MALWARE", "BACKDOOR", "TROJAN",
    "PENTEST", "REDTEAM", "ATTACK", "DEFENSE", "AUDIT",
    "CRYPTO", "HASH", "DECRYPT", "CRACK", "BRUTE",
    "TCP/IP", "HTTP", "DNS", "SSH", "FTP", "SMB",
    "FIREWALL", "IDS", "WAF", "PROXY", "VPN", "TOR",
]

# Matrix rain characters
MATRIX_CHARS = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ012345789Z"


def get_terminal_size() -> Tuple[int, int]:
    """Get terminal width and height."""
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except:
        return 80, 24


def move_cursor(x: int, y: int) -> None:
    """Move cursor to position."""
    sys.stdout.write(f"\033[{y};{x}H")


def clear_screen() -> None:
    """Clear the screen."""
    sys.stdout.write(HACKER.CLEAR_SCREEN + HACKER.HOME)
    sys.stdout.flush()


class FloatingWord:
    """A word that floats across the screen."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.reset()

    def reset(self):
        """Reset to a new random position and word."""
        self.word = random.choice(HACKER_WORDS)
        self.x = random.randint(0, self.width - len(self.word) - 1)
        self.y = random.randint(2, self.height - 3)
        self.dx = random.choice([-1, 1]) * random.uniform(0.3, 0.8)
        self.dy = random.choice([-1, 1]) * random.uniform(0.1, 0.3)
        self.life = random.randint(20, 60)
        self.brightness = random.choice([HACKER.DIM, HACKER.GREEN, HACKER.BRIGHT_GREEN])

    def update(self) -> bool:
        """Update position. Returns False if dead."""
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

        # Bounce off walls
        if self.x < 0 or self.x > self.width - len(self.word):
            self.dx *= -1
            self.x = max(0, min(self.x, self.width - len(self.word)))
        if self.y < 2 or self.y > self.height - 3:
            self.dy *= -1
            self.y = max(2, min(self.y, self.height - 3))

        return self.life > 0

    def render(self) -> str:
        """Return the rendered word with position."""
        return (int(self.x), int(self.y), f"{self.brightness}{self.word}{HACKER.RESET}")


class MatrixColumn:
    """A column of falling matrix characters."""

    def __init__(self, x: int, height: int):
        self.x = x
        self.height = height
        self.y = random.randint(-height, 0)
        self.speed = random.randint(1, 3)
        self.length = random.randint(5, 15)
        self.chars = [random.choice(MATRIX_CHARS) for _ in range(self.length)]

    def update(self):
        """Update the column."""
        self.y += self.speed
        if self.y - self.length > self.height:
            self.y = random.randint(-self.height // 2, 0)
            self.speed = random.randint(1, 3)
            self.chars = [random.choice(MATRIX_CHARS) for _ in range(self.length)]

        # Randomly change some chars
        if random.random() < 0.1:
            idx = random.randint(0, len(self.chars) - 1)
            self.chars[idx] = random.choice(MATRIX_CHARS)


def print_matrix_rain(duration: float = 2.0) -> None:
    """Display matrix rain effect."""
    width, height = get_terminal_size()

    # Create columns
    columns = [MatrixColumn(x, height) for x in range(0, width, 2)]

    sys.stdout.write(HACKER.HIDE_CURSOR + HACKER.BLACK_BG)
    clear_screen()

    start_time = time.time()

    try:
        while time.time() - start_time < duration:
            # Build frame buffer
            frame = [[' ' for _ in range(width)] for _ in range(height)]
            colors = [[HACKER.DARK_GREEN for _ in range(width)] for _ in range(height)]

            for col in columns:
                col.update()

                for i, char in enumerate(col.chars):
                    y = int(col.y) - i
                    if 0 <= y < height:
                        frame[y][col.x] = char
                        if i == 0:
                            colors[y][col.x] = HACKER.WHITE  # Head is white
                        elif i < 3:
                            colors[y][col.x] = HACKER.MATRIX_GREEN  # Near head is bright
                        else:
                            colors[y][col.x] = HACKER.GREEN  # Trail is dimmer

            # Render frame
            sys.stdout.write(HACKER.HOME)
            for y in range(height - 1):
                line = ""
                for x in range(width):
                    if frame[y][x] != ' ':
                        line += f"{colors[y][x]}{frame[y][x]}"
                    else:
                        line += ' '
                sys.stdout.write(line + HACKER.RESET + "\n")

            sys.stdout.flush()
            time.sleep(0.05)

    finally:
        sys.stdout.write(HACKER.RESET)


def print_typing_effect(text: str, delay: float = 0.03, color: str = HACKER.BRIGHT_GREEN) -> None:
    """Print text with typing effect."""
    for char in text:
        sys.stdout.write(f"{color}{char}{HACKER.RESET}")
        sys.stdout.flush()
        time.sleep(delay)


def print_centered(text: str, width: int, color: str = HACKER.BRIGHT_GREEN) -> None:
    """Print text centered."""
    padding = (width - len(text)) // 2
    print(f"{' ' * padding}{color}{text}{HACKER.RESET}")


def print_landing_animation() -> None:
    """Display the full landing page animation."""
    width, height = get_terminal_size()

    sys.stdout.write(HACKER.HIDE_CURSOR)
    sys.stdout.flush()

    try:
        # Phase 1: Brief matrix rain
        print_matrix_rain(duration=1.5)

        # Phase 2: Clear and show logo with floating words
        clear_screen()

        # Create floating words
        words = [FloatingWord(width, height) for _ in range(12)]

        logo_lines = FENNEC_LOGO.strip().split('\n')
        logo_height = len(logo_lines)
        logo_start_y = (height - logo_height) // 2 - 2

        # Animation loop with floating words
        frames = 40
        for frame in range(frames):
            clear_screen()

            # Update and collect floating words
            word_renders = []
            for word in words:
                if not word.update():
                    word.reset()
                word_renders.append(word.render())

            # Render floating words (behind logo)
            for x, y, rendered in word_renders:
                if y < logo_start_y or y > logo_start_y + logo_height + 2:
                    move_cursor(x + 1, y + 1)
                    sys.stdout.write(rendered)

            # Calculate logo fade-in
            progress = min(1.0, frame / 20)

            # Render logo
            for i, line in enumerate(logo_lines):
                y = logo_start_y + i
                x = (width - len(line)) // 2
                move_cursor(x + 1, y + 1)

                if progress >= 1.0:
                    sys.stdout.write(f"{HACKER.MATRIX_GREEN}{line}{HACKER.RESET}")
                else:
                    # Partial reveal with glitch
                    output = ""
                    for j, char in enumerate(line):
                        if char != ' ' and random.random() < progress:
                            output += f"{HACKER.MATRIX_GREEN}{char}"
                        elif char != ' ' and random.random() < 0.3:
                            output += f"{HACKER.DIM}{random.choice('░▒▓█')}"
                        else:
                            output += ' '
                    sys.stdout.write(f"{output}{HACKER.RESET}")

            # Subtitle
            subtitle = "[ AUTONOMOUS RED TEAM PENETRATION TESTING ]"
            move_cursor((width - len(subtitle)) // 2, logo_start_y + logo_height + 2)
            if frame > 25:
                sys.stdout.write(f"{HACKER.BRIGHT_GREEN}{subtitle}{HACKER.RESET}")

            # Blinking cursor effect at bottom
            if frame % 10 < 5:
                move_cursor(2, height - 2)
                sys.stdout.write(f"{HACKER.BRIGHT_GREEN}>{HACKER.RESET} Initializing FENNEC AI...")
            else:
                move_cursor(2, height - 2)
                sys.stdout.write(f"{HACKER.BRIGHT_GREEN}>{HACKER.RESET} Initializing FENNEC AI..._")

            sys.stdout.flush()
            time.sleep(0.08)

        # Phase 3: Final hold with status messages
        status_messages = [
            "Loading exploit modules...",
            "Connecting to C2 framework...",
            "Initializing reconnaissance tools...",
            "Calibrating attack vectors...",
            "Ready.",
        ]

        for i, msg in enumerate(status_messages):
            move_cursor(2, height - 2)
            sys.stdout.write(HACKER.CLEAR_LINE)
            sys.stdout.write(f"{HACKER.BRIGHT_GREEN}>{HACKER.RESET} {msg}")
            sys.stdout.flush()

            if i < len(status_messages) - 1:
                time.sleep(0.4)
            else:
                time.sleep(0.6)

        # Brief pause before transition
        time.sleep(0.3)

        # Clear for next screen
        clear_screen()

    finally:
        sys.stdout.write(HACKER.SHOW_CURSOR + HACKER.RESET)
        sys.stdout.flush()


def print_simple_landing() -> None:
    """Simple landing without heavy animation (for non-TTY)."""
    print(f"{HACKER.BRIGHT_GREEN}")
    print("=" * 60)
    print()
    print(FENNEC_LOGO)
    print()
    print("  [ AUTONOMOUS RED TEAM PENETRATION TESTING ]")
    print()
    print("=" * 60)
    print(f"{HACKER.RESET}")


def show_landing(skip_animation: bool = False) -> None:
    """
    Show the landing page.

    Args:
        skip_animation: If True, show simple version without animation
    """
    # Check if we're in a real terminal
    if not sys.stdout.isatty() or skip_animation:
        print_simple_landing()
        return

    try:
        print_landing_animation()
    except KeyboardInterrupt:
        # User interrupted, clean up
        sys.stdout.write(HACKER.SHOW_CURSOR + HACKER.RESET)
        clear_screen()
    except Exception:
        # Fallback to simple version on any error
        sys.stdout.write(HACKER.SHOW_CURSOR + HACKER.RESET)
        print_simple_landing()


if __name__ == "__main__":
    show_landing()
