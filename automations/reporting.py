"""08 Reporting: turn a CSV into Excel and HTML summary reports.

The HTML report can be printed to PDF from any browser.
"""
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd


def build_summary(df: pd.DataFrame, group_by: str, value: str) -> pd.DataFrame:
    summary = (
        df.groupby(group_by)[value]
        .agg(total="sum", average="mean", count="count")
        .sort_values("total", ascending=False)
        .reset_index()
    )
    summary["average"] = summary["average"].round(2)
    return summary


def to_excel(df: pd.DataFrame, summary: pd.DataFrame, output: Path) -> None:
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        df.to_excel(writer, sheet_name="Raw Data", index=False)


def to_html(summary: pd.DataFrame, title: str, output: Path) -> None:
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    output.write_text(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #222; }}
table {{ border-collapse: collapse; }}
th, td {{ border: 1px solid #ccc; padding: .4rem .8rem; text-align: right; }}
th {{ background: #f2f2f2; }}
</style></head><body>
<h1>{title}</h1><p>Generated {generated}</p>
{summary.to_html(index=False)}
</body></html>
""")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="CSV file")
    parser.add_argument("--group-by", required=True, help="column to group by")
    parser.add_argument("--value", required=True, help="numeric column to total")
    parser.add_argument("--out-dir", type=Path, default=Path("reports"))
    parser.add_argument("--title", default="Automated Report")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    summary = build_summary(df, args.group_by, args.value)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    xlsx = args.out_dir / f"report_{stamp}.xlsx"
    html = args.out_dir / f"report_{stamp}.html"
    to_excel(df, summary, xlsx)
    to_html(summary, args.title, html)
    print(summary.to_string(index=False))
    print(f"\nSaved {xlsx} and {html}")


if __name__ == "__main__":
    main()
