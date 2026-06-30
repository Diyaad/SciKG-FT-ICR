"""
merge_rawfile_metadata.py — one-time merge of manual filename metadata into the
FOXDEN JSON files for the 46 RAW files.

For each FOXDEN JSON in data/raw/rawfiles_metadata/, this script finds the
matching row in data/raw/rawfiles_metadata.csv (joined by the .raw filename) and
writes an ENRICHED copy to data/processed/rawfiles_enriched/. The enriched copy
has the manual CSV fields under a "filename_metadata" key placed FIRST, followed
by every original FOXDEN key in its original order. The data/raw/ inputs are
never modified — immutability is preserved per project policy (CLAUDE.md).

This is a one-time data prep step. After it runs, the enriched JSONs in
data/processed/rawfiles_enriched/ are the canonical source for
02c_extract_rawfiles.py. The manual CSV stays in place as a reference.

⚠️ Two similarly named INPUT paths — they are DIFFERENT, and both are read-only:
    data/raw/rawfiles_metadata.csv   the manual CSV (input, never modified)
    data/raw/rawfiles_metadata/      the folder of 46 FOXDEN JSONs (read only)
Output goes to a separate processed directory:
    data/processed/rawfiles_enriched/   the 46 enriched JSONs (written here)

Standard library only. No API calls. No package installs.

Run from the repository root:
    python scripts/merge_rawfile_metadata.py
"""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CSV_PATH = REPO / "data" / "raw" / "rawfiles_metadata.csv"
JSON_DIR = REPO / "data" / "raw" / "rawfiles_metadata"
OUTPUT_DIR = REPO / "data" / "processed" / "rawfiles_enriched"

MERGE_SOURCE = "data/raw/rawfiles_metadata.csv"

# Columns copied into filename_metadata, in this exact order. "filename" is the
# join key and is deliberately NOT copied — the JSON file's name encodes it.
META_FIELDS = [
    "operator_initials",
    "operator_name",
    "date_acquired",
    "sample_organism_strain",
    "sample_state",
    "sample_growth_medium",
    "sample_growth_date",
    "bioreplicate_id",
    "sample_prep_method",
    "fractionation_method",
    "fraction_id",
    "experimental_parameters",
    "run_number",
]

# Values that mean "no value" — normalized to null regardless of letter case.
NULL_TOKENS = {"", "n/a", "na", "none", "null"}


def clean(value):
    """Empty cells and N/A-style placeholders become None; else stripped str."""
    if value is None:
        return None
    text = value.strip()
    if text.lower() in NULL_TOKENS:
        return None
    return text


def detect_dialect(path):
    """Return a csv dialect, preferring Sniffer, falling back to tab-vs-comma."""
    with path.open(newline="", encoding="utf-8") as f:
        sample = f.readline()
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t")
    except csv.Error:
        delimiter = "\t" if sample.count("\t") > sample.count(",") else ","

        class _Fallback(csv.Dialect):
            pass

        _Fallback.delimiter = delimiter
        _Fallback.quotechar = '"'
        _Fallback.doublequote = True
        _Fallback.skipinitialspace = False
        _Fallback.lineterminator = "\r\n"
        _Fallback.quoting = csv.QUOTE_MINIMAL
        return _Fallback


def load_csv_rows(path):
    """Load the CSV keyed by the 'filename' column. Returns {filename: rowdict}."""
    dialect = detect_dialect(path)
    rows = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, dialect=dialect)
        for row in reader:
            filename = (row.get("filename") or "").strip()
            if not filename:
                continue
            rows[filename] = row
    return rows


def build_metadata_block(row, merged_at):
    """Construct the filename_metadata block from a CSV row."""
    block = {}
    for field in META_FIELDS:
        value = clean(row.get(field))
        if field == "run_number" and value is not None:
            try:
                value = int(value)
            except ValueError:
                # Non-integer run_number is a finding, not a crash. Keep the raw
                # string so nothing is silently dropped, and warn.
                print(f"WARNING non-integer run_number {value!r} kept as string")
        block[field] = value
    block["merged_at"] = merged_at
    block["merge_source"] = MERGE_SOURCE
    return block


def main():
    # --- Preconditions: both paths must exist and be the right kind ---------
    if not CSV_PATH.is_file():
        print(f"ERROR CSV file missing: {CSV_PATH}")
        return 1
    if not JSON_DIR.is_dir():
        print(f"ERROR rawfiles_metadata folder missing: {JSON_DIR}")
        return 1

    csv_rows = load_csv_rows(CSV_PATH)
    json_paths = sorted(JSON_DIR.glob("*.json"))

    # Output directory lives under data/processed/ — data/raw/ stays immutable.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    merged_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    enriched = 0
    skipped_no_match = 0
    errors = 0
    matched_raw_names = set()
    first_output_path = None

    # --- Main loop ----------------------------------------------------------
    for json_path in json_paths:
        raw_name = json_path.stem + ".raw"
        row = csv_rows.get(raw_name)
        if row is None:
            print(f"NO CSV MATCH {json_path.name}")
            skipped_no_match += 1
            continue

        try:
            with json_path.open(encoding="utf-8") as f:
                original = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"MALFORMED {json_path.name}: {exc}")
            errors += 1
            continue

        # filename_metadata FIRST, then every original FOXDEN key in its
        # original order. The source JSON on disk is never touched. If the
        # original somehow already carried a filename_metadata key, the fresh
        # block wins (idempotent re-runs reflect current CSV values).
        enriched_data = {"filename_metadata": build_metadata_block(row, merged_at)}
        for key, value in original.items():
            if key == "filename_metadata":
                continue
            enriched_data[key] = value

        output_path = OUTPUT_DIR / json_path.name
        try:
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(enriched_data, f, indent=2)
                f.write("\n")
        except OSError as exc:
            print(f"ERROR writing {output_path.name}: {exc}")
            errors += 1
            continue

        matched_raw_names.add(raw_name)
        enriched += 1
        if first_output_path is None:
            first_output_path = output_path

    # CSV rows that never matched any JSON on disk.
    unmatched_csv = sorted(set(csv_rows) - matched_raw_names)

    # --- Summary ------------------------------------------------------------
    print()
    print(f"CSV rows loaded:                {len(csv_rows)}")
    print(f"JSON files found:               {len(json_paths)}")
    print(f"JSON files enriched:            {enriched}")
    print(f"JSON files skipped (no match):  {skipped_no_match}")
    print(f"CSV rows unmatched:             {len(unmatched_csv)}")
    print(f"Errors:                         {errors}")

    expected = 46
    if len(csv_rows) != expected or len(json_paths) != expected or enriched != expected:
        print()
        print(f"NOTE counts differ from expected {expected}.")
        if unmatched_csv:
            print("  CSV rows with no matching JSON:")
            for name in unmatched_csv:
                print(f"    {name}")

    # --- Verification -------------------------------------------------------
    print()
    print("VERIFICATION")

    # 1. Count enriched output files carrying a filename_metadata block.
    have_block = 0
    for out_path in OUTPUT_DIR.glob("*.json"):
        try:
            with out_path.open(encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if "filename_metadata" in data:
            have_block += 1
    ok_count = have_block == enriched
    print(f"  output files with filename_metadata: {have_block} "
          f"(expected {enriched}) -> {'OK' if ok_count else 'MISMATCH'}")

    # 2. Sample output re-parses, has filename_metadata FIRST, and still
    #    carries an original FOXDEN field.
    ok_sample = False
    ok_first = False
    ok_preserved = False
    if first_output_path is not None:
        try:
            with first_output_path.open(encoding="utf-8") as f:
                sample = json.load(f)
            ok_sample = True
            keys = list(sample.keys())
            ok_first = bool(keys) and keys[0] == "filename_metadata"
            ok_preserved = any(k in sample for k in ("instrument", "filepath", "filename"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  sample re-parse failed: {exc}")
    name = first_output_path.name if first_output_path else "none"
    print(f"  sample JSON re-parses valid:         {'OK' if ok_sample else 'FAIL'} ({name})")
    print(f"  sample has filename_metadata first:  {'OK' if ok_first else 'FAIL'}")
    print(f"  sample retains FOXDEN field:         {'OK' if ok_preserved else 'FAIL'}")

    # 3. Confirm the immutable source dir was not given a filename_metadata
    #    block by this run (data/raw/ must stay untouched).
    raw_touched = 0
    for json_path in JSON_DIR.glob("*.json"):
        try:
            with json_path.open(encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if "filename_metadata" in data:
            raw_touched += 1
    print(f"  data/raw/ files left unmodified:     "
          f"{'OK' if raw_touched == 0 else f'FAIL ({raw_touched} touched)'}")

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
