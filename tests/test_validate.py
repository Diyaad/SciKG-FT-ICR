"""
Tests for scripts/04_validate.py

Verifies:
- records missing a DOI fail validation
- records missing source_api or extracted_at fail validation
- failed records go to quarantine.jsonl not silently dropped
- validation_report.json is always produced
"""
