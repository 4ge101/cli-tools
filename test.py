#!/usr/bin/env python3
"""
╔══════════════════════════════════════╗
║           S Y S A U R A             ║
║     Neon Cyberpunk System Monitor   ║
╚══════════════════════════════════════╝

Install dependencies:
    pip install psutil rich

Run:
    python sysaura.py
"""

import time
import platform
import socket
import psutil
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.columns import Columns
from rich import box
from rich.align import Align
from rich.rule import Rule

console = Console()

# ── Neon Cyberpunk Colors ──────────────────────────────────────────────────────
NEON_CYAN    = "bright_cyan"
NEON_PINK    = "bright_magenta"
NEON_GREEN   = "bright_green"
NEON_YELLOW  = "bright_yellow"
NEON_RED     = "bright_red"
NEON_BLUE    = "bright_blue"
DIM          = "grey50"
BG_DARK      = "grey11"

# ── ASCII Art Banner ───────────────────────────────────────────────────────────
BANNER = r"""
 ███████╗██╗   ██╗███████╗ █████╗ ██╗   ██╗██████╗  █████╗
 ██╔════╝╚██╗ ██╔╝██╔════╝██╔══██╗██║   ██║██╔══██╗██╔══██╗
 ███████╗ ╚████╔╝ ███████╗███████║██║   ██║██████╔╝███████║
 ╚════██║  ╚██╔╝  ╚════██║██╔══██║██║   ██║██╔══██╗██╔══██║
 ███████║   ██║   ███████║██║  ██║╚██████╔╝██║  ██║██║  ██║
 ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
"""

# ── Helpers ────────────────────────────────────────────────────────────────────

def neon_bar(value: float, width: int = 20) -> Text:
    """Returns a colored block-bar based on percentage value."""
    filled = int(value / 100 * width)
    empty  = width - filled

    if value >= 85:
        color = NEON_RED
    elif value >= 60:
        color = NEON_YELLOW
    else:
        color = NEON_CYAN

    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * empty,  style=DIM)
    bar.append(f" {value:5.1f}%", style=color + " bold")
    return bar


def bytes_to_human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def uptime() -> str:
    boot   = psutil.boot_time()
    now    = time.time()
    delta  = int(now - boot)
    h, rem = divmod(delta, 3600)
    m, s   = divmod(rem, 60)
    return f"{h}h {m}m {s}s"


# ── Sections ───────────────────────────────────────────────────────────────────

def make_header() -> Panel:
    banner_text = Text(BANNER, style=f"bold {NEON_CYAN}", justify="center")
    host   = socket.gethostname()
    osname = f"{platform.system()} {platform.release()}"
    now    = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    sub = Text(justify="center")
    sub.append(f"  {host}  ", style=f"bold {NEON_PINK}")
    sub.append("│", style=DIM)
    sub.append(f"  {osname}  ", style=f"{NEON_BLUE}")
    sub.append("│", style=DIM)
    sub.append(f"  {now}  ", style=f"{NEON_GREEN}")

    content = Text(justify="center")
    content.append_text(banner_text)
    content.append("\n")
    content.append_text(sub)

    return Panel(
        Align.center(content),
        border_style=NEON_CYAN,
        box=box.DOUBLE_EDGE,
    )


def make_cpu() -> Panel:
    per_cpu  = psutil.cpu_percent(percpu=True)
    avg      = sum(per_cpu) / len(per_cpu)
    freq     = psutil.cpu_freq()
    cores    = psutil.cpu_count(logical=False)
    threads  = psutil.cpu_count(logical=True)

    table = Table(box=None, show_header=False, padding=(0, 1))
    table.add_column("Label", style=DIM, width=14)
    table.add_column("Bar")

    table.add_row("  OVERALL", neon_bar(avg))
    table.add_row("", Text(""))

    for i, pct in enumerate(per_cpu):
        table.add_row(f"  Core {i:<3}", neon_bar(pct, width=15))

    table.add_row("", Text(""))
    info = Text()
    info.append(f"  Cores: ", style=DIM)
    info.append(f"{cores}P / {threads}T   ", style=NEON_PINK + " bold")
    if freq:
        info.append(f"Freq: ", style=DIM)
        info.append(f"{freq.current:.0f} MHz", style=NEON_CYAN + " bold")
    table.add_row("", info)

    return Panel(table, title=f"[bold {NEON_CYAN}]◈  C P U[/]",
                 border_style=NEON_CYAN, box=box.ROUNDED)


def make_memory() -> Panel:
    vm   = psutil.virtual_memory()
    swap = psutil.swap_memory()

    table = Table(box=None, show_header=False, padding=(0, 1))
    table.add_column("Label", style=DIM, width=14)
    table.add_column("Bar")

    table.add_row("  RAM", neon_bar(vm.percent))
    used_str  = bytes_to_human(vm.used)
    total_str = bytes_to_human(vm.total)
    info_ram  = Text(f"  {used_str} / {total_str}", style=DIM)
    table.add_row("", info_ram)

    table.add_row("", Text(""))
    table.add_row("  SWAP", neon_bar(swap.percent))
    s_used  = bytes_to_human(swap.used)
    s_total = bytes_to_human(swap.total)
    info_sw = Text(f"  {s_used} / {s_total}", style=DIM)
    table.add_row("", info_sw)

    return Panel(table, title=f"[bold {NEON_PINK}]◈  M E M O R Y[/]",
                 border_style=NEON_PINK, box=box.ROUNDED)


def make_disk() -> Panel:
    partitions = psutil.disk_partitions()
    table = Table(box=None, show_header=False, padding=(0, 1))
    table.add_column("Mount", style=DIM, width=14)
    table.add_column("Bar")

    for p in partitions[:4]:
        try:
            usage = psutil.disk_usage(p.mountpoint)
            label = p.mountpoint[:12]
            table.add_row(f"  {label}", neon_bar(usage.percent, width=16))
            info = Text(f"  {bytes_to_human(usage.used)} / {bytes_to_human(usage.total)}", style=DIM)
            table.add_row("", info)
        except PermissionError:
            pass

    return Panel(table, title=f"[bold {NEON_YELLOW}]◈  D I S K[/]",
                 border_style=NEON_YELLOW, box=box.ROUNDED)


def make_network() -> Panel:
    net = psutil.net_io_counters()
    table = Table(box=None, show_header=False, padding=(0, 1))
    table.add_column("Label", style=DIM, width=14)
    table.add_column("Value", style=NEON_GREEN + " bold")

    table.add_row("  ▲ Sent",     bytes_to_human(net.bytes_sent))
    table.add_row("  ▼ Received", bytes_to_human(net.bytes_recv))
    table.add_row("  Packets ▲",  str(net.packets_sent))
    table.add_row("  Packets ▼",  str(net.packets_recv))

    # active connections
    try:
        conns = len(psutil.net_connections())
        table.add_row("  Connections", str(conns))
    except Exception:
        pass

    return Panel(table, title=f"[bold {NEON_GREEN}]◈  N E T W O R K[/]",
                 border_style=NEON_GREEN, box=box.ROUNDED)


def make_system_info() -> Panel:
    table = Table(box=None, show_header=False, padding=(0, 1))
    table.add_column("Label", style=DIM, width=14)
    table.add_column("Value", style=NEON_BLUE + " bold")

    table.add_row("  Hostname",   socket.gethostname())
    table.add_row("  OS",         f"{platform.system()} {platform.release()}")
    table.add_row("  Arch",       platform.machine())
    table.add_row("  Python",     platform.python_version())
    table.add_row("  Uptime",     uptime())
    table.add_row("  PID count",  str(len(psutil.pids())))

    return Panel(table, title=f"[bold {NEON_BLUE}]◈  S Y S T E M[/]",
                 border_style=NEON_BLUE, box=box.ROUNDED)


def make_top_processes() -> Panel:
    procs = sorted(
        psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]),
        key=lambda p: p.info.get("cpu_percent") or 0,
        reverse=True,
    )[:6]

    table = Table(box=box.SIMPLE, show_header=True, header_style=f"bold {NEON_PINK}")
    table.add_column("PID",    style=DIM,       width=7)
    table.add_column("Name",   style=NEON_CYAN,  width=18)
    table.add_column("CPU%",   style=NEON_YELLOW, width=8)
    table.add_column("MEM%",   style=NEON_GREEN,  width=8)

    for p in procs:
        try:
            table.add_row(
                str(p.info["pid"]),
                (p.info["name"] or "?")[:17],
                f"{p.info['cpu_percent']:.1f}",
                f"{p.info['memory_percent']:.1f}",
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return Panel(table, title=f"[bold {NEON_RED}]◈  T O P  P R O C E S S E S[/]",
                 border_style=NEON_RED, box=box.ROUNDED)


def make_footer() -> Text:
    t = Text(justify="center")
    t.append("  [Q] QUIT  ", style=f"bold {NEON_RED}")
    t.append("│", style=DIM)
    t.append("  Refreshing every 1s  ", style=DIM)
    t.append("│", style=DIM)
    t.append("  SYSAURA v1.0  ", style=f"bold {NEON_CYAN}")
    return t


# ── Main render ────────────────────────────────────────────────────────────────

def render() -> Layout:
    layout = Layout()

    layout.split_column(
        Layout(name="header",   size=11),
        Layout(name="body"),
        Layout(name="footer",   size=3),
    )

    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )

    layout["left"].split_column(
        Layout(name="cpu"),
        Layout(name="memory"),
    )

    layout["right"].split_column(
        Layout(name="top_row"),
        Layout(name="bottom_row"),
    )

    layout["top_row"].split_row(
        Layout(name="disk"),
        Layout(name="network"),
    )

    layout["bottom_row"].split_row(
        Layout(name="sysinfo"),
        Layout(name="processes"),
    )

    layout["header"].update(make_header())
    layout["cpu"].update(make_cpu())
    layout["memory"].update(make_memory())
    layout["disk"].update(make_disk())
    layout["network"].update(make_network())
    layout["sysinfo"].update(make_system_info())
    layout["processes"].update(make_top_processes())
    layout["footer"].update(
        Panel(make_footer(), border_style=NEON_CYAN, box=box.HORIZONTALS)
    )

    return layout


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    console.clear()
    try:
        with Live(render(), refresh_per_second=1, screen=True) as live:
            while True:
                time.sleep(1)
                live.update(render())
    except KeyboardInterrupt:
        console.clear()
        console.print(
            Panel(
                Text("[ SYSAURA SHUTDOWN ]", style=f"bold {NEON_CYAN}", justify="center"),
                border_style=NEON_CYAN,
                box=box.DOUBLE_EDGE,
            )
        )


if __name__ == "__main__":
    main()