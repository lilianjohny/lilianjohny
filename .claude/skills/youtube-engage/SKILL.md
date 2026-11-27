---
name: youtube-engage
description: >-
  Module 3 of the YouTube agent: ENGAGE. Reads a video's comments (via the
  YouTube Data API, or a paste/export), sorts them into questions, praise,
  criticism, video ideas, collab leads and spam, drafts replies in the
  creator's voice for the creator to post, writes the pinned comment, and lists
  who to engage with (top commenters, superfans, creators worth a collab). Use
  when the user says "read my comments", "reply to comments", "who should I
  engage with", "pinned comment", "community", or via /youtube-agent.
argument-hint: "<video link or id> [--limit 200]"
---

# youtube-engage

**One job: talk to the audience.** Reads `youtube/channel.md` and
`youtube/voice.md`. Writes to `youtube/engage/`.

## 1. Read comments

With `YOUTUBE_API_KEY` set:

```bash
python3 "${CLAUDE_SKILL_DIR}/../youtube-agent/yt_data.py" comments --video <url-or-id> --limit 200 --out youtube/engage/<video-id>.json
```

Without a key: ask the user to paste comments, or share a YouTube Studio
screenshot/export. Never invent comments.

## 2. Sort them

Write `youtube/engage/<video-id>-triage.md` with each comment in one bucket
(keep the comment's link):

| bucket | what to do |
| --- | --- |
| **Questions** | reply first; repeated questions → a video idea or a pinned answer |
| **Video ideas / requests** | add to the plan backlog with the commenter's words |
| **Praise** | short, specific thanks; heart it |
| **Criticism (fair)** | thank, acknowledge, say what you'll change |
| **Criticism (troll)** | don't reply; hide or ignore |
| **Collab / business** | flag to the creator; never reply on their behalf with commitments |
| **Spam / scams / impersonators** | list for the creator to remove and report |

Add a short **summary**: the top 3 themes, the most-liked comments, sentiment in
one line, and any recurring confusion in the video (a hint for the next edit).

## 3. Reply drafts → `youtube/engage/<video-id>-replies.md`

- Prioritise: questions → high-like comments → first-time commenters early in
  the video's life (the first hour after upload matters most).
- Each reply: the comment link, the comment, the draft. In the creator's voice
  (`voice.md` reply rules), 1-3 sentences, answers or asks a follow-up question
  to keep the thread going. No copy-paste replies; no generic "Thanks!!" walls.
- Never promise giveaways, deals, or anything the creator didn't approve.

**Posting:** the Data API key is read-only. The creator posts replies from
YouTube Studio > Comments (fastest: open each link). Posting through the API
needs the creator's own OAuth login (`youtube.force-ssl` scope); offer to write
a script for that only if they ask, and never handle their password.

## 4. Pinned comment

One comment to pin: a question that invites replies, or the resource/next
video viewers ask for. In voice.

## 5. Who to engage with → `youtube/engage/people.md`

- **Superfans**: names that comment often and positively across videos (merge
  with earlier pulls in `youtube/engage/`). Ideas: shout-out, heart, community
  post feature.
- **Creators in the comments**: commenters with their own channels in the niche;
  note channel links only if visible. Suggest collab or reply-to-their-video
  ideas.
- **Creators to engage with** (from `channel.md` and virality scans): leave
  genuinely useful comments on their new uploads, in the first hour. Draft 2-3.

## Rules

- No fake engagement: no bot comments, no sock-puppet replies, no buying likes.
- Don't share personal data of commenters outside the creator's own files.
