#!/usr/bin/env python3
"""
claude-review — PR review agent that analyzes a PR diff and outputs structured Markdown.

Usage:
  python3 claude-review.py --pr https://github.com/owner/repo/pull/123
  python3 claude-review.py --diff diff.txt --pr https://github.com/owner/repo/pull/123

Requires GITHUB_TOKEN env var for private repos (optional for public).

Output: Structured Markdown with summary, risks, suggestions, and confidence score.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error


def fetch_pr_diff(pr_url: str, token: str = None) -> str:
    """Fetch the diff for a GitHub PR."""
    # Parse PR URL: https://github.com/owner/repo/pull/123
    parts = pr_url.rstrip("/").split("/")
    if len(parts) < 7 or "pull" not in parts:
        raise ValueError(f"Invalid PR URL: {pr_url}")

    owner = parts[-4]
    repo = parts[-3]
    pr_number = parts[-1]

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API error: {e.code} — {e.read().decode()[:200]}")


def fetch_pr_metadata(pr_url: str, token: str = None) -> dict:
    """Fetch PR metadata (title, description, changed files)."""
    parts = pr_url.rstrip("/").split("/")
    owner = parts[-4]
    repo = parts[-3]
    pr_number = parts[-1]

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {"User-Agent": "claude-review/1.0", "Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {}


def analyze_diff(diff_text: str, metadata: dict = None) -> dict:
    """Analyze a diff and return structured review data."""
    if not diff_text or diff_text.strip() == "":
        return {
            "summary": "Empty diff — no changes to review.",
            "risks": [],
            "suggestions": [],
            "confidence": "High",
        }

    files_changed = []
    additions = 0
    deletions = 0
    current_file = None

    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            parts = line.split(" b/")
            if len(parts) >= 2:
                current_file = parts[-1].strip()
                files_changed.append(current_file)
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    # Detect risks
    risks = []
    suggestions = []

    # Check for dangerous patterns
    danger_patterns = {
        "rm -rf": "Destructive file operation detected",
        "DROP TABLE": "Database schema destruction",
        "TRUNCATE": "Database data truncation",
        "DELETE FROM": "Bulk data deletion without WHERE clause",
        "eval(": "Use of eval() — potential code injection risk",
        "exec(": "Use of exec() — potential code injection risk",
        "subprocess.call": "Subprocess call — verify input sanitization",
        "innerHTML": "Direct innerHTML assignment — XSS risk",
        "document.write": "document.write — XSS and performance risk",
        "localStorage": "localStorage usage — consider security implications",
        "TODO": "TODO comment left in code",
        "FIXME": "FIXME comment left in code",
        "HACK": "HACK comment — indicates technical debt",
        "console.log": "Debug console.log left in code",
        "print(": "Debug print statement left in code",
        "password": "Possible hardcoded credential detected",
        "secret": "Possible hardcoded secret detected",
        "api_key": "Possible hardcoded API key detected",
        ".skip()": "Test skip detected — may hide real issues",
        "xit(": "Skipped test detected",
        "xdescribe": "Skipped test suite detected",
    }

    for pattern, message in danger_patterns.items():
        if pattern.lower() in diff_text.lower():
            # Count occurrences
            count = diff_text.lower().count(pattern.lower())
            if count > 0:
                if pattern in ("TODO", "FIXME", "HACK", "console.log", "print("):
                    suggestions.append(f"{message} ({count} occurrence(s))")
                elif pattern in ("password", "secret", "api_key"):
                    risks.append(f"🔴 {message}")
                else:
                    risks.append(f"🟡 {message} ({count} occurrence(s))")

    # Large diff warning
    total_lines = additions + deletions
    if total_lines > 500:
        risks.append(f"🟡 Large diff: {total_lines} lines changed — consider splitting into smaller PRs")

    # Many files changed
    if len(files_changed) > 15:
        risks.append(f"🟡 Many files changed: {len(files_changed)} — consider scope reduction")

    # No tests modified
    test_files = [f for f in files_changed if any(t in f.lower() for t in ["test", "spec", "__tests__"])]
    if files_changed and not test_files and additions > 20:
        suggestions.append("No test files modified — consider adding tests for new functionality")

    # Only tests modified (no src changes)
    src_files = [f for f in files_changed if not any(t in f.lower() for t in ["test", "spec", "__tests__"])]
    if not src_files and test_files:
        suggestions.append("Only test files modified — verify this is intentional")

    # Confidence score
    if total_lines > 1000:
        confidence = "Low"
    elif total_lines > 300 or len(risks) > 3:
        confidence = "Medium"
    else:
        confidence = "High"

    # Build summary
    title = metadata.get("title", "") if metadata else ""
    summary_parts = []
    if title:
        summary_parts.append(f'PR "{title}"')
    summary_parts.append(
        f"changes {len(files_changed)} file(s) with {additions} addition(s) and {deletions} deletion(s)."
    )
    summary = "This PR " + " ".join(summary_parts)

    if risks:
        summary += f" {len(risks)} risk(s) identified."
    if suggestions:
        summary += f" {len(suggestions)} suggestion(s) for improvement."

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "files_changed": files_changed,
        "stats": {"additions": additions, "deletions": deletions, "files": len(files_changed)},
    }


def format_review(review: dict, pr_url: str) -> str:
    """Format review data as Markdown."""
    lines = [
        f"# PR Review: {pr_url}",
        "",
        f"## Summary",
        "",
        review["summary"],
        "",
        f"## Changed Files ({review['stats']['files']})",
        "",
    ]

    for f in review.get("files_changed", []):
        lines.append(f"- `{f}`")

    lines.extend([
        "",
        f"## Stats",
        "",
        f"- **Additions:** {review['stats']['additions']}",
        f"- **Deletions:** {review['stats']['deletions']}",
        f"- **Files:** {review['stats']['files']}",
        "",
    ])

    if review["risks"]:
        lines.extend(["## Identified Risks", ""])
        for risk in review["risks"]:
            lines.append(f"- {risk}")
        lines.append("")

    if review["suggestions"]:
        lines.extend(["## Improvement Suggestions", ""])
        for suggestion in review["suggestions"]:
            lines.append(f"- {suggestion}")
        lines.append("")

    confidence = review["confidence"]
    emoji = {"Low": "🔴", "Medium": "🟡", "High": "🟢"}.get(confidence, "⚪")
    lines.extend([
        "## Confidence Score",
        "",
        f"**{emoji} {confidence}**",
        "",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="PR review agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--diff", help="Local diff file (skips API fetch)")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")

    # Get diff
    if args.diff:
        with open(args.diff) as f:
            diff_text = f.read()
    else:
        print(f"Fetching diff from {args.pr}...", file=sys.stderr)
        diff_text = fetch_pr_diff(args.pr, token)

    # Get metadata
    metadata = fetch_pr_metadata(args.pr, token)

    # Analyze
    review = analyze_diff(diff_text, metadata)

    # Format
    markdown = format_review(review, args.pr)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(markdown)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
