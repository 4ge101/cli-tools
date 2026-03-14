#!/usr/bin/env python3
"""
╔══════════════════════════════════════╗
║         M A T R I X  R A I N        ║
║     Terminal Matrix Animation 🟢     ║
╚══════════════════════════════════════╝

Install:
    pip install rich

Run:
    python matrix.py
"""

import random
import time
from rich.console import Console
from rich.text import Text
from rich.live import Live

console = Console()

# ── Config ─────────────────────────────────────────────────────────────────────
WIDTH       = 100
HEIGHT      = 38
FPS         = 20
DENSITY     = 0.04   # chance of new stream per column per frame

# ── Character sets ─────────────────────────────────────────────────────────────
KATAKANA = [chr(c) for c in range(0x30A0, 0x30FF)]
LATIN    = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
SYMBOLS  = list("@#$%&*<>[]{}|/\\=+-~^?!")
CHARS    = KATAKANA + LATIN + SYMBOLS

def rchar():
    return random.choice(CHARS)

# ── Stream ─────────────────────────────────────────────────────────────────────

class Stream:
    def __init__(self, col):
        self.col    = col
        self.head   = random.randint(-HEIGHT, 0)
        self.length = random.randint(6, HEIGHT // 2)
        self.speed  = random.choice([1, 1, 1, 2])
        self.chars  = [rchar() for _ in range(HEIGHT)]
        self.mutate_cd = 0

    def update(self):
        self.head += self.speed
        # randomly mutate a char in the trail
        self.mutate_cd -= 1
        if self.mutate_cd <= 0:
            idx = random.randint(0, HEIGHT - 1)
            self.chars[idx] = rchar()
            self.mutate_cd = random.randint(1, 4)

    @property
    def done(self):
        return self.head - self.length > HEIGHT

    def draw(self, grid):
        for i in range(self.length):
            y = self.head - i
            if 0 <= y < HEIGHT:
                ch = self.chars[y % len(self.chars)]
                if i == 0:
                    # bright white head
                    grid[y][self.col] = (ch, "bold bright_white")
                elif i == 1:
                    grid[y][self.col] = (ch, "bold bright_green")
                elif i < 4:
                    grid[y][self.col] = (ch, "green")
                elif i < self.length // 2:
                    grid[y][self.col] = (ch, "dark_green")
                else:
                    grid[y][self.col] = (ch, "grey23")

# ── Grid ──────────────────────────────────────────────────────────────────────

def empty_grid():
    return [[(" ", "") for _ in range(WIDTH)] for _ in range(HEIGHT)]

def render(grid):
    lines = []
    for row in grid:
        line = Text()
        for char, style in row:
            if style:
                line.append(char, style=style)
            else:
                line.append(char)
        lines.append(line)
    return Text("\n").join(lines)

# ── Glitch overlay ─────────────────────────────────────────────────────────────

def glitch(grid):
    if random.random() < 0.06:
        row = random.randint(0, HEIGHT - 1)
        for col in range(WIDTH):
            if random.random() < 0.3:
                grid[row][col] = (rchar(), random.choice(["bright_green", "green", "dark_green"]))

# ── Message ───────────────────────────────────────────────────────────────────

MESSAGES = [
    "FOLLOW THE WHITE RABBIT",
    "WAKE UP, NEO...",
    "THE MATRIX HAS YOU",
    "KNOCK KNOCK, NEO.",
    "THERE IS NO SPOON",
]

class Message:
    def __init__(self):
        self.text  = random.choice(MESSAGES)
        self.x     = (WIDTH - len(self.text)) // 2
        self.y     = random.randint(HEIGHT // 4, HEIGHT * 3 // 4)
        self.life  = 60
        self.max   = 60

    def draw(self, grid):
        self.life -= 1
        ratio = self.life / self.max
        for i, ch in enumerate(self.text):
            xi = self.x + i
            if 0 <= xi < WIDTH:
                if ratio > 0.7:
                    style = "bold bright_white"
                elif ratio > 0.4:
                    style = "bold bright_green"
                else:
                    style = "green"
                grid[self.y][xi] = (ch, style)

    @property
    def done(self):
        return self.life <= 0

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    streams  = []
    messages = []
    frame    = 0
    msg_cd   = random.randint(40, 80)

    try:
        with Live(console=console, refresh_per_second=FPS, screen=True) as live:
            while True:
                frame  += 1
                msg_cd -= 1

                # spawn new streams
                for col in range(WIDTH):
                    if random.random() < DENSITY:
                        # avoid stacking too many on same col
                        active_cols = {s.col for s in streams}
                        if col not in active_cols:
                            streams.append(Stream(col))

                # update & cull
                for s in streams:
                    s.update()
                streams = [s for s in streams if not s.done]

                # spawn message
                if msg_cd <= 0:
                    messages.append(Message())
                    msg_cd = random.randint(80, 160)

                messages = [m for m in messages if not m.done]

                # draw
                grid = empty_grid()
                for s in streams:
                    s.draw(grid)
                glitch(grid)
                for m in messages:
                    m.draw(grid)

                live.update(render(grid))
                time.sleep(1 / FPS)

    except KeyboardInterrupt:
        console.clear()
        console.print("\n  [bright_green]// SYSTEM DISCONNECTED //[/]\n")

if __name__ == "__main__":
    main()