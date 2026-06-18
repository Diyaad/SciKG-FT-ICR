"""
Tests for scripts/03_normalize.py

Verifies:
- instrument names resolve to canonical labels
- researchers with ORCIDs deduplicate correctly
- unresolvable entity names go to review_queue.jsonl not the graph
- every normalization decision is logged to normalization_log.jsonl
"""
