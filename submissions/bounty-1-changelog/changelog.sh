#!/usr/bin/env bash
# Generate CHANGELOG.md from git history since the last tag
# Usage: bash changelog.sh [--dry-run] [--output FILE]

set -euo pipefail

DRY_RUN=false
OUTPUT_FILE="CHANGELOG.md"
CATEGORIES=("Added" "Fixed" "Changed" "Removed")

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--dry-run] [--output FILE]"
      echo "Generates CHANGELOG.md from git history since the last tag."
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Check if we're in a git repo
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: Not in a git repository" >&2
  exit 1
fi

# Find the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [[ -z "$LAST_TAG" ]]; then
  echo "No tags found — using all commits from repo start"
  RANGE="HEAD"
else
  RANGE="${LAST_TAG}..HEAD"
  echo "Found last tag: ${LAST_TAG}"
fi

# Get commits since last tag
COMMITS=$(git log --format="%H|%s" "$RANGE" 2>/dev/null || true)
if [[ -z "$COMMITS" ]]; then
  echo "No commits found since ${LAST_TAG:-repo start}"
  exit 0
fi

# Categorize commits
declare -A CATEGORY_MAP
CATEGORY_MAP=(
  ["feat:"]="Added"
  ["add:"]="Added"
  ["feature:"]="Added"
  ["fix:"]="Fixed"
  ["bugfix:"]="Fixed"
  ["patch:"]="Fixed"
  ["change:"]="Changed"
  ["update:"]="Changed"
  ["refactor:"]="Changed"
  ["refactor("]="Changed"
  ["chore:"]="Changed"
  ["deps:"]="Changed"
  ["remove:"]="Removed"
  ["delete:"]="Removed"
  ["deprecate:"]="Removed"
  ["drop:"]="Removed"
)

# Group commits by category
declare -A GROUPED
for cat in "${CATEGORIES[@]}"; do
  GROUPED["$cat"]=""
done

while IFS='|' read -r hash subject; do
  [[ -z "$subject" ]] && continue

  # Find matching prefix
  category="Changed"  # default
  for prefix in "${!CATEGORY_MAP[@]}"; do
    if [[ "$subject" == "$prefix"* ]]; then
      category="${CATEGORY_MAP[$prefix]}"
      break
    fi
  done

  # Add to group
  GROUPED["$category"]+="- ${subject} (${hash:0:7})"$'\n'
done <<< "$COMMITS"

# Generate changelog entry
TODAY=$(date +%Y-%m-%d)
VERSION="[Unreleased]"
if [[ -n "$LAST_TAG" ]]; then
  LAST_VER="${LAST_TAG#v}"
  if [[ "$LAST_VER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    MAJOR="${LAST_VER%%.*}"
    MINOR="${LAST_VER#*.}"
    MINOR="${MINOR%.*}"
    PATCH="${LAST_VER##*.}"
    NEXT_PATCH=$((PATCH + 1))
    VERSION="[${MAJOR}.${MINOR}.${NEXT_PATCH}]"
  fi
fi

ENTRY="## ${VERSION} - ${TODAY}"$'\n'$'\n'

for cat in "${CATEGORIES[@]}"; do
  content="${GROUPED[$cat]}"
  if [[ -n "$content" ]]; then
    ENTRY+="### ${cat}"$'\n'$'\n'
    ENTRY+="$content"$'\n'
  fi
done

# Output
if [[ "$DRY_RUN" == true ]]; then
  echo "$ENTRY"
  exit 0
fi

# Write to file
if [[ -f "$OUTPUT_FILE" ]]; then
  TEMP=$(mktemp)
  {
    echo "$ENTRY"
    echo ""
    cat "$OUTPUT_FILE"
  } > "$TEMP"
  mv "$TEMP" "$OUTPUT_FILE"
  echo "Updated ${OUTPUT_FILE} (prepended new entry)"
else
  echo "$ENTRY" > "$OUTPUT_FILE"
  echo "Created ${OUTPUT_FILE}"
fi

# Show preview
echo ""
echo "Preview:"
echo "---"
head -20 "$OUTPUT_FILE"
