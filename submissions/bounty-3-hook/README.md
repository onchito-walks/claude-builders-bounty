# Pre-Tool-Use Safety Hook

A Claude Code `pre-tool-use` hook that intercepts and blocks destructive bash commands before execution.

## What It Blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | Destroys database table |
| `TRUNCATE` | Empties database table |
| `DELETE FROM` (no WHERE) | Deletes all rows |
| `git push --force` | Overwrites remote history |
| `chmod 777` | Insecure world-writable permissions |
| Fork bomb `:(){ :|:& };:` | System crash |
| `dd of=/dev/` | Direct disk write |
| `mkfs` | Filesystem format |

## Install

```bash
# 1. Copy the hook
mkdir -p ~/.claude/hooks
cp pre-tool-use-block-destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use-block-destructive.py

# 2. Add to Claude Code settings
# Edit ~/.claude/settings.json and add:
```

```json
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
```

That's it. The next time Claude Code tries to run a destructive command, it gets blocked.

## How It Works

1. Claude Code sends tool-use events to the hook via stdin as JSON
2. The hook checks the bash command against a list of dangerous patterns
3. If matched: the command is blocked, logged, and Claude receives an explanation
4. If safe: the command passes through normally

## Blocked Command Log

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with:

```
2026-05-11T03:44:12Z | rm -rf: recursive force delete | rm -rf /tmp/test | /home/user/project
```

Format: `timestamp | reason | command | project_path`

## Testing

```bash
python3 test_hook.py
```

Expected output: `Results: 24 passed, 0 failed`

## Uninstall

Remove the hook entry from `~/.claude/settings.json` and delete the script:

```bash
rm ~/.claude/hooks/pre-tool-use-block-destructive.py
```
