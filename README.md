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
