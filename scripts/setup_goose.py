"""
One-step Goose setup for this project's MCP server (Windows).

Assumes:
- Goose CLI is already installed (see docs/setup_goose.md for the install command).
- You have (or will create) a free Gemini API key from Google AI Studio.

What this does:
1. Asks for your Gemini API key (input hidden) and saves it as the GOOGLE_API_KEY
   user environment variable. This is Goose's documented override for reading a
   provider key without touching its OS credential store - we deliberately avoid
   writing directly into Goose's keyring, since its exact stored format there is
   undocumented and not worth guessing.
2. Writes the Google provider + internal-system-bridge extension entries into
   Goose's config.yaml, using the exact schema Goose itself generated during a
   real, manually-verified setup - existing settings in that file are preserved,
   not overwritten wholesale.

Make sure core_api_mock and mcp_server (HTTP mode) are already running before
you launch this script - it finishes by launching `goose session` directly, so
you're talking to the MCP server's tools immediately, no extra steps.
"""

import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

MCP_SERVER_URL = "http://127.0.0.1:9000/mcp"
EXTENSION_NAME = "internal-system-bridge"
CONFIG_PATH = Path(os.environ["APPDATA"]) / "Block" / "goose" / "config" / "config.yaml"
FALLBACK_GOOSE_PATH = Path.home() / ".local" / "bin" / "goose.exe"


def find_goose() -> str:
    # goose.exe often isn't on PATH for freshly-opened terminals even after
    # install, so fall back to its known default install location.
    on_path = shutil.which("goose")
    if on_path:
        return on_path
    if FALLBACK_GOOSE_PATH.exists():
        return str(FALLBACK_GOOSE_PATH)
    print(f"Could not find goose.exe on PATH or at {FALLBACK_GOOSE_PATH}.")
    print("Install it first - see docs/setup_goose.md.")
    sys.exit(1)


def load_existing_config() -> dict:
    # Load whatever Goose already has so we only add/update our own keys,
    # instead of clobbering the rest of the user's config.
    if CONFIG_PATH.exists():
        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return {}


def main() -> None:
    print("Goose + internal-system-bridge setup")
    print("-------------------------------------")
    api_key = getpass.getpass("Paste your Gemini API key (hidden, from Google AI Studio): ").strip()
    if not api_key:
        print("No key entered - aborting.")
        sys.exit(1)

    # Persist at the user level so Goose finds it automatically in future sessions...
    subprocess.run(["setx", "GOOGLE_API_KEY", api_key], check=True, capture_output=True)
    # ...and also set it for THIS process right now, since setx alone only affects
    # terminals opened after this point - this lets us launch `goose session`
    # below with the key already active, no new terminal needed.
    os.environ["GOOGLE_API_KEY"] = api_key

    config = load_existing_config()

    config["active_provider"] = "google"
    providers = config.setdefault("providers", {})
    providers["google"] = {
        "enabled": True,
        "model": "gemini-3.5-flash",
        "configured": True,
    }

    extensions = config.setdefault("extensions", {})
    extensions[EXTENSION_NAME] = {
        "enabled": True,
        "type": "streamable_http",
        "name": EXTENSION_NAME,
        "description": "Internal Core API tools (system reports, health check, image metadata) - local dev MCP server",
        "uri": MCP_SERVER_URL,
        "envs": {},
        "env_keys": [],
        "headers": {},
        "timeout": 300,
        "socket": None,
        "bundled": None,
    }

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    print()
    print(f"Done. Updated {CONFIG_PATH}")
    print("GOOGLE_API_KEY saved as a persistent user environment variable.")
    print()
    print("Starting goose session now...")
    print()

    goose_path = find_goose()
    subprocess.run([goose_path, "session"])


if __name__ == "__main__":
    main()
