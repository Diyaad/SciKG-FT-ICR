"""
Tests for scripts/01_fetch.py

Verifies:
- fetch_paper(doi) returns a dict with required fields
- bad DOI raises a clear error not a silent failure
- raw JSON is saved to data/raw/publications/{doi_safe}.json
- manifest.json is updated after each successful fetch
- fetching the same DOI twice does not overwrite the existing file
"""
