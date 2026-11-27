---
name: youtube-plan
description: >-
  Module 1 of the YouTube agent: PLAN. Decides what to post (ranked ideas from
  the channel's pillars, what already worked, and audience questions), when to
  post (days and times from the creator's capacity and their audience data), and
  writes the whole-week plan with long videos, Shorts cut from them, and the
  production deadlines for each. Use when the user says "what should I post",
  "when should I post", "plan my week", "content calendar", "weekly plan",
  "video ideas", or via /youtube-agent.
argument-hint: "[week, e.g. 'next week' or 2026-W49]"
---

# youtube-plan

**One job: decide what goes out, and when.** Reads `youtube/channel.md`,
`youtube/voice.md`, and anything in `youtube/research/` and `youtube/engage/`.
If `channel.md` is missing, run `/youtube-agent setup` first.

## 1. What to post

Build a candidate list of 8-12 ideas from these sources, and tag each with where
it came from (no source, no idea):

- **Proven**: outliers from `youtube/research/` (own channel or niche scans,
  outlier >= 2x). Same angle, new take.
- **Asked**: questions and requests in comments (`youtube/engage/*.json`).
- **Pillar gaps**: a content pillar in `channel.md` that hasn't had a video in
  the last 4 uploads.
- **Timely**: dated hooks the user mentions (launches, seasons, events). Do not
  invent trends; if you can search the web, cite what you found.

Score each 1-5 on: **demand** (evidence people want it), **fit** (pillar +
audience), **packaging** (can you see a clickable title + thumbnail right now?),
**effort** (5 = easy to make with their capacity). Keep the top ones that fit
capacity. For every pick, write the working title and the one-line thumbnail
idea: if you can't package it, it doesn't make the plan.

## 2. When to post

- Publish days come from `channel.md` capacity. Never plan more than they said
  they can make.
- Time of day: use the creator's YouTube Studio data ("When your viewers are on
  YouTube") if they share it; publish 1-2 hours before their peak. If no data,
  say it's a starting default (e.g. weekday early afternoon in the audience's
  timezone) to be replaced with real data after 4-6 uploads.
- Consistency beats volume: same days each week. Space long videos at least two
  days apart; Shorts can fill the gaps.

## 3. The whole-week plan

Write `youtube/plans/<YYYY>-W<ww>.md`:

```markdown
# Week <ww> plan (<Mon date> – <Sun date>)

| day | publish (tz) | format | working title | thumbnail idea | source | status |
| --- | --- | --- | --- | --- | --- | --- |

## Production schedule
| video | script by | film by | edit by | thumbnail by | publish |

## Shorts
- 2-3 Shorts cut from each long video: the moment, start/end timestamps once
  the edit exists, and the on-screen hook text.

## Community & engagement
- Community post / poll idea, and when.
- Comment-reply blocks: first hour after each upload (see /youtube-engage).

## Backlog (ideas that didn't make it, with scores)
```

Then hand each planned video to `/youtube-create` if the user wants the scripts
now.

## Rules

- Never show made-up search volumes or "this will get X views". Show the
  evidence you used, or say it's a hunch.
- Respect capacity. A plan the creator can't finish is worse than a smaller one.
- Re-plan from data: if last week's numbers are shared, note what over/under
  performed vs the channel median and adjust.
