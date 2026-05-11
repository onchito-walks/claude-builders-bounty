# claude-review — PR Review Agent

Automated PR review agent that analyzes diffs and outputs structured Markdown reviews.

## Install

```bash
pip install claude-review
# or just copy claude-review.py to your project
```

## Usage

### CLI

```bash
# Review a public PR
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# Review with GitHub token (for private repos / rate limits)
GITHUB_TOKEN=ghp_xxx python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# Review from a local diff file
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --diff changes.diff

# Save output to file
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action

Copy `.github/workflows/pr-review.yml` to your repo. Reviews are posted automatically on every PR.

## Output Format

```markdown
# PR Review: https://github.com/owner/repo/pull/123

## Summary
This PR "Add auth flow" changes 5 file(s) with 120 addition(s) and 30 deletion(s). 2 risk(s) identified.

## Changed Files (5)
- `src/auth.ts`
- `src/middleware.ts`
- `tests/auth.test.ts`

## Stats
- **Additions:** 120
- **Deletions:** 30
- **Files:** 5

## Identified Risks
- 🟡 eval() detected (1 occurrence)
- 🟡 Large diff: 150 lines — consider splitting

## Improvement Suggestions
- No test files modified — consider adding tests

## Confidence Score
**🟡 Medium**
```

## What It Detects

### Risks (🔴 High / 🟡 Medium)
- Hardcoded credentials (password, secret, api_key)
- Code injection vectors (eval, exec, subprocess)
- XSS risks (innerHTML, document.write)
- Database destruction (DROP TABLE, TRUNCATE)
- Destructive operations (rm -rf)
- Large diffs (>500 lines)
- Too many files changed (>15)

### Suggestions (improvement opportunities)
- Missing tests for new code
- Debug statements left in (console.log, print)
- TODO/FIXME/HACK comments
- Skipped tests

### Confidence Score
- **🟢 High:** Small diff, few risks
- **🟡 Medium:** Moderate size or some risks
- **🔴 Low:** Large diff or many risks

## Tested On

### Test 1: claude-builders-bounty PR #912

```bash
$ python3 claude-review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/912
```

Output: Structured review with file listing, stats, and risk assessment.

### Test 2: A known large PR

```bash
$ python3 claude-review.py --pr https://github.com/microsoft/vscode/pull/200000
```

Output: Low confidence score with risk warnings about diff size.

## Requirements

- Python 3.8+
- Internet access for API calls (or use --diff for offline)
