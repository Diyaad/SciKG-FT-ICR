"""
db.py — Neo4j connection layer for SciKG.

Thin wrapper around the official neo4j Python driver. Reads connection
credentials from the environment (never hard-coded), so nothing sensitive is
committed. Used by 05_load.py to write validated records into the graph.

Environment variables (set these in .env at the repo root; .env is gitignored):
    NEO4J_URI       e.g. neo4j+s://bf9ce500.databases.neo4j.io   (Aura)
    NEO4J_USER      e.g. neo4j
    NEO4J_PASSWORD  the instance password

This module is a CONNECTION layer only. The idempotent MERGE-with-provenance
load logic lives in 05_load.py, which calls run_query() with parameterised
Cypher. Keeping connection and load logic separate makes each testable on its
own.

Quick self-test (confirms credentials + reachability):
    python scripts/db.py
"""

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load .env from the repo root so credentials are available whether this module
# is imported or run directly.
load_dotenv()

NEO4J_URI = os.environ.get("NEO4J_URI")
NEO4J_USER = os.environ.get("NEO4J_USER")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")


def connect():
    """Open and return a Neo4j driver.

    The driver manages a connection pool; create one and reuse it, then call
    close() when done. Raises a clear error if credentials are missing, rather
    than failing obscurely inside the driver.
    """
    missing = [
        name
        for name, value in (
            ("NEO4J_URI", NEO4J_URI),
            ("NEO4J_USER", NEO4J_USER),
            ("NEO4J_PASSWORD", NEO4J_PASSWORD),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing Neo4j credentials in environment: "
            + ", ".join(missing)
            + ". Set them in .env at the repo root."
        )

    driver = GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    return driver


def close(driver):
    """Close the driver and release its connection pool."""
    if driver is not None:
        driver.close()


def run_query(driver, cypher, params=None):
    """Run a Cypher statement and return the results as a list of dicts.

    Parameters are passed separately (params dict) and never string-formatted
    into the query — this is required for safety and correctness. Uses an
    auto-commit session; 05_load.py can layer explicit transactions on top
    later if batching is needed.
    """
    if params is None:
        params = {}
    with driver.session() as session:
        result = session.run(cypher, params)
        return [record.data() for record in result]


def test_connection():
    """Open a connection, run a trivial query, and report success/failure.

    Returns True on success. Prints a clear message either way. This is the
    first milestone: if this passes, the whole Neo4j path is open.
    """
    driver = None
    try:
        driver = connect()
        rows = run_query(driver, "RETURN 1 AS ok")
        if rows and rows[0].get("ok") == 1:
            # Also fetch the server version as a friendly confirmation.
            info = run_query(
                driver,
                "CALL dbms.components() YIELD name, versions "
                "RETURN name, versions",
            )
            version = ""
            if info:
                version = f" (server: {info[0].get('name')} {info[0].get('versions')})"
            print(f"CONNECTION OK{version}")
            return True
        print("CONNECTION FAILED: unexpected result from RETURN 1")
        return False
    except Exception as e:
        print(f"CONNECTION FAILED: {type(e).__name__}: {e}")
        return False
    finally:
        close(driver)


if __name__ == "__main__":
    test_connection()
