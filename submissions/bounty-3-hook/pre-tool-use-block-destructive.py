#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.

Install:
  cp pre-tool-use-block-destructive.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/pre-tool-use-block-destructive.py

Then add to ~/.claude/settings.json:
  {
    "hooks": {
      "pre-tool-use": [
        {
          "command": "python3 ~/.claude/hooks/pre-tool-use-block-destructive.py",
          "tools": ["Bash"]
        }
      ]
    }
  }

See: https://docs.anthropic.com/claude-code/hooks
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

BLOCKED_PATTERNS = [
    # rm -rf variants
    (r"\brm\s+.*-[a-zA-Z]*f[a-zA-Z]*\s+.*-[a-zA-Z]*r[a-zA-Z]*\s", "rm -rf: recursive force delete"),
    (r"\brm\s+.*-[a-zA-Z]*r[a-zA-Z]*\s+.*-[a-zA-Z]*f[a-zA-Z]*\s", "rm -rf: recursive force delete"),
    (r"\brm\s+-rf\b", "rm -rf: recursive force delete"),
    (r"\brm\s+-fr\b", "rm -rf: recursive force delete"),
    # DROP TABLE
    (r"\bDROP\s+TABLE\b", "DROP TABLE: destroys database table"),
    # TRUNCATE
    (r"\bTRUNCATE\s+TABLE?\b", "TRUNCATE: empties database table"),
    (r"\bTRUNCATE\b", "TRUNCATE: empties database table"),
    # DELETE FROM without WHERE
    (r"\bDELETE\s+FROM\b(?![\s\S]*?\bWHERE\b)", "DELETE FROM without WHERE: deletes all rows"),
    # git push --force
    (r"\bgit\s+push\s+.*--force\b", "git push --force: overwrites remote history"),
    (r"\bgit\s+push\s+.*-f\b", "git push -f: overwrites remote history"),
    # chmod 777
    (r"\bchmod\s+777\b", "chmod 777: insecure world-writable permissions"),
    # :(){ :|:& };: (fork bomb)
    (r":\(\)\{\s*:\|:&\s*\};:", "fork bomb detected"),
    # dd to disk
    (r"\bdd\s+.*of=/dev/", "dd to /dev: direct disk write"),
    # mkfs
    (r"\bmkfs\b", "mkfs: filesystem format command"),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def log_blocked(command: str, reason: str) -> None:
    """Log a blocked command attempt."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    project = os.getcwd()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | {reason} | {command} | {project}\n")


def check_command(command: str) -> tuple[bool, str]:
    """
    Check if a command matches any blocked pattern.
    Returns (is_blocked, reason).
    """
    normalized = " ".join(command.split())

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE | re.DOTALL):
            return True, reason

    # Special check: DELETE FROM without WHERE
    if re.search(r"\bDELETE\s+FROM\b", normalized, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", normalized, re.IGNORECASE):
            return True, "DELETE FROM without WHERE: deletes all rows"

    return False, ""


def main():
    """Read tool input from stdin, check command, output decision."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked(command, reason)
        response = {
            "decision": "block",
            "reason": f"🚫 BLOCKED: {reason}. This command was intercepted by the safety hook and logged to {LOG_FILE}. If you're sure this is safe, ask the user to run it manually.",
        }
        print(json.dumps(response))
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
