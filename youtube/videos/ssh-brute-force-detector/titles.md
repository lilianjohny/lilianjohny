# Titles

Each was checked with `yt_data.py title`. Five angles:

| # | Angle | Title | chars |
|---|---|---|---|
| 1 | result / story | **I Caught Hackers Guessing Passwords With 20 Lines of Python** | 59 |
| 2 | warning | Your Server Is Being Attacked Right Now. Here's Proof. | 54 |
| 3 | question | Who's Trying to Log Into Your Server? Find Out in 5 Minutes | 59 |
| 4 | mistake | Stop Ignoring Your Auth Log | 27 |
| 5 | tutorial / search | Build a Brute-Force Detector in Python (Beginner Project) | 57 |

## Pick: #1
It has a story ("I caught"), a villain ("hackers"), and a low-effort promise
("20 lines"), and it fits the thumbnail without repeating it. "20 lines" is true:
the detection logic (regex + counter + threshold) is under 20 lines in
`automations/security_checks.py`. Show it on screen so the claim is checkable.

**Backup for search traffic:** #5. If #1 underperforms on click-through after
48-72h, swap to #5 (Studio > Content > title). Don't change the thumbnail at
the same time, or you won't know which change worked.
