#!/usr/bin/env python3
"""Tests for pre-tool-use-block-destructive.py"""

import json
import subprocess
import sys
import os

SCRIPT = os.path.join(os.path.dirname(__file__), "pre-tool-use-block-destructive.py")


def run_hook(command: str) -> dict:
    """Run the hook with a simulated Bash tool input."""
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command}
    })
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=payload,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode == 0 and result.stdout.strip():
        try:
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return {"decision": "allow", "raw": result.stdout}
    return {"decision": "allow"}


def test_blocked():
    """Commands that MUST be blocked."""
    blocked = [
        ("rm -rf /", "rm -rf"),
        ("rm -fr /home/user/data", "rm -rf"),
        ("sudo rm -rf /var/log", "rm -rf"),
        ("DROP TABLE users;", "DROP TABLE"),
        ("DROP TABLE IF EXISTS sessions;", "DROP TABLE"),
        ("TRUNCATE TABLE logs;", "TRUNCATE"),
        ("TRUNCATE users;", "TRUNCATE"),
        ("DELETE FROM users;", "DELETE FROM without WHERE"),
        ("git push --force origin main", "git push --force"),
        ("git push -f", "git push -f"),
        ("chmod 777 /etc/passwd", "chmod 777"),
        ("mkfs.ext4 /dev/sda1", "mkfs"),
        ("dd if=/dev/zero of=/dev/sda", "dd to /dev"),
    ]
    passed = 0
    failed = 0
    for cmd, expected_reason in blocked:
        result = run_hook(cmd)
        if result.get("decision") == "block":
            print(f"  ✅ BLOCKED: {cmd[:40]} — {result.get('reason', '')[:50]}")
            passed += 1
        else:
            print(f"  ❌ NOT BLOCKED: {cmd[:40]} (expected: {expected_reason})")
            failed += 1
    return passed, failed


def test_allowed():
    """Commands that MUST pass through."""
    allowed = [
        "ls -la /home/user",
        "rm file.txt",
        "git push origin main",
        "git push",
        "DELETE FROM users WHERE id = 5;",
        "chmod 644 config.yaml",
        "cat /etc/passwd",
        "echo hello world",
        "docker compose up -d",
        "ps aux | grep python",
        "pip install requests",
    ]
    passed = 0
    failed = 0
    for cmd in allowed:
        result = run_hook(cmd)
        if result.get("decision") != "block":
            print(f"  ✅ ALLOWED: {cmd[:40]}")
            passed += 1
        else:
            print(f"  ❌ FALSELY BLOCKED: {cmd[:40]} — {result.get('reason', '')[:50]}")
            failed += 1
    return passed, failed


if __name__ == "__main__":
    print("🧪 Testing blocked commands...")
    bp, bf = test_blocked()
    print()
    print("🧪 Testing allowed commands...")
    ap, af = test_allowed()
    print()
    total_p = bp + ap
    total_f = bf + af
    print(f"Results: {total_p} passed, {total_f} failed")
    if total_f > 0:
        sys.exit(1)
