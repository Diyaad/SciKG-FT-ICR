"""
02_extract.py — SciKG pipeline stage 2 (extract)

Reads every .json file in data/raw/publications/ that does not end in
_FAILED.json, extracts structured fields from the CrossRef response, and
writes one JSONL record per paper to
data/processed/entities/publications.jsonl

This stage only extracts fields that are explicitly present in the source
response. Missing or empty fields are written as None — never inferred,
filled in, or guessed.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

PUBLICATIONS_DIR = Path("data/raw/publications")
MANIFEST = Path("data/raw/manifest.json")
OUTPUT = Path("data/processed/entities/publications.jsonl")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest):
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def clean_affiliation(name):
    for ch in ("\r", "\n", "\t"):
        name = name.replace(ch, " ")
    return name.strip()


def extract_authors(message):
    authors = []
    for author in message.get("author", []):
        affiliations = []
        for aff in author.get("affiliation", []):
            name = aff.get("name", None)
            if name is not None:
                affiliations.append(clean_affiliation(name))
        authors.append(
            {
                "given": author.get("given", None),
                "family": author.get("family", None),
                "orcid": author.get("ORCID", None),
                "sequence": author.get("sequence", None),
                "affiliations": affiliations,
            }
        )
    return authors


def extract_year(message):
    for key in ("published", "issued"):
        block = message.get(key)
        if block:
            date_parts = block.get("date-parts")
            if date_parts and date_parts[0]:
                return date_parts[0][0]
    return None


def extract_funders(message):
    funders = []
    for funder in message.get("funder", []):
        funders.append(
            {
                "name": funder.get("name", None),
                "doi": funder.get("DOI", None),
                "awards": funder.get("award", []),
            }
        )
    return funders


def extract_referenced_dois(message):
    dois = []
    for ref in message.get("reference", []):
        doi = ref.get("DOI", None)
        if doi is not None:
            dois.append(doi)
    return dois


def first_or_none(value):
    if value:
        return value[0]
    return None


def extract_record(message, source_api):
    return {
        "doi": message.get("DOI", "").lower() or None,
        "title": first_or_none(message.get("title", [])),
        "year": extract_year(message),
        "authors": extract_authors(message),
        "journal": first_or_none(message.get("container-title", [])),
        "publisher": message.get("publisher", None),
        "volume": message.get("volume", None),
        "issue": message.get("issue", None),
        "funders": extract_funders(message),
        "referenced_dois": extract_referenced_dois(message),
        "cited_by_count": message.get("is-referenced-by-count", None),
        "abstract": message.get("abstract", None),
        "source_api": source_api,
        "extracted_at": now_iso(),
        "evidence_note": (
            "Extracted from CrossRef API response via scripts/02_extract.py"
        ),
    }


def main():
    manifest = load_manifest()
    manifest_lower = {
        k.lower(): k for k in manifest["papers"]
    }

    extracted = 0
    skipped = 0
    errors = 0

    files = sorted(
        p
        for p in PUBLICATIONS_DIR.glob("*.json")
        if not p.name.endswith("_FAILED.json")
    )

    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            print(f"ERROR   {path.name} — could not parse JSON")
            errors += 1
            continue

        message = data.get("message", {})
        doi = message.get("DOI", None)

        original_key = manifest_lower.get(
            doi.lower() if doi else "", None
        )
        paper_entry = (
            manifest["papers"][original_key]
            if original_key else {}
        )
        stages_complete = paper_entry.get("stages_complete", [])

        if "extract" in stages_complete:
            print(f"SKIP    {doi} (already extracted)")
            skipped += 1
            continue

        source_api = paper_entry.get("source_api", None)
        record = extract_record(message, source_api)

        with open(OUTPUT, "a", encoding="utf-8") as out:
            out.write(json.dumps(record) + "\n")

        if original_key:
            if "extract" not in manifest["papers"][
                    original_key]["stages_complete"]:
                manifest["papers"][original_key][
                    "stages_complete"].append("extract")
            save_manifest(manifest)

        print(f"EXTRACT {doi}")
        extracted += 1

    print(f"Done — {extracted} extracted, {skipped} skipped, {errors} errors")


if __name__ == "__main__":
    main()
