"""
fetch_crossref_orcid.py — cache CrossRef author/ORCID metadata for graph DOIs.

READ-ONLY with respect to the graph: this script queries Neo4j only to
enumerate Publication DOIs, then fetches https://api.crossref.org/works/{doi}
for each and caches the raw JSON response to disk. It writes nothing to Neo4j
and nothing under data/raw/.

ORCIDs are read from CrossRef's STRUCTURED author array (author[].ORCID and
author[].authenticated-orcid) — this is a deterministic lookup, not an
extraction. If CrossRef returns no ORCID for an author, the value is null; no
ORCID is ever inferred, and no name-based lookup against the ORCID registry is
performed.

Politeness (CrossRef polite pool):
  - User-Agent carries a mailto so CrossRef can contact us
  - one request per REQUEST_INTERVAL seconds, single-threaded
  - responses cached to CACHE_DIR so re-runs never re-query

Usage:
    python3 scripts/fetch_crossref_orcid.py            # fetch missing only
    python3 scripts/fetch_crossref_orcid.py --refresh  # ignore cache
"""

import json
import os
import sys
import time
import urllib.parse

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(REPO, "data", "processed", "cache", "crossref")
LOG_PATH = os.path.join(REPO, "data", "processed", "logs", "crossref_orcid_fetch_log.jsonl")

# CrossRef polite pool: identify ourselves and give a contact address.
MAILTO = "davidsbutcher@protonmail.com"
USER_AGENT = (
    "SciKG/0.1 (https://github.com/nhmfl/scikg; provenance-aware scientific "
    f"knowledge graph; mailto:{MAILTO})"
)
REQUEST_INTERVAL = 1.0  # seconds between requests
TIMEOUT = 30
MAX_RETRIES = 3


def doi_safe(doi):
    """Filesystem-safe cache key for a DOI (same convention as data/raw/publications)."""
    return urllib.parse.quote(doi, safe="")


def graph_dois():
    """Return [(identifier, doi, publication_year)] for every Publication with a DOI."""
    driver = db.connect()
    try:
        rows = db.run_query(
            driver,
            """
            MATCH (p:Publication)
            WHERE p.doi IS NOT NULL
            RETURN p.identifier AS identifier, p.doi AS doi,
                   p.publication_year AS year
            ORDER BY p.identifier
            """,
        )
    finally:
        db.close(driver)
    return rows


def fetch_one(session, doi):
    """GET one CrossRef work record. Returns (status, payload_or_None)."""
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/")
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=TIMEOUT)
        except requests.RequestException as exc:
            if attempt == MAX_RETRIES:
                return ("error", {"error": str(exc)})
            time.sleep(2 ** attempt)
            continue

        if resp.status_code == 200:
            try:
                return ("ok", resp.json())
            except ValueError as exc:
                return ("error", {"error": "bad json: %s" % exc})
        if resp.status_code == 404:
            return ("not_found", None)
        if resp.status_code in (429, 500, 502, 503, 504):
            if attempt == MAX_RETRIES:
                return ("error", {"error": "http %d" % resp.status_code})
            # Respect Retry-After when CrossRef sends it.
            wait = resp.headers.get("Retry-After")
            time.sleep(float(wait) if wait and wait.isdigit() else 2 ** attempt)
            continue
        return ("error", {"error": "http %d" % resp.status_code})
    return ("error", {"error": "retries exhausted"})


def main():
    refresh = "--refresh" in sys.argv
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    pubs = graph_dois()
    print("Publications with a DOI in the graph: %d" % len(pubs), flush=True)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    counts = {"cached": 0, "ok": 0, "not_found": 0, "error": 0}
    log = open(LOG_PATH, "a", encoding="utf-8")
    try:
        for i, row in enumerate(pubs, 1):
            doi = row["doi"].strip()
            path = os.path.join(CACHE_DIR, doi_safe(doi) + ".json")

            if os.path.exists(path) and not refresh:
                counts["cached"] += 1
                continue

            status, payload = fetch_one(session, doi)
            counts[status if status in counts else "error"] += 1

            record = {
                "identifier": row["identifier"],
                "doi": doi,
                "status": status,
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            }
            if status == "ok":
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh)
            else:
                # Cache negative results too, so re-runs don't re-query them.
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump({"_scikg_status": status, "_scikg_detail": payload}, fh)
                record["detail"] = payload

            log.write(json.dumps(record) + "\n")
            log.flush()

            if i % 25 == 0:
                print("  %d/%d  %s" % (i, len(pubs), counts), flush=True)
            time.sleep(REQUEST_INTERVAL)
    finally:
        log.close()

    print("done: %s" % counts, flush=True)


if __name__ == "__main__":
    main()
