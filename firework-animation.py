

import random
import time
import math
from rich.console import Console
from rich.text import Text
from rich.live import Live

console = Console()

# ── Config ─────────────────────────────────────────────────────────────────────
WIDTH        = 100
HEIGHT       = 38
FPS          = 24
MAX_ROCKETS  = 6
TRAIL_LEN    = 6

# ── Color palettes ─────────────────────────────────────────────────────────────
PALETTES = [
    ["bright_red", "red", "dark_red"],
    ["bright_yellow", "yellow", "orange3"],
    ["bright_cyan", "cyan", "dark_cyan"],
    ["bright_magenta", "magenta", "purple"],
    ["bright_green", "green", "dark_green"],
    ["bright_white", "white", "grey70"],
    ["bright_blue", "blue", "dark_blue"],
]

SPARKS   = ["★", "✦", "✧", "·", "°", "*", "٭", "⋆", "✸", "✺", "❋", "✼"]
ROCKETS  = ["│", "┃", "╽"]
EXPLODE  = ["✦", "★", "✸", "✺", "❋", "✼", "·", "°", "*"]

# ── Grid ──────────────────────────────────────────────────────────────────────

def empty_grid():
    return [[(" ", "grey15") for _ in range(WIDTH)] for _ in range(HEIGHT)]

def set_pixel(grid, x, y, char, style):
    xi, yi = int(round(x)), int(round(y))
    if 0 <= xi < WIDTH and 0 <= yi < HEIGHT:
        grid[yi][xi] = (char, style)

# ── Particles ─────────────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, vx, vy, palette, life, char=None):
        self.x       = x
        self.y       = y
        self.vx      = vx
        self.vy      = vy
        self.palette = palette
        self.life    = life
        self.max_life= life
        self.char    = char or random.choice(EXPLODE)

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.07   # gravity
        self.vx   *= 0.97   # drag
        self.life -= 1

    @property
    def alive(self):
        return self.life > 0

    def draw(self, grid):
        ratio = self.life / self.max_life
        if ratio > 0.6:
            color = self.palette[0]
        elif ratio > 0.3:
            color = self.palette[1]
        else:
            color = self.palette[2]
        set_pixel(grid, self.x, self.y, self.char, color)


class Rocket:
    def __init__(self):
        self.x        = random.randint(10, WIDTH - 10)
        self.y        = HEIGHT - 1
        self.vy       = random.uniform(-1.6, -1.2)
        self.target_y = random.randint(4, HEIGHT // 2 - 2)
        self.palette  = random.choice(PALETTES)
        self.trail    = []
        self.exploded = False
        self.particles= []
        self.char     = random.choice(ROCKETS)

    def update(self):
        if not self.exploded:
            self.trail.append((self.x, self.y))
            if len(self.trail) > TRAIL_LEN:
                self.trail.pop(0)
            self.y += self.vy
            if self.y <= self.target_y:
                self.explode()
        else:
            for p in self.particles:
                p.update()
            self.particles = [p for p in self.particles if p.alive]

    def explode(self):
        self.exploded = True
        count = random.randint(60, 120)
        shape = random.choice(["circle", "star", "ring", "burst"])

        for i in range(count):
            angle  = (2 * math.pi * i) / count
            if shape == "circle":
                speed  = random.uniform(0.4, 1.2)
                vx     = math.cos(angle) * speed
                vy     = math.sin(angle) * speed * 0.55
            elif shape == "star":
                # 5-pointed star: boost every 72 degrees
                speed  = 1.2 if i % (count // 5) < 3 else 0.4
                speed += random.uniform(-0.1, 0.2)
                vx     = math.cos(angle) * speed
                vy     = math.sin(angle) * speed * 0.55
            elif shape == "ring":
                speed  = random.uniform(0.9, 1.1)
                vx     = math.cos(angle) * speed
                vy     = math.sin(angle) * speed * 0.55
            else:  # burst
                speed  = random.uniform(0.1, 1.4)
                vx     = math.cos(angle) * speed
                vy     = math.sin(angle) * speed * 0.5

            life = random.randint(14, 28)
            self.particles.append(
                Particle(self.x, self.y, vx, vy, self.palette, life)
            )

        # add some glitter
        for _ in range(20):
            vx   = random.uniform(-0.6, 0.6)
            vy   = random.uniform(-0.6, 0.1)
            life = random.randint(8, 18)
            self.particles.append(
                Particle(self.x, self.y, vx, vy, self.palette, life, char="·")
            )

    def draw(self, grid):
        if not self.exploded:
            for i, (tx, ty) in enumerate(self.trail):
                alpha = i / len(self.trail)
                color = self.palette[0] if alpha > 0.6 else (self.palette[1] if alpha > 0.3 else self.palette[2])
                set_pixel(grid, tx, ty, "╎" if alpha < 0.4 else self.char, color)
            set_pixel(grid, self.x, self.y, "▲", self.palette[0])
        else:
            for p in self.particles:
                p.draw(grid)

    @property
    def done(self):
        return self.exploded and len(self.particles) == 0


# ── Ground / skyline ──────────────────────────────────────────────────────────

def draw_skyline(grid):
    buildings = [
        (2,  8, 6),  (9,  12, 5), (15, 6,  4), (20, 10, 6),
        (27, 14, 5), (33, 8,  3), (37, 11, 7), (45, 7,  5),
        (51, 13, 6), (58, 9,  4), (63, 15, 5), (69, 8,  6),
        (76, 12, 4), (81, 6,  5), (87, 10, 7), (93, 13, 4),
    ]
    for bx, bh, bw in buildings:
        top = HEIGHT - 1 - bh
        for row in range(top, HEIGHT):
            for col in range(bx, min(bx + bw, WIDTH)):
                if row == top:
                    set_pixel(grid, col, row, "▄", "grey23")
                else:
                    # windows
                    if (col - bx) % 2 == 1 and (row - top) % 2 == 1 and random.random() < 0.4:
                        set_pixel(grid, col, row, "░", "yellow4")
                    else:
                        set_pixel(grid, col, row, "█", "grey19")
    # ground
    for col in range(WIDTH):
        set_pixel(grid, col, HEIGHT - 1, "▀", "grey23")


# ── Stars ─────────────────────────────────────────────────────────────────────

STAR_POSITIONS = [(random.randint(0, WIDTH-1), random.randint(0, HEIGHT//2)) for _ in range(60)]

def draw_stars(grid):
    for sx, sy in STAR_POSITIONS:
        if grid[sy][sx][0] == " ":
            char  = "·" if random.random() > 0.05 else "✦"
            color = random.choice(["grey30", "grey35", "grey42"])
            set_pixel(grid, sx, sy, char, color)


# ── Render ─────────────────────────────────────────────────────────────────────

def render(grid):
    lines = []
    for row in grid:
        line = Text()
        for char, style in row:
            line.append(char, style=style)
        lines.append(line)
    return Text("\n").join(lines)


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    rockets   = []
    frame     = 0
    launch_cd = 0

    try:
        with Live(console=console, refresh_per_second=FPS, screen=True) as live:
            while True:
                frame    += 1
                launch_cd-= 1

                # launch new rockets
                if launch_cd <= 0 and len(rockets) < MAX_ROCKETS:
                    rockets.append(Rocket())
                    # sometimes double-launch
                    if random.random() < 0.3 and len(rockets) < MAX_ROCKETS:
                        rockets.append(Rocket())
                    launch_cd = random.randint(6, 18)

                # update
                for r in rockets:
                    r.update()
                rockets = [r for r in rockets if not r.done]

                # draw
                grid = empty_grid()
                draw_stars(grid)
                draw_skyline(grid)
                for r in rockets:
                    r.draw(grid)

                # title
                title_chars = "✦ FIREWORKS ✦"
                tx = (WIDTH - len(title_chars)) // 2
                for i, ch in enumerate(title_chars):
                    color = random.choice(["bright_yellow", "bright_cyan", "bright_magenta", "bright_white"])
                    set_pixel(grid, tx + i, 1, ch, color)

                live.update(render(grid))
                time.sleep(1 / FPS)

    except KeyboardInterrupt:
        console.clear()
        console.print("\n  [bright_yellow]✦ Thanks for watching! ✦[/]\n")


if __name__ == "__main__":
    main()