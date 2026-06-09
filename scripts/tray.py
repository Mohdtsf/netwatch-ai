#!/usr/bin/env python3
"""
NetWatch AI — System Tray Icon
Desktop tray app for Start/Stop/Open Dashboard.

Requirements:
    pip install pystray Pillow

Usage:
    python scripts/tray.py
"""

import subprocess
import sys
import os
import webbrowser
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Install dependencies: pip install pystray Pillow")
    sys.exit(1)


# ── Configuration ─────────────────────────────

PROJECT_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_URL = "http://localhost:3000"
API_DOCS_URL = "http://localhost:8000/docs"
COMPOSE_CMD = ["docker", "compose"]


def _run_compose(*args):
    """Run a docker compose command in the project directory."""
    return subprocess.run(
        [*COMPOSE_CMD, *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


# ── Actions ───────────────────────────────────


def is_running() -> bool:
    """Check if NetWatch services are running."""
    result = _run_compose("ps", "--format", "json", "-q")
    return bool(result.stdout.strip())


def start_services(icon, item):
    """Start all NetWatch services."""
    icon.notify("Starting NetWatch AI...", "NetWatch")
    result = _run_compose("up", "-d")
    if result.returncode == 0:
        icon.notify("NetWatch AI is running!", "NetWatch")
        _update_icon(icon, running=True)
    else:
        icon.notify(f"Start failed: {result.stderr[:100]}", "NetWatch")


def stop_services(icon, item):
    """Stop all NetWatch services."""
    icon.notify("Stopping NetWatch AI...", "NetWatch")
    result = _run_compose("down")
    if result.returncode == 0:
        icon.notify("NetWatch AI stopped.", "NetWatch")
        _update_icon(icon, running=False)
    else:
        icon.notify(f"Stop failed: {result.stderr[:100]}", "NetWatch")


def restart_services(icon, item):
    """Restart all services."""
    icon.notify("Restarting NetWatch AI...", "NetWatch")
    _run_compose("restart")
    icon.notify("NetWatch AI restarted!", "NetWatch")


def open_dashboard(icon, item):
    """Open the web dashboard in the default browser."""
    webbrowser.open(DASHBOARD_URL)


def open_api_docs(icon, item):
    """Open API documentation."""
    webbrowser.open(API_DOCS_URL)


def view_logs(icon, item):
    """Open logs in a terminal."""
    subprocess.Popen(
        ["x-terminal-emulator", "-e", "docker", "compose", "logs", "-f", "--tail=100"],
        cwd=PROJECT_DIR,
    )


def quit_app(icon, item):
    """Quit the tray application (does NOT stop services)."""
    icon.stop()


# ── Icon Creation ─────────────────────────────


def _create_icon_image(running: bool = False) -> Image.Image:
    """Create a simple tray icon — green circle if running, red if not."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer ring
    draw.ellipse([4, 4, size - 4, size - 4], outline=(59, 130, 246, 200), width=3)

    # Inner ring
    draw.ellipse([14, 14, size - 14, size - 14], outline=(6, 182, 212, 160), width=2)

    # Center dot — green if running, red if not
    center_color = (34, 197, 94, 255) if running else (239, 68, 68, 255)
    draw.ellipse([24, 24, size - 24, size - 24], fill=center_color)

    return img


def _update_icon(icon, running: bool):
    """Update the tray icon to reflect running state."""
    icon.icon = _create_icon_image(running)


# ── Main ──────────────────────────────────────


def main():
    running = is_running()

    menu = pystray.Menu(
        pystray.MenuItem("Open Dashboard", open_dashboard, default=True),
        pystray.MenuItem("API Documentation", open_api_docs),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Start Services", start_services),
        pystray.MenuItem("Stop Services", stop_services),
        pystray.MenuItem("Restart Services", restart_services),
        pystray.MenuItem("View Logs", view_logs),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit Tray App", quit_app),
    )

    icon = pystray.Icon(
        name="NetWatch AI",
        icon=_create_icon_image(running),
        title="NetWatch AI" + (" — Running" if running else " — Stopped"),
        menu=menu,
    )

    icon.run()


if __name__ == "__main__":
    main()
