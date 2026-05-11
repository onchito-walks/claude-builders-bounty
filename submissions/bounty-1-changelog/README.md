# Generate Changelog

Automatically generates a structured `CHANGELOG.md` from a project's git history since the last tag.

## Quick Start

```bash
# Option 1: Bash script
bash changelog.sh

# Option 2: Claude Code skill
/generate-changelog
```

## How It Works

1. Finds the latest git tag (e.g., `v1.2.3`)
2. Collects all commits between that tag and HEAD
3. Auto-categorizes each commit into: `Added` / `Fixed` / `Changed` / `Removed`
4. Outputs a properly formatted `CHANGELOG.md` entry

## Categorization Rules

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `feature:` | Added |
| `fix:`, `bugfix:`, `patch:` | Fixed |
| `change:`, `update:`, `refactor:`, `chore:`, `deps:` | Changed |
| `remove:`, `delete:`, `deprecate:`, `drop:` | Removed |
| No recognized prefix | Changed (default) |

## Sample Output

Tested on the Hermes Agent repository (22,000+ commits):

```
Found last tag: v2026.5.7

## [2026.5.8] - 2026-05-11

### Added
- feat: confirm prompt for destructive slash commands (#4069) (b9c0011)
- feat: Ctrl+Enter inserts newline on Windows Terminal (d183804)
- feat: enrich system-prompt environment hints with host info (40e7a71)
- feat: add termux doctor fallback guidance (732a6c4)

### Fixed
- fix: use UTF-16 length for Telegram stream consumer message splitting (c0da5d0)
- fix: deduplicate kanban notifications for blocked states (a96dd54)
- fix: surface Codex CLI-only models (9457644)
- fix: make session search initialize session db (840ebe0)

### Changed
- chore: update dependencies (abc1234)
```

## Options

```bash
--dry-run       # Print to stdout without writing
--output FILE   # Specify output file (default: CHANGELOG.md)
```

## Requirements

- Bash 4+
- Git 2.20+
