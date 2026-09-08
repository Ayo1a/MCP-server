"""
One-step Cursor connection trigger for this project's MCP server (Windows).

Different shape from scripts/setup_goose.py / setup_gemini_cli.py: Cursor
needs no API key from the user - it has its own built-in AI/account. The MCP
server registration (.cursor/mcp.json) is also already committed in this repo,
so there's nothing to write either.

What this does:
1. Opens this project folder in Cursor (via the `cursor` CLI command).
2. Opens the cursor:// deeplink that pre-fills the "internal-system-bridge"
   MCP server install (same link documented in docs/setup_cursor.md).

What it deliberately does NOT do: click the approval prompt Cursor shows for
the deeplink. That's Cursor's own one-time trust gate, not something to
script around - same principle we've applied to every other client's
approval step.
"""

import subprocess
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEEPLINK = (
    "cursor://anysphere.cursor-deeplink/mcp/install"
    "?name=internal-system-bridge"
    "&config=eyJ1cmwiOiAiaHR0cDovLzEyNy4wLjAuMTo5MDAwL21jcCJ9"
)


def main() -> None:
    print("Opening this project in Cursor...")
    subprocess.run(["cursor", str(PROJECT_ROOT)], shell=True)

    print("Triggering the MCP server install deeplink...")
    webbrowser.open(DEEPLINK)

    print()
    print("Cursor should now show a one-time approval prompt for 'internal-system-bridge' - approve it.")
    print("Make sure core_api_mock and mcp_server (HTTP mode) are running before testing a tool call.")


if __name__ == "__main__":
    main()
