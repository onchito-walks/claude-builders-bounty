---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag
trigger: /generate-changelog
---

# Generate Changelog Skill

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage

Run `/generate-changelog` in Claude Code, or use the standalone script:

```bash
bash changelog.sh
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
| `change:`, `update:`, `refactor:`, `refactor(`, `chore:`, `deps:` | Changed |
| `remove:`, `delete:`, `deprecate:`, `drop:` | Removed |
| No recognized prefix | Changed (default) |

## Output Format

```markdown
## [Unreleased] - 2026-05-11

### Added
- feat: add user authentication endpoint (#42)

### Fixed
- fix: resolve null pointer in payment handler (#39)

### Changed
- refactor: optimize database query performance (#40)

### Removed
- remove: deprecated v1 API endpoints (#38)
```

## Instructions

When the user runs `/generate-changelog`:

1. Run `git describe --tags --abbrev=0 2>/dev/null` to find the last tag
2. If no tag exists, use all commits from the repo start
3. Run `git log --format="%H|%s" [last_tag]..HEAD` to get commits
4. For each commit message, classify it using the prefix rules above
5. Group by category and format as CHANGELOG.md
6. If CHANGELOG.md already exists, prepend the new entry; otherwise create it
7. Show the generated entry to the user for review before writing
