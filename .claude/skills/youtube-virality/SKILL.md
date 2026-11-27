---
name: youtube-virality
description: >-
  Module 4 of the YouTube agent: VIRALITY. Scans the top videos in the niche and
  on any channel, ranks them by outlier score (views vs that channel's normal),
  breaks down why the winners worked (title, thumbnail, hook, structure,
  length), and reworks the pattern into new ideas in the creator's own voice.
  Use when the user says "what's going viral", "scan top videos", "why did this
  video blow up", "outliers", "steal like an artist", "viral ideas", or via
  /youtube-agent.
argument-hint: "<niche keywords, @channel, or video links>"
---

# youtube-virality

**One job: find what already won and make it ours.** Reads
`youtube/channel.md` and `youtube/voice.md`. Writes to `youtube/research/`.

Tool:

```bash
T="${CLAUDE_SKILL_DIR}/../youtube-agent/yt_data.py"
python3 "$T" top --channel @someone --no-shorts --out youtube/research/someone-top.md   # one channel
python3 "$T" search --query "<niche keywords>" --days 90 --out youtube/research/scan-<topic>.md
python3 "$T" top --csv export.csv                                                       # offline
```

`top` needs `YOUTUBE_API_KEY` (free, ~1-5 quota units per call); `search` costs
100+ units of the 10,000/day default quota, so run it a few times, not dozens.
Without a key: ask for video links or a YouTube Studio/analytics CSV export
(`title,views` columns at least), or, if web search is available, search for
recent popular videos in the niche and say the numbers are approximate.

## 1. Scan top videos

Run, in this order: the creator's own channel (what already works for *them*),
2-3 creators from `channel.md`, and one niche `search`. **Outlier score**, not
views, is the signal: a 5x video on a 10k channel teaches more than a 1x video on
a 5M channel.

## 2. Break down the winners

For the top 5-10 outliers (>= 2x), write `youtube/research/breakdown-<topic>.md`:

| video | outlier | **title** pattern | **thumbnail** (if seen) | **hook** formula # | **structure** | length |

- **Titles**: the angle (mistake / result / versus / question...), word count,
  the curiosity gap.
- **Hooks**: map each to a formula in `viral-hooks.md` (if the user can share a
  transcript or you can read captions; otherwise mark "not checked").
- **Structure**: the beats, where the payoff lands, re-hooks.
- **Pattern**: 3-5 bullet "what these winners have in common".

Only describe what you actually saw. If you couldn't watch or read a
transcript, say the hook/structure is unverified.

## 3. Rework in your voice

Turn each pattern into 3-5 new ideas for *this* channel: a different
angle/story/experience the creator can genuinely deliver, a title in their
voice, a thumbnail idea, and the hook formula. Pass the best ones to
`/youtube-plan` (backlog) or `/youtube-create` (make it now).

## Rules

- Borrow structure, never content: no reused scripts, thumbnails, footage, or
  near-identical titles.
- Numbers come from the tool or the user's data, with the date pulled. Views
  change daily.
