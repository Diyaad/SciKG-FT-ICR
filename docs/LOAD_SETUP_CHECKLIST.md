# Load Setup Checklist (fresh machine → graph in Neo4j)

Goal: get `05_load.py` to load the SciKG graph into Neo4j on your machine.
Follow top to bottom. Shared credentials + an `.env` file are **necessary but
not sufficient** — the load reads local pipeline output that is **not** in git,
so you must regenerate it first.

Everything below is Windows / PowerShell. Run all commands from the repo root
(`SciKG-FT-ICR`), not from inside `scripts/`.

---

## 0. Prerequisites

- [ ] Python 3.x on PATH (`python --version`)
- [ ] Dependencies installed:
  ```powershell
  pip install -r requirements.txt
  ```
  (You need at least `neo4j` and `python-dotenv`.)

## 1. Be on the right branch, up to date

- [ ] On `diya/pipeline-expansion` and pulled:
  ```powershell
  git branch --show-current      # should print diya/pipeline-expansion
  git pull origin diya/pipeline-expansion
  ```
  This branch already contains the `04_validate.py` UTF-8 fix (commit
  `80eea91`). Without it, `04` crashes on Windows with
  `UnicodeDecodeError: 'charmap' codec can't decode byte ...`.

> You do **not** need `data/raw/rawfiles_pxd/` (the 952 local-only PXD files).
> The PXD *outputs* are already committed under `data/processed/entities/`, so
> `03_normalize.py` has everything it needs. You do **not** run `02f`.

## 2. Create `.env` at the repo root — the right way

The file must be **UTF-8, no BOM, no null bytes**. The #1 setup failure is a
`.env` saved as UTF-16 by PowerShell (`>`, `Out-File`, `Set-Content` without
`-Encoding utf8`), which makes `db.py` die with `ValueError: embedded null
character`.

- [ ] Create `SciKG-FT-ICR\.env` with exactly these three keys (values from the
  shared credentials — no quotes, no trailing spaces):
  ```
  NEO4J_URI=neo4j+s://<instance>.databases.neo4j.io
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=<the-instance-password>
  ```
  **Recommended:** create it in VS Code → paste the 3 lines → bottom-right
  status bar, click the encoding → **"Save with Encoding" → "UTF-8"** (NOT
  "UTF-8 with BOM", NOT "UTF-16"). Do **not** create it with `echo ... > .env`.

- [ ] Verify it's clean (no nulls, no BOM):
  ```powershell
  python -c "b=open('.env','rb').read(); print('nulls:', b.count(0), '| first2:', b[:2].hex())"
  ```
  Expected: `nulls: 0 | first2:` something that is **not** `fffe` or `feff`
  (a `4e...` / plain-ASCII start is good). If nulls > 0 or you see a BOM,
  recreate the file as UTF-8.

## 3. Confirm the database connection

- [ ] ```powershell
  python scripts/db.py
  ```
  Expected: `CONNECTION OK (server: Neo4j Kernel ['5.x-aura'])`.
  The DB is Neo4j **Aura (cloud)** — the same credentials reach the same
  instance from any machine, so there is no local Neo4j to start.
  If this fails, fix it **before** running the pipeline (see table below).

## 4. Run the pipeline in order

Never skip or reorder stages.

- [ ] ```powershell
  python scripts/03_normalize.py
  ```
  Expect it to mint RawDataFile composite ids and ~21 Advisory nodes.

- [ ] ```powershell
  python scripts/04_validate.py
  ```
  Confirm the gate in `data/processed/validated/validation_report.json`:
  ```powershell
  python -c "import json; r=json.load(open('data/processed/validated/validation_report.json',encoding='utf-8')); print('load_cleared:', r['load_cleared'], '| quarantined:', r['quarantined'], '| byte_identical_sets:', len(r['counted_categories']['byte_identical_sets']))"
  ```
  Expected: **`load_cleared: True | quarantined: 0 | byte_identical_sets: 21`**.
  If `load_cleared` is `False`, **stop** and report — do not run `05`.

- [ ] ```powershell
  python scripts/05_load.py
  ```
  Expected tail: `DONE: 4909 nodes, 11668 edges loaded (idempotent; safe to
  re-run).` It's idempotent (MERGE), so re-running never duplicates nodes/edges.

---

## Troubleshooting — error → cause → fix

| Error you see | Where | Cause | Fix |
|---|---|---|---|
| `UnicodeDecodeError: 'charmap' codec can't decode byte ...` | `04` | Old branch without the UTF-8 fix | `git pull origin diya/pipeline-expansion` (step 1) |
| `ValueError: embedded null character` | `db.py` / `05` | `.env` saved as UTF-16 | Recreate `.env` as UTF-8 (step 2) |
| `Missing Neo4j credentials in environment: ...` | `db.py` / `05` | `.env` not at repo root, or wrong var names | Put `.env` in repo root; use exact names `NEO4J_URI/USER/PASSWORD` |
| `CONNECTION FAILED: ... Unauthorized` | `db.py` | Wrong password, or trailing space/quote on a value | Re-copy the value; no quotes, no trailing whitespace |
| `CONNECTION FAILED: ... ServiceUnavailable` / timeout | `db.py` | Network/firewall/VPN blocking outbound TCP 7687 | Try another network; check the URI |
| `FileNotFoundError` / missing `validation_report.json` | `05` | `validated/` was never generated (not in git) | Run `03` then `04` first (step 4) |
| `ModuleNotFoundError: neo4j` / `dotenv` | any | Deps not installed | `pip install -r requirements.txt` |

If you still get stuck, send the **exact error text** and **which command**
produced it — that pins the cause immediately.
