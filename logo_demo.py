import time
import random
import sys
from rich.console import Console
from rich.live import Live
from rich.text import Text

console = Console()

logo_lines = [
    "███╗   ██╗██╗  ██╗ ██████╗██╗      ██╗",
    "████╗  ██║╚██╗██╔╝██╔════╝██║      ██║",
    "██╔██╗ ██║ ╚███╔╝ ██║     ██║      ██║",
    "██║╚██╗██║ ██╔██╗ ██║     ██║      ██║",
    "██║ ╚████║██╔╝ ██╗╚██████╗███████╗ ██║",
    "╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝╚══════╝ ╚═╝"
]

def get_gradient_char(char, position, length, offset=0, palette="blaze"):
    if char == ' ': return char
    ratio = ((position / max(1, length - 1)) + offset) % 1.0
    if palette == "blaze":
        start_rgb = (255, 0, 0)
        end_rgb = (255, 165, 0)
    elif palette == "shimmer":
        pulse_width = 0.2
        dist_to_center = abs(ratio - 0.5)
        if dist_to_center < pulse_width:
            glow = (1 - (dist_to_center / pulse_width))
            return f"\033[38;2;255;{int(200*glow)};{int(100*glow)}m{char}"
        else:
            return f"\033[38;2;100;0;0m{char}"
    r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
    g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
    b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
    return f"\033[38;2;{r};{g};{b}m{char}"

def demo_assembly():
    console.print("\n[bold white]Option 1: The Assembly (Intro Animation)[/bold white]")
    frames = 15
    for f in range(frames):
        out = ""
        for line in logo_lines:
            row = ""
            for i, char in enumerate(line):
                if char == ' ': row += ' '
                elif random.random() > (f / frames): row += random.choice(["░", "▒", "▓"])
                else: row += get_gradient_char(char, i, len(line))
            out += row + "\n"
        sys.stdout.write(out)
        if f < frames - 1:
            sys.stdout.write(f"\033[{len(logo_lines)}A")
        time.sleep(0.08)
    time.sleep(1)

def demo_flow():
    console.print("\n[bold white]Option 2: The Flowing Gradient (Live Engine)[/bold white]")
    offset = 0
    start_time = time.time()
    with Live(console=console, refresh_per_second=20) as live:
        while time.time() - start_time < 5:
            offset += 0.05
            full_logo = ""
            for line in logo_lines:
                row = ""
                for i, char in enumerate(line):
                    row += get_gradient_char(char, i, len(line), offset=offset)
                full_logo += row + "\033[0m\n"
            live.update(Text.from_ansi(full_logo))
            time.sleep(0.05)

def demo_shimmer():
    console.print("\n[bold white]Option 3: The Shimmer Pulse[/bold white]")
    offset = 0
    start_time = time.time()
    with Live(console=console, refresh_per_second=20) as live:
        while time.time() - start_time < 5:
            offset += 0.08
            full_logo = ""
            for line in logo_lines:
                row = ""
                for i, char in enumerate(line):
                    row += get_gradient_char(char, i, len(line), offset=offset, palette="shimmer")
                full_logo += row + "\033[0m\n"
            live.update(Text.from_ansi(full_logo))
            time.sleep(0.05)

if __name__ == "__main__":
    try:
        demo_assembly()
        demo_flow()
        demo_shimmer()
        console.print("\n[bold green]Demo Complete![/bold green]")
    except KeyboardInterrupt:
        pass
