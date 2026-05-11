# Weekly GitHub Dev Summary — n8n + Claude

Automated weekly narrative summary of GitHub repo activity, powered by Claude.

## Setup (5 steps)

### 1. Import the workflow
In n8n: **Menu → Import from File** → select `weekly-github-summary-workflow.json`

### 2. Configure credentials
Create these credentials in n8n:
- **HTTP Header Auth** (name: `GitHub Token`): Header name `Authorization`, value `Bearer ghp_YOUR_TOKEN`
- **Anthropic API** (name: `Claude API`): Your Anthropic API key

### 3. Set environment variables
```
GITHUB_REPO=owner/repo          # Target repository
GITHUB_CREDENTIAL_ID=<id>       # n8n credential ID for GitHub
ANTHROPIC_CREDENTIAL_ID=<id>    # n8n credential ID for Claude
DELIVERY_METHOD=discord         # "discord" or "email"
DISCORD_WEBHOOK_URL=<url>       # If using Discord
# OR for email:
EMAIL_FROM=noreply@example.com
EMAIL_TO=team@example.com
SMTP_CREDENTIAL_ID=<id>
SUMMARY_LANGUAGE=EN             # EN or FR
```

### 4. Activate the workflow
Click **Active** toggle in n8n. It will run every Friday at 5 PM UTC.

### 5. Test manually
Click **Execute Workflow** to verify. Check the output of the "Generate Summary with Claude" node.

## How it works

1. **Cron Trigger** — Fires every Friday at 5 PM (configurable)
2. **GitHub API** — Fetches commits, closed issues, and merged PRs from the past week
3. **Data Processing** — Formats raw GitHub data into structured summaries
4. **Claude API** — Generates a professional narrative summary using `claude-sonnet-4-20250514`
5. **Delivery** — Sends the summary via Discord webhook OR email (configurable)

## Configuration options

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REPO` | required | GitHub repo in `owner/repo` format |
| `DELIVERY_METHOD` | `discord` | Delivery channel: `discord` or `email` |
| `SUMMARY_LANGUAGE` | `EN` | Summary language: `EN` (English) or `FR` (French) |
| `DISCORD_WEBHOOK_URL` | — | Discord webhook URL for delivery |
| `EMAIL_TO` | — | Recipient email address |

## Output example

```
## Weekly Dev Summary — myorg/myrepo

### Executive Overview
This week saw 47 commits across 12 contributors, with 3 feature PRs merged
and 8 issues closed. The team shipped the new auth module and fixed critical
caching bugs.

### Key Achievements
- #142 New OAuth2 module with PKCE support (merged by @alice, +2,340/-180)
- `a3f7b2c` Refactored connection pool for 40% throughput improvement

### Bug Fixes
- #98 Resolved session expiry race condition
- #101 Fixed timezone handling in scheduled reports
...
```

## License
MIT
