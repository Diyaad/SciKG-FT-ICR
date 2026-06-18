"""
01_fetch.py — SciKG pipeline stage 1 (fetch)

Reads data/raw/doi_list.csv, fetches raw metadata for each DOI from CrossRef
(then OpenAlex as a fallback), saves the raw API responses as JSON to
data/raw/publications/, and updates data/raw/manifest.json after each
successful fetch.

This script ONLY fetches and saves raw API responses. It does not parse,
extract, or interpret the content. Files already present in
data/raw/publications/ are never overwritten — data/raw/ is immutable.
"""

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

DOI_LIST = Path("data/raw/doi_list.csv")
PUBLICATIONS_DIR = Path("data/raw/publications")
MANIFEST = Path("data/raw/manifest.json")

CROSSREF_HEADERS = {"User-Agent": "SciKG/0.1 (mailto:scikg@research.org)"}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def make_doi_safe(doi):
    return doi.replace("/", "_").replace(".", "_")


def read_dois(path):
    dois = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dois.append(row["doi"])
    return dois


def update_manifest(doi, doi_safe, source_api):
    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)

    manifest["papers"][doi] = {
        "doi": doi,
        "fetched_at": now_iso(),
        "source_api": source_api,
        "raw_file": f"data/raw/publications/{doi_safe}.json",
        "stages_complete": ["fetch"],
    }

    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def fetch_crossref(doi):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url, headers=CROSSREF_HEADERS)
    time.sleep(1)
    if response.status_code == 200:
        return response.json()
    return None


def fetch_openalex(doi):
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    response = requests.get(url)
    time.sleep(1)
    if response.status_code == 200:
        return response.json()
    return None


def main():
    dois = read_dois(DOI_LIST)

    fetched = 0
    skipped = 0
    failed = 0

    for doi in dois:
        doi_safe = make_doi_safe(doi)
        target = PUBLICATIONS_DIR / f"{doi_safe}.json"

        if target.exists():
            print(f"SKIP   {doi} (already fetched)")
            skipped += 1
            continue

        # Try CrossRef first.
        data = None
        source_api = None
        try:
            data = fetch_crossref(doi)
            if data is not None:
                source_api = "crossref"
        except requests.RequestException:
            data = None

        # Fall back to OpenAlex.
        if data is None:
            try:
                data = fetch_openalex(doi)
                if data is not None:
                    source_api = "openalex"
            except requests.RequestException:
                data = None

        if data is not None:
            save_json(target, data)
            update_manifest(doi, doi_safe, source_api)
            print(f"FETCH  {doi} from {source_api}")
            fetched += 1
        else:
            failure_path = PUBLICATIONS_DIR / f"{doi_safe}_FAILED.json"
            save_json(
                failure_path,
                {
                    "doi": doi,
                    "error": "both APIs failed",
                    "attempted_at": now_iso(),
                },
            )
            print(f"FAILED {doi} — both APIs returned errors")
            failed += 1

    print(f"Done — {fetched} fetched, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
