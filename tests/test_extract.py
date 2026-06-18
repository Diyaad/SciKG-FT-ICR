"""
Tests for scripts/02_extract.py

Verifies:
- extract() returns all required fields
- missing fields are None not absent from the output dict
- every record has source_api and extracted_at populated
- no field is inferred when absent from the source JSON
"""
