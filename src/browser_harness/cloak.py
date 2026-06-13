"""CloakBrowser launcher — auto-starts a stealth Chromium instance with CDP enabled.

When BU_CLOAK=1, the daemon calls ensure_cloak_browser() before connecting.
This finds the CloakBrowser binary, launches it headless with --remote-debugging-port,
and sets BU_CDP_URL so get_ws_url() picks it up naturally.

Env vars:
    BU_CLOAK=1              Enable CloakBrowser mode
    BU_CLOAK_PORT=9222      CDP port (default 9222)
    BU_CLOAK_WIDTH=1920     Viewport width
    BU_CLOAK_HEIGHT=1080    Viewport height
    BU_CLOAK_BINARY=        Override CloakBrowser binary path
"""
import json
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

_CLOAK_PORT_DEFAULT = 9222
_cloak_proc: subprocess.Popen | None = None


def _find_cloak_binary() -> str | None:
    """Locate the CloakBrowser Chromium binary."""
    # 1. Explicit override
    if explicit := os.environ.get("BU_CLOAK_BINARY"):
        if os.path.isfile(explicit):
            return explicit

    # 2. cloakbrowser CLI info
    try:
        result = subprocess.run(
            ["cloakbrowser", "info"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Binary:"):
                    path = line.split(":", 1)[1].strip()
                    if os.path.isfile(path):
                        return path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 3. Common install locations
    cloak_home = Path.home() / ".cloakbrowser"
    if cloak_home.is_dir():
        for d in sorted(cloak_home.iterdir(), reverse=True):
            if d.name.startswith("chromium-"):
                binary = d / "chrome"
                if binary.is_file():
                    return str(binary)

    # 4. which chromium-browser / google-chrome as fallback
    for name in ("chromium-browser", "google-chrome", "chromium"):
        try:
            result = subprocess.run(
                ["which", name], capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    return None


def _cdp_alive(port: int) -> bool:
    """Check if a CDP endpoint is responding on the given port."""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/json/version", timeout=2
        ) as r:
            data = json.loads(r.read())
            return "webSocketDebuggerUrl" in data
    except Exception:
        return False


def ensure_cloak_browser() -> str | None:
    """Launch CloakBrowser if BU_CLOAK=1 and it's not already running.

    Returns the CDP URL (e.g. http://127.0.0.1:9222) or None if not in cloak mode.
    Sets BU_CDP_URL as a side effect so get_ws_url() picks it up.
    """
    global _cloak_proc

    if not os.environ.get("BU_CLOAK"):
        return None

    port = int(os.environ.get("BU_CLOAK_PORT", _CLOAK_PORT_DEFAULT))
    cdp_url = f"http://127.0.0.1:{port}"

    # Already running?
    if _cdp_alive(port):
        os.environ["BU_CDP_URL"] = cdp_url
        return cdp_url

    # Find binary
    binary = _find_cloak_binary()
    if not binary:
        raise RuntimeError(
            "BU_CLOAK=1 but CloakBrowser binary not found. "
            "Install: uv tool install cloakbrowser && cloakbrowser install"
        )

    width = os.environ.get("BU_CLOAK_WIDTH", "1920")
    height = os.environ.get("BU_CLOAK_HEIGHT", "1080")

    cmd = [
        binary,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-gpu",
        "--no-sandbox",
        f"--window-size={width},{height}",
        "about:blank",
    ]

    _cloak_proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for CDP to be ready
    deadline = time.time() + 15
    while time.time() < deadline:
        if _cdp_alive(port):
            os.environ["BU_CDP_URL"] = cdp_url
            return cdp_url
        if _cloak_proc.poll() is not None:
            raise RuntimeError(
                f"CloakBrowser exited immediately (code {_cloak_proc.returncode}). "
                f"Binary: {binary}"
            )
        time.sleep(0.3)

    raise RuntimeError(
        f"CloakBrowser started but CDP not ready on port {port} after 15s. "
        f"PID: {_cloak_proc.pid}"
    )


def shutdown_cloak_browser():
    """Kill the CloakBrowser process if we launched it."""
    global _cloak_proc
    if _cloak_proc and _cloak_proc.poll() is None:
        try:
            _cloak_proc.send_signal(signal.SIGTERM)
            _cloak_proc.wait(timeout=5)
        except Exception:
            try:
                _cloak_proc.kill()
            except Exception:
                pass
    _cloak_proc = None
