---
name: youtube-create
description: >-
  Module 2 of the YouTube agent: CREATE. Turns one video idea into a ready-to-film
  package in the creator's voice: a script that opens with one of 21 hook
  formulas, 5 title options, 3 thumbnail concepts (with an optional image
  prompt), a description with chapters, and an edit plan (cut list, b-roll,
  on-screen text, Shorts moments, and ffmpeg commands if footage is shared). Use
  when the user says "write a script", "hook for my video", "title ideas",
  "thumbnail ideas", "description", "edit my video", "make this video", or via
  /youtube-agent.
argument-hint: "<the video idea or working title> [--short]"
---

# youtube-create

**One job: make the video.** Reads `youtube/channel.md`, `youtube/voice.md`
(required) and `youtube/viral-hooks.md` (falls back to `viral-hooks.md` in this
folder). If the virality module ran for this idea, read its breakdown in
`youtube/research/` and reuse the winning structure.

Output folder: `youtube/videos/<slug>/` (slug = short kebab-case of the idea).
Save the idea as `idea.md` first: the idea, the viewer, the promise, the source.

Title tool (shared with the agent):

```bash
python3 "${CLAUDE_SKILL_DIR}/../youtube-agent/yt_data.py" title "Title one" "Title two"
```

## Order matters: package first

On YouTube the title and thumbnail decide if anyone sees the script. So:

### 1. Titles → `titles.md`
Five options, each a different angle (result, mistake, question, contrast,
story). 40-60 characters, front-load the payoff, no clickbait the video doesn't
pay off. Run them through the title tool and fix what it flags. Mark one pick
and say why.

### 2. Thumbnail → `thumbnail.md`
Three concepts that **complement** the pick title (don't repeat its words).
For each: the single focal point, face/emotion (if the creator shows face),
max 3-4 words of text, background, contrast colour, and what the viewer should
feel in 1 second. Add a text prompt for an image generator if the user wants
mock-ups, and a shot list if they'll shoot it. Mark the recommended title +
thumbnail pair.

### 3. Script → `script.md`
- **Hook (0-30s)**: pick the best-fitting formula from `viral-hooks.md`, write
  2-3 hook variants with it, choose one. The hook must confirm the title and
  thumbnail's promise in the first 5 seconds.
- **Structure**: setup → stakes → 3-5 beats (each ends with an open loop into
  the next) → payoff → one call to action that fits the video (next video, not
  "smash the bell"). Re-hook roughly every 60-90 seconds.
- Write it the way the creator talks (`voice.md`): their words, their sentence
  length, read-aloud test. Mark `[B-ROLL: ...]`, `[ON-SCREEN: ...]`,
  `[CUT]` cues inline. Give an estimated length (~150 spoken words/minute).
- `--short`: under 60 seconds, hook in the first 1-2 seconds, one idea, loopable
  ending, on-screen text for silent viewing.

### 4. Description → `description.md`
First two lines carry the search keywords and the promise (they show before
"more"). Then chapters (00:00 Intro ...) from the script beats, links the
creator provides (never invent links), and 3-5 hashtags max. Pinned comment
draft at the bottom for `/youtube-engage`.

### 5. Edit → `edit.md`
Claude can't operate an editor, but it can plan the edit and, with footage
files in the project, run the mechanical parts:
- Cut list against the script: what to keep, cut, tighten; pacing notes;
  pattern interrupts every ~20-40s (zoom, b-roll, text, sound).
- B-roll and graphics list, music/SFX cues, captions note.
- 2-3 Shorts moments with in/out points once timestamps exist.
- If the user shares footage and `ffmpeg` is installed, generate and (with their
  go-ahead) run commands for trims, joins, vertical 9:16 crops for Shorts, and
  burned-in captions from an `.srt`. Never overwrite the original files.

## Rules

- Never copy another creator's script, title, or thumbnail. Borrow the formula.
- The video must deliver what the title and thumbnail promise, in the first 30s.
- No made-up facts or stats inside scripts. Mark anything to verify `[CHECK]`.
