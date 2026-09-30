import socket
from collections import Counter
from pathlib import Path

import pandas as pd

from automations import (data_processing, file_automation, network_tools, reporting,
                         security_checks, system_monitor, web_automation, api_automation)

SAMPLES = Path(__file__).parent.parent / "samples"


def test_organize_and_rename(tmp_path):
    for name in ["a.jpg", "b.pdf", "c.py", "d.xyz"]:
        (tmp_path / name).write_text("x")
    file_automation.organize(tmp_path)
    assert (tmp_path / "Images" / "a.jpg").exists()
    assert (tmp_path / "Documents" / "b.pdf").exists()
    assert (tmp_path / "Code" / "c.py").exists()
    assert (tmp_path / "Other" / "d.xyz").exists()

    docs = tmp_path / "Documents"
    (docs / "z.TXT").write_text("y")
    file_automation.bulk_rename(docs, "doc")
    assert sorted(p.name for p in docs.iterdir()) == ["doc_001.pdf", "doc_002.txt"]


def test_backup(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "f.txt").write_text("hi")
    archive = file_automation.backup(src, tmp_path / "out")
    assert archive.exists() and archive.suffix == ".zip"


def test_parse_page():
    html = '<title> Hi </title><a href="/x">x</a><a href="/x#top">dup</a><a href="mailto:a@b.c">m</a>'
    title, links = web_automation.parse_page(html, "https://example.com/page")
    assert title == "Hi"
    assert links == ["https://example.com/x"]


def test_data_processing():
    df = data_processing.clean(pd.read_csv(SAMPLES / "sales.csv"))
    assert "revenue" in df.columns
    assert len(df) == 7  # one duplicate row removed
    assert len(data_processing.filter_rows(df, "revenue > 2000")) == 3


def test_thresholds():
    stats = {"cpu_percent": 95.0, "ram_percent": 40.0}
    warnings = system_monitor.check_thresholds(stats, {"cpu_percent": 85, "ram_percent": 85})
    assert len(warnings) == 1 and "cpu_percent" in warnings[0]
    assert "cpu_percent" in system_monitor.snapshot()


def test_failed_logins():
    counts = security_checks.failed_logins((SAMPLES / "auth.log").read_text().splitlines())
    assert counts == Counter({"203.0.113.5": 5, "198.51.100.7": 1})
    assert security_checks.suspicious_ips(counts, 5) == [("203.0.113.5", 5)]


def test_integrity(tmp_path):
    (tmp_path / "a.txt").write_text("1")
    (tmp_path / "b.txt").write_text("2")
    base = security_checks.hash_tree(tmp_path)
    (tmp_path / "a.txt").write_text("changed")
    (tmp_path / "b.txt").unlink()
    (tmp_path / "c.txt").write_text("3")
    assert security_checks.compare(base, security_checks.hash_tree(tmp_path)) == {
        "added": ["c.txt"], "removed": ["b.txt"], "modified": ["a.txt"]}


def test_network_local_port():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen()
    port = server.getsockname()[1]
    try:
        assert network_tools.scan_ports("127.0.0.1", [port]) == [port]
    finally:
        server.close()
    assert network_tools.parse_ports("22,80,8000-8002") == [22, 80, 8000, 8001, 8002]


def test_api_pick():
    assert api_automation.pick({"a": 1, "b": 2}, ["a"]) == {"a": 1}
    assert api_automation.pick([{"a": 1, "b": 2}], ["b"]) == [{"b": 2}]


def test_reporting(tmp_path):
    df = pd.read_csv(SAMPLES / "sales.csv")
    summary = reporting.build_summary(df, "Region", "Revenue")
    assert summary.iloc[0]["Region"] == "South"
    reporting.to_excel(df, summary, tmp_path / "r.xlsx")
    reporting.to_html(summary, "Test", tmp_path / "r.html")
    assert (tmp_path / "r.xlsx").exists()
    assert "<table" in (tmp_path / "r.html").read_text()
