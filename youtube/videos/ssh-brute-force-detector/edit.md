# Edit plan

## Pacing
- Hook: no intro, no logo. First frame = red ALERT lines. Cut on every sentence.
- Visual change every ~20-30s: zoom into code, terminal ↔ face cam, highlight
  boxes on log lines, line counter overlay in Beat 2.
- Beat 3 reveal: hold 1-2 seconds of silence after the number. Don't rush it.
- Cut all "um", re-takes and typing pauses. Speed up typing 4-8x and installs to 10x.

## Must-blur list
- Your server's public IP (dashboard, terminal prompt, `ssh` commands)
- Real attacker IPs: blur the last two octets (show `185.x.x.x` style)
- Any real usernames on your own accounts, and SSH key fingerprints

## Graphics / on-screen text
- Log line anatomy (Beat 1): three coloured boxes: FAILED / USERNAME / IP
- "< 20 lines" counter (Beat 2)
- Big number card for the 24h total (Beat 3). Reuse it for thumbnail B.
- Checklist overlay for the 3 lock-down steps (Beat 4), ticking off
- Burned-in captions on the Shorts (many people watch muted)

## Music / SFX
- Low ambient tension under hook and reveal; drop the music out for the number.
- Soft "tick" SFX on each checklist item.

## Shorts (9:16)
| # | in | out | on-screen hook text |
|---|---|---|---|
| 1 | 0:00 | 0:20, then 5:00-5:30 | "I left a server online for 24h…" |
| 2 | Beat 3 usernames | ~+40s | "The passwords hackers try first" |
Timestamps are from the script. Replace them with the real ones after the edit.

## ffmpeg (if you share footage in the project; originals never overwritten)
```bash
# trim a clip
ffmpeg -ss 00:05:00 -to 00:05:30 -i raw/main.mp4 -c copy out/clip-reveal.mp4
# vertical 9:16 centre crop for Shorts
ffmpeg -i out/clip-reveal.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920" -c:a copy out/short-1.mp4
# burn captions from an .srt
ffmpeg -i out/short-1.mp4 -vf subtitles=out/short-1.srt -c:a copy out/short-1-captioned.mp4
```
