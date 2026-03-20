import curses
import random
import time

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    # colors
    curses.init_pair(1, curses.COLOR_CYAN,    -1)  # bright drops
    curses.init_pair(2, curses.COLOR_BLUE,    -1)  # mid drops
    curses.init_pair(3, curses.COLOR_WHITE,   -1)  # splash / lightning
    curses.init_pair(4, curses.COLOR_YELLOW,  -1)  # city lights
    curses.init_pair(5, curses.COLOR_BLACK,   -1)  # dark sky (unused visually)
    curses.init_pair(6, curses.COLOR_GREEN,   -1)  # ground / mist

    stdscr.nodelay(True)
    stdscr.timeout(50)

    HEIGHT, WIDTH = stdscr.getmaxyx()

    GROUND = HEIGHT - 4
    CITY_ROW = GROUND - 1

    RAIN_CHARS   = ['|', '|', '|', "'", '`']
    SPLASH_CHARS = ['*', '+', 'x', '.']
    HEAVY_CHARS  = ['|', '|', '/', '|', '|', '/']

    # --- rain drops ---
    class Drop:
        def __init__(self):
            self.reset()

        def reset(self):
            self.x   = random.randint(0, WIDTH - 2)
            self.y   = random.uniform(-10, 0)
            self.spd = random.uniform(1.2, 2.8)
            self.ch  = random.choice(HEAVY_CHARS)
            self.col = random.choice([1, 1, 2, 2, 1])
            self.trail = random.randint(2, 5)

    drops = [Drop() for _ in range(int(WIDTH * 1.4))]

    # --- splashes ---
    splashes = []

    # --- city skyline: (x, width, height) ---
    buildings = []
    bx = 0
    while bx < WIDTH:
        bw = random.randint(4, 10)
        bh = random.randint(3, min(12, GROUND - 2))
        buildings.append((bx, bw, bh))
        bx += bw + random.randint(0, 1)

    # pre-generate window lights per building
    win_lights = []
    for (bx, bw, bh) in buildings:
        lights = {}
        for row in range(1, bh):
            for col in range(1, bw - 1, 2):
                lights[(row, col)] = random.random() > 0.4
        win_lights.append(lights)

    # flicker timer
    flicker_timer = 0
    FLICKER_INTERVAL = 8

    # lightning
    lightning      = 0
    lightning_timer = random.randint(40, 120)

    # scroll offset for wind effect
    wind_offset = 0.0
    wind_timer  = 0

    frame = 0

    while True:
        key = stdscr.getch()
        if key == ord('q') or key == ord('Q'):
            break

        HEIGHT, WIDTH = stdscr.getmaxyx()
        GROUND   = HEIGHT - 4
        CITY_ROW = GROUND - 1

        stdscr.erase()

        # --- lightning flash ---
        lightning_timer -= 1
        if lightning_timer <= 0:
            lightning       = random.randint(3, 6)
            lightning_timer = random.randint(60, 180)

        flash = lightning > 0
        if flash:
            lightning -= 1

        # --- draw sky ---
        sky_char = ' '
        if flash:
            for row in range(0, CITY_ROW):
                try:
                    stdscr.addstr(row, 0, sky_char * (WIDTH - 1),
                                  curses.color_pair(3) | curses.A_BOLD)
                except curses.error:
                    pass

        # --- draw buildings ---
        for i, (bx, bw, bh) in enumerate(buildings):
            if bx >= WIDTH:
                continue
            top_row = GROUND - bh
            for row in range(top_row, GROUND):
                local_row = row - top_row
                for col in range(bw):
                    cx = bx + col
                    if cx >= WIDTH - 1:
                        continue
                    # building body
                    ch = '#'
                    attr = curses.A_NORMAL
                    # window
                    if 0 < local_row < bh - 1 and 0 < col < bw - 1:
                        lit = win_lights[i].get((local_row, col - ((col) % 2)), False)
                        if lit:
                            ch   = 'o'
                            attr = curses.color_pair(4) | curses.A_BOLD
                        else:
                            ch   = '.'
                            attr = curses.color_pair(2)
                    else:
                        attr = curses.color_pair(2)
                    try:
                        stdscr.addch(row, cx, ch, attr)
                    except curses.error:
                        pass

        # --- ground line ---
        ground_str = '~' * (WIDTH - 1)
        try:
            stdscr.addstr(GROUND, 0, ground_str, curses.color_pair(6) | curses.A_BOLD)
        except curses.error:
            pass

        # --- puddles ---
        for px in range(2, WIDTH - 3, 9):
            puddle = '___'
            try:
                stdscr.addstr(GROUND + 1, px, puddle, curses.color_pair(2))
            except curses.error:
                pass

        # --- update & draw rain ---
        wind_offset += 0.05
        for d in drops:
            d.y += d.spd
            # wind drift
            wx = int(d.x + wind_offset * 0.3) % (WIDTH - 1)

            # draw trail
            for t in range(d.trail):
                ty = int(d.y) - t
                if 0 <= ty < GROUND and 0 <= wx < WIDTH - 1:
                    alpha = d.trail - t
                    if alpha > 2:
                        attr = curses.color_pair(1) | curses.A_BOLD
                    else:
                        attr = curses.color_pair(2)
                    try:
                        stdscr.addch(ty, wx, d.ch, attr)
                    except curses.error:
                        pass

            # hit ground → splash
            if d.y >= GROUND:
                if random.random() < 0.6:
                    splashes.append({
                        'x': wx, 'y': GROUND,
                        'ch': random.choice(SPLASH_CHARS),
                        'ttl': random.randint(1, 3)
                    })
                d.reset()
                d.x = random.randint(0, WIDTH - 2)

        # --- draw splashes ---
        new_splashes = []
        for s in splashes:
            if 0 <= s['x'] < WIDTH - 1:
                try:
                    stdscr.addch(s['y'], s['x'], s['ch'],
                                 curses.color_pair(3) | curses.A_BOLD)
                except curses.error:
                    pass
            s['ttl'] -= 1
            if s['ttl'] > 0:
                new_splashes.append(s)
        splashes = new_splashes

        # --- flicker windows ---
        flicker_timer += 1
        if flicker_timer >= FLICKER_INTERVAL:
            flicker_timer = 0
            for lights in win_lights:
                for key in lights:
                    if random.random() < 0.04:
                        lights[key] = not lights[key]

        # --- status bar ---
        status = " Biratnagar Heavy Rain  |  press Q to quit  |  frame: {}".format(frame)
        try:
            stdscr.addstr(HEIGHT - 1, 0,
                          status[:WIDTH - 1],
                          curses.color_pair(2))
        except curses.error:
            pass

        # --- lightning bolt ---
        if flash and random.random() < 0.4:
            bx = random.randint(5, WIDTH - 6)
            for by in range(0, CITY_ROW, 2):
                bx += random.randint(-1, 1)
                bx  = max(1, min(WIDTH - 2, bx))
                try:
                    stdscr.addch(by, bx, '|',
                                 curses.color_pair(3) | curses.A_BOLD)
                except curses.error:
                    pass

        stdscr.refresh()
        frame += 1
        time.sleep(0.04)


if __name__ == '__main__':
    curses.wrapper(main)
