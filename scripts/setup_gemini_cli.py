"""
One-step Gemini CLI setup for this project's MCP server (Windows).

Separate from scripts/setup_goose.py - different tool, different config format,
different env var. Do not merge them.

Unlike Goose, the MCP server registration itself (.gemini/settings.json) is
already committed in this repo, so a fresh clone already has it. The only two
things a new user actually needs are:
1. A Gemini API key (from Google AI Studio).
2. This project's folder marked as trusted - Gemini CLI disables all MCP
   servers in a folder it hasn't seen before.

What this does:
1. Asks for your Gemini API key (hidden input) and saves it as the
   GEMINI_API_KEY environment variable - persisted for future terminals
   (setx) and set immediately for this process, so nothing needs restarting.
2. Adds this project's folder to ~/.gemini/trustedFolders.json with the value
   "TRUST_FOLDER" - the exact format Gemini CLI itself writes there (verified
   against a real, already-trusted entry), so the trust prompt never appears.
   Existing entries in that file are preserved, not overwritten.
3. Launches `npx @google/gemini-cli` directly, so you land in a working
   session immediately.
"""

import getpass
import json
import os
import subprocess
import sys
from pathlib import Path

TRUSTED_FOLDERS_PATH = Path.home() / ".gemini" / "trustedFolders.json"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def normalized_project_path() -> str:
    # Gemini CLI stores trust keys as lowercase, forward-slash paths
    # (verified against a real entry in trustedFolders.json).
    return str(PROJECT_ROOT).replace("\\", "/").lower()


def load_trusted_folders() -> dict:
    if TRUSTED_FOLDERS_PATH.exists():
        return json.loads(TRUSTED_FOLDERS_PATH.read_text(encoding="utf-8")) or {}
    return {}


def main() -> None:
    print("Gemini CLI + internal-system-bridge setup")
    print("-------------------------------------------")
    api_key = getpass.getpass("Paste your Gemini API key (hidden, from Google AI Studio): ").strip()
    if not api_key:
        print("No key entered - aborting.")
        sys.exit(1)

    # Persist at the user level so Gemini CLI finds it automatically in future
    # terminals, and set it for this process so we can launch a session below
    # without needing a new terminal.
    subprocess.run(["setx", "GEMINI_API_KEY", api_key], check=True, capture_output=True)
    os.environ["GEMINI_API_KEY"] = api_key

    trusted = load_trusted_folders()
    trusted[normalized_project_path()] = "TRUST_FOLDER"
    TRUSTED_FOLDERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRUSTED_FOLDERS_PATH.write_text(json.dumps(trusted, indent=2), encoding="utf-8")

    print()
    print(f"Done. Trusted {PROJECT_ROOT} and saved GEMINI_API_KEY.")
    print("Starting Gemini CLI now...")
    print()

    subprocess.run(["npx", "@google/gemini-cli"], cwd=PROJECT_ROOT, shell=True)


if __name__ == "__main__":
    main()
