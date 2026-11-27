# 🐍 Python Automation Toolkit

> **Code once → automate repeated work.**

Eight small, practical Python scripts. Each one covers a common task you can automate: coding chores, system administration, or defensive security.

| # | Task | Script | What it does |
|---|------|--------|--------------|
| 01 | File Automation | `automations/file_automation.py` | Sort files into folders by type, bulk-rename them, make timestamped zip backups |
| 02 | Web Automation | `automations/web_automation.py` | Scrape a page's title and links, find broken links |
| 03 | Data Processing | `automations/data_processing.py` | Clean, filter, summarize and convert CSV data (CSV/JSON/Excel) |
| 04 | System Monitoring | `automations/system_monitor.py` | Log CPU/RAM/disk use and top processes, warn when limits are passed |
| 05 | Cybersecurity | `automations/security_checks.py` | Find brute-force SSH logins in auth logs, check file integrity with SHA-256 |
| 06 | Network Automation | `automations/network_tools.py` | Resolve DNS and check which ports are open |
| 07 | API Automation | `automations/api_automation.py` | Fetch JSON from REST APIs with retries, pick fields, save the result |
| 08 | Reporting | `automations/reporting.py` | Build Excel and HTML summary reports from a CSV |

## 🎬 YouTube Agent (Claude Code skills)

One idea in → a finished video package out. A main agent plus four modules, each with one job:

| Skill | Module | What it does |
|---|---|---|
| `/youtube-agent` | Main agent | Sets up the channel once (niche, voice, audience → `youtube/channel.md`, `youtube/voice.md`), then routes any idea through the modules |
| `/youtube-plan` | 1 · Plan | What to post, when to post, the whole-week plan |
| `/youtube-create` | 2 · Create | Script from 21 hook formulas, titles, thumbnail concepts, description, edit plan |
| `/youtube-engage` | 3 · Engage | Read and sort comments, draft replies in your voice, who to engage with |
| `/youtube-virality` | 4 · Virality | Scan top videos by outlier score, break down why they won, rework them in your voice |

Start with `/youtube-agent setup`, then `/youtube-agent a video idea for my channel: ...`.

Live YouTube data (top videos, niche scans, comments) uses a free, read-only
[YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com) key:

```bash
export YOUTUBE_API_KEY=...
python3 .claude/skills/youtube-agent/yt_data.py top --channel @yourhandle
python3 .claude/skills/youtube-agent/yt_data.py search --query "home espresso" --days 90
python3 .claude/skills/youtube-agent/yt_data.py comments --video https://youtu.be/<id>
python3 .claude/skills/youtube-agent/yt_data.py title "My Title Idea"   # no key needed
```

Without a key, the skills work from links, pasted comments, or a CSV export (`top --csv`).
Claude drafts everything; you publish and post replies yourself.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Each script has `--help`. Some examples that use the sample data in `samples/`:

```bash
# 01 Organize a messy Downloads folder (preview first)
python -m automations.file_automation organize ~/Downloads --dry-run
python -m automations.file_automation backup ~/Documents --dest backups

# 02 Scrape links and check for broken ones
python -m automations.web_automation https://example.com --check

# 03 Clean + filter + convert
python -m automations.data_processing samples/sales.csv --query "revenue > 2000" --output big_sales.xlsx

# 04 Monitor every 60 seconds and warn when CPU is above 80%
python -m automations.system_monitor --interval 60 --cpu 80

# 05 Detect brute-force attempts / file tampering
python -m automations.security_checks logscan samples/auth.log --threshold 5
python -m automations.security_checks hash ./my_project            # make a baseline
python -m automations.security_checks hash ./my_project --verify   # check for changes later

# 06 Check hosts and ports
python -m automations.network_tools localhost --ports 22,80,443,8000-8010

# 07 Call an API
python -m automations.api_automation https://api.github.com/repos/python/cpython --fields name stargazers_count

# 08 Build a report
python -m automations.reporting samples/sales.csv --group-by Region --value Revenue --title "Sales by Region"
```

## Scheduling

To run a script automatically, schedule it with **cron** (Linux/macOS) or **Task Scheduler** (Windows):

```cron
# Back up Documents every day at 2am
0 2 * * * cd /path/to/repo && .venv/bin/python -m automations.file_automation backup ~/Documents
```

## Tests

```bash
pytest -q
```

## ⚠️ Responsible use

Only run the network and security tools against systems you own or have written permission to test.
