"""
Tests for scripts/05_load.py

Verifies:
- loading the same data twice produces no duplicate nodes
- all provenance properties are set on every loaded node
- node counts match expected values from validation_report.json
- load is idempotent — safe to re-run
"""
