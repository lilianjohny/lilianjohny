#!/usr/bin/env python3
"""YouTube data helper for the youtube-* skills. Standard library only.

Live mode reads the YouTube Data API v3 with a key in YOUTUBE_API_KEY
(read-only, public data). Offline mode reads a CSV export instead, so every
command except `comments` and `search` works without a key.

    yt_data.py top      --channel @handle [--limit 50] [--out file.md]
    yt_data.py top      --csv videos.csv            # columns: title,views[,published,url]
    yt_data.py search   --query "home espresso" [--days 90] [--limit 25]
    yt_data.py comments --video <id or url> [--limit 100] [--out comments.json]
    yt_data.py title    "My Title Here" ["Another title" ...]

`top` and `search` rank videos by outlier score: views divided by the median
views of that channel's recent uploads (top) or views per subscriber (search).
An outlier score of 3 means the video did three times what the channel
normally does; that is the signal worth studying, not raw views.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://www.googleapis.com/youtube/v3/"


# ---------------------------------------------------------------- parsing

def parse_video_id(value: str) -> str:
    """Accept a bare id or any common YouTube URL and return the 11-char id."""
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    u = urllib.parse.urlparse(value)
    host = (u.hostname or "").lower()
    if host.endswith("youtu.be"):
        cand = u.path.lstrip("/").split("/")[0]
    elif "v" in urllib.parse.parse_qs(u.query):
        cand = urllib.parse.parse_qs(u.query)["v"][0]
    else:
        m = re.search(r"/(?:shorts|embed|live|v)/([A-Za-z0-9_-]{11})", u.path)
        cand = m.group(1) if m else ""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", cand):
        raise ValueError(f"not a YouTube video id or URL: {value!r}")
    return cand


def parse_channel_ref(value: str) -> tuple[str, str]:
    """Return ("id", UC...) or ("handle", name) from an id, @handle or URL."""
    value = value.strip()
    if re.fullmatch(r"UC[A-Za-z0-9_-]{22}", value):
        return "id", value
    if value.startswith("@"):
        return "handle", value[1:]
    u = urllib.parse.urlparse(value if "://" in value else "https://" + value)
    parts = [p for p in u.path.split("/") if p]
    if parts:
        if parts[0].startswith("@"):
            return "handle", parts[0][1:]
        if parts[0] == "channel" and len(parts) > 1:
            return "id", parts[1]
    if re.fullmatch(r"[A-Za-z0-9._-]{3,30}", value):
        return "handle", value
    raise ValueError(f"not a channel id, @handle or channel URL: {value!r}")


def parse_iso_duration(value: str) -> int:
    """PT1H2M3S -> seconds."""
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


# ---------------------------------------------------------------- scoring

def add_outlier_scores(videos: list[dict]) -> list[dict]:
    """Score each video against the median views of the list, best first."""
    views = [v["views"] for v in videos if v.get("views") is not None]
    median = statistics.median(views) if views else 0
    for v in videos:
        v["outlier"] = round(v["views"] / median, 2) if median else 0.0
    return sorted(videos, key=lambda v: v["outlier"], reverse=True)


def lint_title(title: str) -> list[str]:
    """Plain checks a strong YouTube title usually passes. Advice, not rules."""
    notes = []
    n = len(title)
    if n > 70:
        notes.append(f"{n} chars: likely cut off in search and on mobile (aim for 40-60)")
    elif n > 60:
        notes.append(f"{n} chars: may be cut off on mobile (aim for 40-60)")
    elif n < 20:
        notes.append(f"{n} chars: very short; is the promise clear?")
    words = re.findall(r"[A-Za-z]{2,}", title)
    caps = [w for w in words if w.isupper() and len(w) > 2]
    if words and len(caps) / len(words) > 0.3:
        notes.append("lots of ALL CAPS words: one for emphasis is enough")
    if title.count("!") > 1:
        notes.append("more than one '!'")
    if re.search(r"\b(episode|ep\.?|part|vlog)\s*#?\d+", title, re.I):
        notes.append("episode/part numbers mean nothing to a new viewer: lead with the payoff")
    if not re.search(r"\d|\b(how|why|what|who|i|you|your|never|stop|best|worst|vs)\b", title, re.I):
        notes.append("no number, question word, 'you/I' or contrast: check it creates curiosity")
    return notes or ["ok"]


# ---------------------------------------------------------------- API

def _key() -> str:
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not key:
        sys.exit("YOUTUBE_API_KEY is not set. Get a free key (YouTube Data API v3) at "
                 "console.cloud.google.com, or use --csv for offline mode.")
    return key


def api_get(endpoint: str, **params) -> dict:
    params["key"] = _key()
    url = API + endpoint + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "yt-data-skill/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:  # surface the API's own message
        body = e.read().decode("utf-8", "replace")
        try:
            msg = json.loads(body)["error"]["message"]
        except Exception:
            msg = body[:300]
        sys.exit(f"YouTube API error {e.code} on {endpoint}: {msg}")


def resolve_channel(ref: str) -> dict:
    kind, value = parse_channel_ref(ref)
    params = {"part": "snippet,statistics,contentDetails"}
    params["id" if kind == "id" else "forHandle"] = value
    items = api_get("channels", **params).get("items", [])
    if not items:
        sys.exit(f"channel not found: {ref}")
    return items[0]


def video_details(ids: list[str]) -> list[dict]:
    out = []
    for i in range(0, len(ids), 50):
        data = api_get("videos", part="snippet,statistics,contentDetails",
                       id=",".join(ids[i:i + 50]))
        for it in data.get("items", []):
            st = it.get("statistics", {})
            out.append({
                "id": it["id"],
                "title": it["snippet"]["title"],
                "channel": it["snippet"]["channelTitle"],
                "channel_id": it["snippet"]["channelId"],
                "published": it["snippet"]["publishedAt"][:10],
                "views": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0)),
                "seconds": parse_iso_duration(it["contentDetails"].get("duration", "")),
                "url": f"https://www.youtube.com/watch?v={it['id']}",
            })
    return out


def channel_uploads(channel: dict, limit: int) -> list[dict]:
    playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while len(ids) < limit:
        params = {"part": "contentDetails", "playlistId": playlist,
                  "maxResults": min(50, limit - len(ids))}
        if token:
            params["pageToken"] = token
        data = api_get("playlistItems", **params)
        ids += [it["contentDetails"]["videoId"] for it in data.get("items", [])]
        token = data.get("nextPageToken")
        if not token:
            break
    return video_details(ids)


# ---------------------------------------------------------------- output

def fmt_len(sec: int) -> str:
    return f"{sec // 60}:{sec % 60:02d}" if sec else ""


def to_markdown(videos: list[dict], heading: str, extra: str = "") -> str:
    lines = [f"# {heading}", ""]
    if extra:
        lines += [extra, ""]
    lines += ["| # | outlier | views | length | published | title |",
              "|---|---|---|---|---|---|"]
    for i, v in enumerate(videos, 1):
        title = v["title"].replace("|", "\\|")
        link = f"[{title}]({v['url']})" if v.get("url") else title
        lines.append(f"| {i} | {v['outlier']}x | {v['views']:,} | {fmt_len(v.get('seconds', 0))} "
                     f"| {v.get('published', '')} | {link} |")
    return "\n".join(lines) + "\n"


def emit(text: str, out: str | None) -> None:
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {out}")
    else:
        print(text)


def read_csv_videos(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    vids = []
    for r in rows:
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        if not r.get("title") or not r.get("views"):
            continue
        vids.append({"title": r["title"],
                     "views": int(float(r["views"].replace(",", ""))),
                     "published": r.get("published", ""),
                     "url": r.get("url", ""),
                     "seconds": 0})
    if not vids:
        sys.exit(f"{path}: need at least 'title' and 'views' columns with data")
    return vids


# ---------------------------------------------------------------- commands

def cmd_top(a) -> None:
    if a.csv:
        vids = add_outlier_scores(read_csv_videos(a.csv))
        head, extra = f"Top videos ({os.path.basename(a.csv)})", ""
    else:
        ch = resolve_channel(a.channel)
        vids = channel_uploads(ch, a.limit)
        if a.no_shorts:
            vids = [v for v in vids if v["seconds"] > 60]
        vids = add_outlier_scores(vids)
        st = ch.get("statistics", {})
        head = f"Top videos: {ch['snippet']['title']}"
        extra = (f"Subscribers: {int(st.get('subscriberCount', 0)):,} · "
                 f"last {len(vids)} uploads · outlier = views / median of these uploads")
    emit(json.dumps(vids, indent=2) if a.json else to_markdown(vids[:a.show], head, extra), a.out)


def cmd_search(a) -> None:
    after = (datetime.now(timezone.utc) - timedelta(days=a.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = api_get("search", part="snippet", q=a.query, type="video", order="viewCount",
                   publishedAfter=after, maxResults=min(a.limit, 50),
                   relevanceLanguage=a.lang)
    ids = [it["id"]["videoId"] for it in data.get("items", [])]
    vids = video_details(ids)
    ch_ids = sorted({v["channel_id"] for v in vids})
    subs = {}
    for i in range(0, len(ch_ids), 50):
        for it in api_get("channels", part="statistics", id=",".join(ch_ids[i:i + 50])).get("items", []):
            subs[it["id"]] = int(it["statistics"].get("subscriberCount", 0) or 0)
    for v in vids:
        s = subs.get(v["channel_id"], 0)
        v["subscribers"] = s
        v["outlier"] = round(v["views"] / s, 2) if s else 0.0
    vids.sort(key=lambda v: v["outlier"], reverse=True)
    if a.json:
        return emit(json.dumps(vids, indent=2), a.out)
    lines = [f"# Niche scan: \"{a.query}\" (last {a.days} days)", "",
             "Outlier = views / channel subscribers. >1 means it reached beyond the channel's audience.", "",
             "| # | outlier | views | subs | channel | title |", "|---|---|---|---|---|---|"]
    for i, v in enumerate(vids, 1):
        t = v["title"].replace("|", "\\|")
        lines.append(f"| {i} | {v['outlier']}x | {v['views']:,} | {v['subscribers']:,} "
                     f"| {v['channel']} | [{t}]({v['url']}) |")
    emit("\n".join(lines) + "\n", a.out)


def cmd_comments(a) -> None:
    vid = parse_video_id(a.video)
    out, token = [], None
    while len(out) < a.limit:
        params = {"part": "snippet", "videoId": vid, "order": a.order, "textFormat": "plainText",
                  "maxResults": min(100, a.limit - len(out))}
        if token:
            params["pageToken"] = token
        data = api_get("commentThreads", **params)
        for it in data.get("items", []):
            top = it["snippet"]["topLevelComment"]
            s = top["snippet"]
            out.append({"comment_id": top["id"], "author": s.get("authorDisplayName", ""),
                        "text": s.get("textDisplay", ""), "likes": s.get("likeCount", 0),
                        "replies": it["snippet"].get("totalReplyCount", 0),
                        "published": s.get("publishedAt", "")[:10],
                        "link": f"https://www.youtube.com/watch?v={vid}&lc={top['id']}"})
        token = data.get("nextPageToken")
        if not token:
            break
    emit(json.dumps({"video_id": vid, "count": len(out), "comments": out},
                    indent=2, ensure_ascii=False), a.out)


def cmd_title(a) -> None:
    for t in a.titles:
        print(f"- {t}")
        for n in lint_title(t):
            print(f"    · {n}")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("top", help="rank a channel's uploads by outlier score")
    g = t.add_mutually_exclusive_group(required=True)
    g.add_argument("--channel", help="@handle, UC... id or channel URL")
    g.add_argument("--csv", help="offline: CSV with title,views[,published,url]")
    t.add_argument("--limit", type=int, default=50, help="uploads to read (default 50)")
    t.add_argument("--show", type=int, default=15, help="rows to print (default 15)")
    t.add_argument("--no-shorts", action="store_true", help="drop videos of 60s or less")
    t.add_argument("--json", action="store_true")
    t.add_argument("--out")
    t.set_defaults(fn=cmd_top)

    s = sub.add_parser("search", help="find breakout videos in a niche (costs 100+ quota units)")
    s.add_argument("--query", required=True)
    s.add_argument("--days", type=int, default=90)
    s.add_argument("--limit", type=int, default=25)
    s.add_argument("--lang", default="en")
    s.add_argument("--json", action="store_true")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_search)

    c = sub.add_parser("comments", help="download top-level comments of a video")
    c.add_argument("--video", required=True)
    c.add_argument("--limit", type=int, default=100)
    c.add_argument("--order", choices=["relevance", "time"], default="relevance")
    c.add_argument("--out")
    c.set_defaults(fn=cmd_comments)

    ti = sub.add_parser("title", help="lint one or more titles")
    ti.add_argument("titles", nargs="+")
    ti.set_defaults(fn=cmd_title)

    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
