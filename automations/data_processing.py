"""03 Data Processing: clean, filter, convert and summarize a CSV with pandas."""
import argparse
from pathlib import Path

import pandas as pd


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names, trim text, drop empty rows and duplicates."""
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].str.strip()
    df = df.dropna(how="all").drop_duplicates()
    return df.reset_index(drop=True)


def filter_rows(df: pd.DataFrame, query: str | None) -> pd.DataFrame:
    """Filter with a pandas query string, e.g. "age > 30 and city == 'Paris'"."""
    return df.query(query).reset_index(drop=True) if query else df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    return df.describe(include="all").transpose()


def convert(df: pd.DataFrame, output: Path) -> None:
    ext = output.suffix.lower()
    if ext == ".csv":
        df.to_csv(output, index=False)
    elif ext == ".json":
        df.to_json(output, orient="records", indent=2)
    elif ext in (".xlsx", ".xls"):
        df.to_excel(output, index=False)
    else:
        raise ValueError(f"Unsupported output format: {ext}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="CSV file to process")
    parser.add_argument("--query", help="pandas filter, e.g. \"price > 100\"")
    parser.add_argument("--output", type=Path, help="save result as .csv, .json or .xlsx")
    args = parser.parse_args()

    raw = pd.read_csv(args.input)
    df = filter_rows(clean(raw), args.query)
    print(f"Rows: {len(raw)} raw -> {len(df)} after cleaning/filtering\n")
    print(summarize(df).to_string())
    if args.output:
        convert(df, args.output)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
