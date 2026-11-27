import importlib.util
from pathlib import Path

import pytest

_PATH = Path(__file__).parent.parent / ".claude" / "skills" / "youtube-agent" / "yt_data.py"
_spec = importlib.util.spec_from_file_location("yt_data", _PATH)
yt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(yt)


@pytest.mark.parametrize("value", [
    "dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
    "https://youtu.be/dQw4w9WgXcQ?si=abc",
    "https://www.youtube.com/shorts/dQw4w9WgXcQ",
    "https://m.youtube.com/embed/dQw4w9WgXcQ",
])
def test_parse_video_id(value):
    assert yt.parse_video_id(value) == "dQw4w9WgXcQ"


def test_parse_video_id_rejects_garbage():
    with pytest.raises(ValueError):
        yt.parse_video_id("https://example.com/nothing")


@pytest.mark.parametrize("value,expected", [
    ("@mkbhd", ("handle", "mkbhd")),
    ("https://www.youtube.com/@mkbhd/videos", ("handle", "mkbhd")),
    ("UCBJycsmduvYEL83R_U4JriQ", ("id", "UCBJycsmduvYEL83R_U4JriQ")),
    ("youtube.com/channel/UCBJycsmduvYEL83R_U4JriQ", ("id", "UCBJycsmduvYEL83R_U4JriQ")),
])
def test_parse_channel_ref(value, expected):
    assert yt.parse_channel_ref(value) == expected


def test_iso_duration():
    assert yt.parse_iso_duration("PT1H2M3S") == 3723
    assert yt.parse_iso_duration("PT45S") == 45
    assert yt.parse_iso_duration("P1DT1M") == 86460
    assert yt.parse_iso_duration("") == 0


def test_outlier_scores_rank_by_median():
    vids = [{"title": t, "views": v} for t, v in [("a", 100), ("b", 1000), ("c", 200), ("d", 300)]]
    ranked = yt.add_outlier_scores(vids)
    assert ranked[0]["title"] == "b"
    assert ranked[0]["outlier"] == 4.0  # median of 100,200,300,1000 = 250
    assert ranked[-1]["outlier"] == 0.4


def test_lint_title():
    assert yt.lint_title("I Tried 5 Espresso Machines Under $300") == ["ok"]
    notes = " ".join(yt.lint_title("Vlog 12 THIS IS SO CRAZY!!! " + "x" * 50))
    assert "chars" in notes and "CAPS" in notes and "'!'" in notes and "episode" in notes


def test_top_from_csv(tmp_path, capsys):
    f = tmp_path / "v.csv"
    f.write_text("Title,Views,Published\nOne,\"1,000\",2026-01-01\nTwo,100,2026-01-02\nThree,200,\n")
    out = tmp_path / "top.md"
    yt.main(["top", "--csv", str(f), "--out", str(out)])
    text = out.read_text()
    assert text.index("One") < text.index("Three") < text.index("Two")
    assert "5.0x" in text and "1,000" in text


def test_missing_key_exits(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    with pytest.raises(SystemExit) as e:
        yt.main(["comments", "--video", "dQw4w9WgXcQ"])
    assert "YOUTUBE_API_KEY" in str(e.value)
