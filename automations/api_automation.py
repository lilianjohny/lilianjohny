"""07 API Automation: fetch JSON from a REST API with retries and save it.

Example (free, no key needed):
    python -m automations.api_automation https://api.github.com/repos/python/cpython --fields name stargazers_count
"""
import argparse
import json
import time
from pathlib import Path

import requests


def fetch_json(url: str, params: dict | None = None, token: str | None = None,
               retries: int = 3, backoff: float = 1.0):
    """GET a URL and return parsed JSON, retrying on network errors and 5xx/429."""
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code == 429 or resp.status_code >= 500:
                raise requests.HTTPError(f"HTTP {resp.status_code}", response=resp)
            resp.raise_for_status()
            return resp.json()
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
            status = getattr(exc.response, "status_code", None) if isinstance(exc, requests.HTTPError) else None
            retryable = status is None or status == 429 or status >= 500
            if not retryable or attempt == retries - 1:
                raise
            time.sleep(backoff * 2 ** attempt)


def pick(data, fields: list[str] | None):
    """Keep only selected top-level fields from a dict or list of dicts."""
    if not fields:
        return data
    if isinstance(data, list):
        return [{k: item.get(k) for k in fields} for item in data]
    return {k: data.get(k) for k in fields}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url")
    parser.add_argument("--fields", nargs="*", help="only keep these fields")
    parser.add_argument("--token", help="bearer token, if the API needs one")
    parser.add_argument("--output", type=Path, help="save JSON to this file")
    args = parser.parse_args()

    data = pick(fetch_json(args.url, token=args.token), args.fields)
    text = json.dumps(data, indent=2)
    if args.output:
        args.output.write_text(text)
        print(f"Saved to {args.output}")
    else:
        print(text)


if __name__ == "__main__":
    main()
