# Idea: catch brute-force login attempts on your own server with Python

- **The idea:** Spin up a cheap cloud server, leave SSH open for a day, then run a
  short Python script on its auth log to see who tried to break in, how often, and
  with which usernames. Then lock it down.
- **The viewer:** someone getting into cybersecurity/IT who knows basic Python.
- **The promise:** in ~10 minutes you'll have a working intrusion-detection script
  and a portfolio project, and you'll see real attack traffic with your own eyes.
- **Source:** pillar 1 "Defend your own stuff". The code already exists:
  `automations/security_checks.py logscan` (tested in `tests/`).
- **Virality check:** skipped. `YOUTUBE_API_KEY` is not set and no reference
  links were given, so there's no outlier data yet. The angle "I left X exposed,
  here's what happened" is a known format (hook formula #5 *challenge* plus
  #2 *result first*), but how this channel's version performs is unknown until it's live.

## Film requirements
- A server **you own**: any $4-6/month cloud VPS with SSH open on port 22.
  Leave it 24h before filming the reveal. [CHECK] Use the real numbers from
  your own log on screen. Don't reuse numbers from anyone else.
- Blur your server's public IP and any real usernames in the edit.
- The repo's `samples/auth.log` (7 lines) is for the walkthrough of how the
  code works. The reveal must be your real log.
