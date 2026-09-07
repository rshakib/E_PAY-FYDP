from pathlib import Path
import os
import shutil
import socket
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
FRONTEND_INDEX_FILE = FRONTEND_DIR / "dist" / "index.html"
TLS_CERT_FILE = ROOT_DIR.parent / "nginx" / "ssl" / "selfsigned.crt"
TLS_KEY_FILE = ROOT_DIR.parent / "nginx" / "ssl" / "selfsigned.key"


def is_enabled(name: str, default: bool = True) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def npm_executable() -> str | None:
    return shutil.which("npm") or shutil.which("npm.cmd")


def ensure_frontend_build() -> None:
    if FRONTEND_INDEX_FILE.is_file() or not is_enabled("AUTO_BUILD_FRONTEND", True):
        return

    npm = npm_executable()
    if not npm:
        print(
            "Frontend build is missing, and npm was not found on PATH. "
            "Install Node.js, then run `cd e_banking/frontend && npm install && npm run build`.",
            flush=True,
        )
        return

    print("Frontend build is missing. Building it now...", flush=True)
    install_command = [npm, "ci"] if (FRONTEND_DIR / "package-lock.json").is_file() else [npm, "install"]
    if not (FRONTEND_DIR / "node_modules").is_dir():
        subprocess.run(install_command, cwd=FRONTEND_DIR, check=True)
    subprocess.run([npm, "run", "build"], cwd=FRONTEND_DIR, check=True)


def ssl_context():
    if not is_enabled("ENABLE_TLS", True):
        return None
    if TLS_CERT_FILE.is_file() and TLS_KEY_FILE.is_file():
        return str(TLS_CERT_FILE), str(TLS_KEY_FILE)
    print(
        "TLS certificate files were not found. Starting local Flask server over HTTP. "
        "Expected cert files under nginx/ssl/.",
        flush=True,
    )
    return None


ensure_frontend_build()

os.chdir(PROJECT_DIR)
sys.path.insert(0, str(PROJECT_DIR))

from app import app  # noqa: E402


def choose_port(preferred_port: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sock.connect_ex(("127.0.0.1", preferred_port)) != 0:
            return preferred_port

    fallback_port = preferred_port + 1
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        while sock.connect_ex(("127.0.0.1", fallback_port)) == 0:
            fallback_port += 1
    print(f"Port {preferred_port} is already in use. Starting on port {fallback_port} instead.")
    return fallback_port


if __name__ == "__main__":
    port = choose_port(int(os.environ.get("PORT", "5001")))
    context = ssl_context()
    scheme = "https" if context else "http"
    print(f"Starting local server at {scheme}://localhost:{port}", flush=True)
    app.run(debug=True, port=port, use_reloader=False, ssl_context=context)
