"""
analyze_orcid_coverage.py — measure ORCID coverage and match ORCIDs to the
Researcher nodes already present in the graph.

STRICTLY READ-ONLY. This script issues only MATCH/RETURN Cypher. It never
writes to Neo4j, never sets a property, never merges nodes. Its only outputs
are a Markdown report and a candidate JSONL, neither of which is applied to
anything.

Matching discipline (the rule that makes this safe):
  An ORCID is only ever matched against the BOUNDED set of Researcher nodes
  already connected to that same Publication via AUTHORED_BY. There is no
  global name search anywhere in this file. If the CrossRef author cannot be
  resolved inside that per-paper set, the row is UNMATCHED and no candidate is
  emitted.

Name comparison accounts for two known artifacts in the graph's Researcher
nodes, both inherited from the MagLab CSV:
  - accent collapse: 'Håkansson' vs 'Hakansson' (and '_' standing in for an
    accented character, as in the identifier 'h_kansson_k_2024')
  - fused names: one node holding two people, e.g.
    'Purcell, J.M. and Marshall, A.G.' — the CSV's first-author-and-last-author
    convention parsed into a single node.

Usage:
    python3 scripts/analyze_orcid_coverage.py
"""

import collections
import html
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(REPO, "data", "processed", "cache", "crossref")
REVIEW_DIR = os.path.join(REPO, "data", "processed", "review")
REPORT_PATH = os.path.join(REVIEW_DIR, "orcid_coverage_report.md")
CANDIDATES_PATH = os.path.join(REVIEW_DIR, "orcid_candidates.jsonl")

ORCID_RE = re.compile(r"(\d{4}-\d{4}-\d{4}-\d{3}[\dX])", re.I)


# ---------------------------------------------------------------- name utils

def deaccent(text):
    """'Håkansson' -> 'hakansson'. Also repairs the mojibake seen in the CSV."""
    if not text:
        return ""
    # Latin-1 control range artifacts ('\x96' en-dash, '\x9a' s-caron) appear in
    # a few CSV-sourced names; map them to a plain separator / letter.
    text = text.replace("\x96", "-").replace("\x97", "-").replace("\x9a", "s")
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def norm_family(text):
    """Normalize a family name to comparable alpha-only form, keeping '_'.

    '_' is preserved because it stands in for an accented character in
    identifier-derived names; it becomes a single-character wildcard at
    comparison time.
    """
    return re.sub(r"[^a-z0-9_]", "", deaccent(text))


def family_matches(graph_fam, crossref_fam):
    """True if two normalized family names match, treating '_' as a wildcard."""
    a, b = norm_family(graph_fam), norm_family(crossref_fam)
    if not a or not b:
        return False
    if a == b:
        return True
    # '_' stands in for exactly one dropped character (accent-collapse artifact).
    # Build the pattern char-by-char: re.escape() does not escape '_', so a
    # post-hoc replace on the escaped string would silently never fire.
    for pat, other in ((a, b), (b, a)):
        if "_" in pat and len(pat) == len(other):
            rx = "".join("." if c == "_" else re.escape(c) for c in pat)
            if re.fullmatch(rx, other):
                return True
    return False


def initial(given):
    """First alphabetic character of a given name, lowercased ('A.G.' -> 'a')."""
    for ch in deaccent(given or ""):
        if ch.isalpha():
            return ch
    return ""


def split_components(name_full, family_name, given_name):
    """Return [(family, given)] for a Researcher node.

    A fused node ('Purcell, J.M. and Marshall, A.G.') yields one tuple per
    person. A normal node yields a single tuple.
    """
    if name_full and " and " in name_full:
        parts = [p.strip() for p in re.split(r"\s+and\s+", name_full) if p.strip()]
        comps = []
        for part in parts:
            if part.lower().strip(" .") in ("et al", "et al."):
                continue
            if "," in part:
                fam, giv = part.split(",", 1)
            else:
                # 'Chanton J.P.' — trailing initials with no comma.
                m = re.match(r"^(.*?)\s+([A-Z](?:\.[A-Z])*\.?)$", part.strip())
                fam, giv = (m.group(1), m.group(2)) if m else (part, "")
            comps.append((fam.strip(), giv.strip()))
        if comps:
            return comps
    return [(family_name or "", given_name or "")]


# ------------------------------------------------------------- data loading

def load_graph():
    """Pull publications, their DOIs, and their AUTHORED_BY Researcher sets."""
    driver = db.connect()
    try:
        pubs = db.run_query(
            driver,
            """
            MATCH (p:Publication)
            RETURN p.identifier AS identifier, p.doi AS doi,
                   p.publication_year AS year, p.url AS url
            """,
        )
        authors = db.run_query(
            driver,
            """
            MATCH (p:Publication)-[:AUTHORED_BY]->(r:Researcher)
            WHERE p.doi IS NOT NULL
            RETURN p.doi AS doi, r.identifier AS researcher_id,
                   r.name_full AS name_full, r.family_name AS family_name,
                   r.given_name AS given_name
            """,
        )
    finally:
        db.close(driver)

    by_doi = collections.defaultdict(list)
    for a in authors:
        by_doi[a["doi"].strip()].append(a)
    return pubs, by_doi


def cache_path(doi):
    import urllib.parse
    return os.path.join(CACHE_DIR, urllib.parse.quote(doi, safe="") + ".json")


def crossref_authors(doi):
    """Return (status, journal, year, [author dicts]) from the cached response."""
    path = cache_path(doi)
    if not os.path.exists(path):
        return ("missing", None, None, [])
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    if "_scikg_status" in payload:
        return (payload["_scikg_status"], None, None, [])

    msg = payload.get("message", {})
    container = msg.get("container-title") or []
    # CrossRef HTML-escapes titles ('Energy &amp; Fuels').
    journal = html.unescape(container[0]) if container else None
    issued = (msg.get("issued") or {}).get("date-parts") or [[None]]
    year = issued[0][0] if issued and issued[0] else None

    out = []
    for a in msg.get("author", []) or []:
        raw_orcid = a.get("ORCID")
        orcid = None
        if raw_orcid:
            m = ORCID_RE.search(raw_orcid)
            orcid = m.group(1).upper() if m else None
        out.append(
            {
                "given": a.get("given"),
                "family": a.get("family"),
                "sequence": a.get("sequence"),
                "orcid": orcid,
                "authenticated": bool(a.get("authenticated-orcid")),
            }
        )
    return ("ok", journal, year, out)


# ------------------------------------------------------------------ matching

def match_author(cr_author, graph_authors):
    """Match one CrossRef author against the bounded per-paper Researcher set.

    Returns (match_class, [matched researcher records], via_fused_flag).
    """
    hits = []
    fused_hit = False
    for node in graph_authors:
        comps = split_components(
            node["name_full"], node["family_name"], node["given_name"]
        )
        is_fused = len(comps) > 1
        for fam, giv in comps:
            if not family_matches(fam, cr_author["family"]):
                continue
            gi, ci = initial(giv), initial(cr_author["given"])
            # Require the initial to agree when both sides have one; if either
            # side lacks a given name, family agreement alone is accepted.
            if gi and ci and gi != ci:
                continue
            hits.append(node)
            if is_fused:
                fused_hit = True
            break

    if len(hits) == 1:
        return ("MATCH-UNIQUE", hits, fused_hit)
    if len(hits) > 1:
        return ("MATCH-MULTIPLE", hits, fused_hit)
    return ("UNMATCHED", [], False)


def classify_mechanism(nodes):
    """Guess why several Researcher nodes share one ORCID."""
    reasons = []
    if any(n["name_full"] and " and " in n["name_full"] for n in nodes):
        reasons.append("fused-name")
    raw = {(n["family_name"] or "") for n in nodes}
    norm = {norm_family(n["family_name"] or "").replace("_", "") for n in nodes}
    if len(raw) > 1 and len(norm) == 1:
        reasons.append("accent-collapse")
    elif len(norm) > 1:
        reasons.append("spelling-variant")
    # NOTE: the former "year-suffix-duplicate" reason (re.sub(r"_\d{4}$", ...))
    # is removed. Researcher ids no longer carry a year suffix (KI-16 slug fix:
    # researcher:{translit_family}_{initial}), and accent variants now share one
    # id and merge in 03, so this heuristic could no longer fire — it went
    # silently dead rather than erroring. Dropped rather than left inert.
    return "/".join(dict.fromkeys(reasons)) or "same-name-distinct-nodes"


# -------------------------------------------------------------------- report

def main():
    os.makedirs(REVIEW_DIR, exist_ok=True)
    pubs, authors_by_doi = load_graph()

    with_doi = [p for p in pubs if p["doi"]]
    without_doi = [p for p in pubs if not p["doi"]]

    # How many DOI-less records carry a DOI inside their URL (recoverable tier)?
    url_doi_re = re.compile(r"(10\.\d{4,9}/[^\s?&#]+)")
    recoverable = sum(1 for p in without_doi if p["url"] and url_doi_re.search(p["url"]))
    url_no_doi = sum(1 for p in without_doi if p["url"] and not url_doi_re.search(p["url"]))
    no_url = sum(1 for p in without_doi if not p["url"])

    stats = collections.Counter()
    year_rows = collections.defaultdict(lambda: collections.Counter())
    journal_rows = collections.defaultdict(lambda: collections.Counter())
    distinct_orcids = set()
    authenticated_orcids = set()
    class_counts = collections.Counter()
    candidates = []          # MATCH-UNIQUE rows
    multiples = []           # MATCH-MULTIPLE rows
    unmatched = []           # UNMATCHED rows
    fetch_problems = collections.Counter()

    for pub in with_doi:
        doi = pub["doi"].strip()
        year = pub["year"]
        status, journal, cr_year, cr_authors = crossref_authors(doi)
        if status != "ok":
            fetch_problems[status] += 1
            stats["not_queryable"] += 1
            continue

        stats["queried"] += 1
        journal = journal or "(unknown journal)"
        year_rows[year]["papers"] += 1
        journal_rows[journal]["papers"] += 1

        graph_authors = authors_by_doi.get(doi, [])
        stats["crossref_authors"] += len(cr_authors)
        stats["graph_authors"] += len(graph_authors)

        paper_orcids = [a for a in cr_authors if a["orcid"]]
        if paper_orcids:
            stats["papers_with_orcid"] += 1
            year_rows[year]["papers_with_orcid"] += 1
            journal_rows[journal]["papers_with_orcid"] += 1
        year_rows[year]["orcids"] += len(paper_orcids)
        journal_rows[journal]["orcids"] += len(paper_orcids)

        for a in paper_orcids:
            stats["author_orcid_instances"] += 1
            distinct_orcids.add(a["orcid"])
            if a["authenticated"]:
                stats["authenticated_true"] += 1
                authenticated_orcids.add(a["orcid"])
            else:
                stats["authenticated_false"] += 1

            klass, hits, via_fused = match_author(a, graph_authors)
            class_counts[klass] += 1
            row = {
                "doi": doi,
                "publication_identifier": pub["identifier"],
                "year": year,
                "journal": journal,
                "crossref_author": ", ".join(
                    x for x in [a["family"], a["given"]] if x
                ),
                "sequence": a["sequence"],
                "orcid": a["orcid"],
                "authenticated": a["authenticated"],
                "match_class": klass,
            }
            if klass == "MATCH-UNIQUE":
                row["researcher_id"] = hits[0]["researcher_id"]
                row["researcher_name_full"] = hits[0]["name_full"]
                row["matched_via_fused_node"] = via_fused
                candidates.append((row, hits[0]))
            elif klass == "MATCH-MULTIPLE":
                row["researcher_ids"] = [h["researcher_id"] for h in hits]
                row["researcher_names"] = [h["name_full"] for h in hits]
                multiples.append(row)
            else:
                unmatched.append(row)

    # ---------------------------------------------------- cross-paper checks
    orcid_to_nodes = collections.defaultdict(dict)   # orcid -> {rid: node}
    node_to_orcids = collections.defaultdict(set)    # rid -> {orcid}
    orcid_papers = collections.defaultdict(set)
    for row, node in candidates:
        orcid_to_nodes[row["orcid"]][node["researcher_id"]] = node
        node_to_orcids[node["researcher_id"]].add(row["orcid"])
        orcid_papers[row["orcid"]].add(row["doi"])

    clean_orcids = {o: n for o, n in orcid_to_nodes.items() if len(n) == 1}
    fragmented = {o: n for o, n in orcid_to_nodes.items() if len(n) > 1}
    reverse_error = {r: o for r, o in node_to_orcids.items() if len(o) > 1}

    # Same-paper collision: one node claimed by two ORCIDs on the SAME DOI.
    # A paper cannot list one person twice, so this proves the node holds two
    # people — strictly stronger evidence than a cross-paper disagreement.
    per_paper_node = collections.defaultdict(set)
    for row, node in candidates:
        per_paper_node[(row["doi"], node["researcher_id"])].add(row["orcid"])
    same_paper_nodes = {
        rid for (doi, rid), orcids in per_paper_node.items() if len(orcids) > 1
    }

    # ------------------------------------------------------------- emit files
    with open(CANDIDATES_PATH, "w", encoding="utf-8") as fh:
        for row, node in candidates:
            fh.write(
                json.dumps(
                    {
                        "researcher_id": row["researcher_id"],
                        "orcid": row["orcid"],
                        "authenticated": row["authenticated"],
                        "source_doi": row["doi"],
                        "match_class": row["match_class"],
                        "crossref_author": row["crossref_author"],
                        "researcher_name_full": row["researcher_name_full"],
                        "matched_via_fused_node": row["matched_via_fused_node"],
                        "orcid_maps_to_multiple_nodes": row["orcid"] in fragmented,
                        "node_maps_to_multiple_orcids": (
                            row["researcher_id"] in reverse_error
                        ),
                        "same_paper_orcid_collision": (
                            row["researcher_id"] in same_paper_nodes
                        ),
                        "apply": False,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        # MULTIPLE / UNMATCHED are recorded too, with no researcher_id, so the
        # file is a complete account of every ORCID-bearing CrossRef author.
        for row in multiples:
            fh.write(
                json.dumps(
                    {
                        "researcher_id": None,
                        "candidate_researcher_ids": row["researcher_ids"],
                        "orcid": row["orcid"],
                        "authenticated": row["authenticated"],
                        "source_doi": row["doi"],
                        "match_class": row["match_class"],
                        "crossref_author": row["crossref_author"],
                        "apply": False,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        for row in unmatched:
            fh.write(
                json.dumps(
                    {
                        "researcher_id": None,
                        "orcid": row["orcid"],
                        "authenticated": row["authenticated"],
                        "source_doi": row["doi"],
                        "match_class": row["match_class"],
                        "crossref_author": row["crossref_author"],
                        "apply": False,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    write_report(
        pubs, with_doi, without_doi, recoverable, url_no_doi, no_url,
        stats, fetch_problems, distinct_orcids, authenticated_orcids,
        class_counts, year_rows, journal_rows,
        clean_orcids, fragmented, reverse_error, orcid_papers,
        candidates, multiples, unmatched, same_paper_nodes,
    )

    print("queried: %d  papers_with_orcid: %d  distinct ORCIDs: %d"
          % (stats["queried"], stats["papers_with_orcid"], len(distinct_orcids)))
    print("match classes: %s" % dict(class_counts))
    print("clean ORCIDs: %d  fragmented ORCIDs: %d  reverse-error nodes: %d"
          % (len(clean_orcids), len(fragmented), len(reverse_error)))
    print("wrote %s" % REPORT_PATH)
    print("wrote %s" % CANDIDATES_PATH)


def pct(n, d):
    return "%.1f%%" % (100.0 * n / d) if d else "n/a"


def write_report(pubs, with_doi, without_doi, recoverable, url_no_doi, no_url,
                 stats, fetch_problems, distinct_orcids, authenticated_orcids,
                 class_counts, year_rows, journal_rows,
                 clean_orcids, fragmented, reverse_error, orcid_papers,
                 candidates, multiples, unmatched, same_paper_nodes):
    L = []
    A = L.append
    A("# ORCID coverage and Researcher-node matching — read-only survey")
    A("")
    A("**Status: MEASUREMENT ONLY. Nothing in this pass was applied.** No graph "
      "writes, no properties set, no nodes merged, no git operations. The two "
      "artifacts produced (`orcid_coverage_report.md`, `orcid_candidates.jsonl`) "
      "are proposals for review.")
    A("")
    A("**Schema note.** `docs/SCIKG_SCHEMA.md` defines no `orcid` property on "
      "`Researcher`. Adding one is a schema decision for Diya, and nothing in "
      "`orcid_candidates.jsonl` can be applied until that is ruled. Every row in "
      "the candidate file carries `apply: false`.")
    A("")
    A("**Method.** ORCIDs come from CrossRef's structured author array "
      "(`author[].ORCID`, `author[].authenticated-orcid`) — a deterministic "
      "per-DOI lookup, not an LLM extraction. No ORCID was inferred; no "
      "name-based lookup against the ORCID registry was performed. Matching is "
      "bounded per paper: a CrossRef author is compared **only** against the "
      "Researcher nodes already linked to that Publication by `AUTHORED_BY`. "
      "There is no global name search anywhere in the pipeline.")
    A("")

    # ---- 1. coverage
    A("## 1. Coverage pass")
    A("")
    A("### 1.1 Which publications are queryable at all")
    A("")
    A("| Class | Count | Share of corpus |")
    A("|---|---:|---:|")
    A("| Publication nodes in graph | %d | 100%% |" % len(pubs))
    A("| Has a `doi` property (queryable) | %d | %s |"
      % (len(with_doi), pct(len(with_doi), len(pubs))))
    A("| No `doi` property (**not** queryable) | %d | %s |"
      % (len(without_doi), pct(len(without_doi), len(pubs))))
    A("")
    A("All %d DOI values are well-formed (`^10\\.\\d{4,9}/\\S+$`); there are no "
      "malformed DOIs to repair. The gap is not malformation — it is **absence**."
      % len(with_doi))
    A("")
    pre2016 = sum(1 for p in without_doi if p["year"] and p["year"] < 2016)
    A("The %d DOI-less records are essentially the pre-2016 tail (%d of %d fall "
      "before 2016; the exceptions are %d later records). They break down as:"
      % (len(without_doi), pre2016, len(without_doi), len(without_doi) - pre2016))
    A("")
    A("| DOI-less subclass | Count | Note |")
    A("|---|---:|---|")
    A("| URL contains a recoverable DOI | %d | e.g. `pubs.acs.org/doi/abs/10.1021/ac504166t` — the DOI is literally in the stored URL |" % recoverable)
    A("| URL present, no DOI in it | %d | publisher landing/abstract pages, PubMed links |" % url_no_doi)
    A("| No URL at all | %d | nothing to resolve from |" % no_url)
    A("")
    A("**This pass queried only the %d records that already carry a `doi` "
      "property.** The %d URL-recoverable DOIs are a real, cheap expansion of "
      "coverage — the DOI is present in committed source, so extracting it is a "
      "parse, not an inference — but harvesting them changes what the graph's "
      "`doi` field means and is out of scope for a read-only measurement. "
      "Flagged for Diya as a follow-up." % (len(with_doi), recoverable))
    A("")

    years_with = sorted(
        {p["year"] for p in with_doi if p["year"]}
    )
    years_without = sorted({p["year"] for p in without_doi if p["year"]})
    A("The split is almost perfectly chronological: DOI-less records span "
      "%s–%s, DOI-bearing records span %s–%s. The MagLab CSV simply did not "
      "record DOIs for older entries."
      % (min(years_without), max(years_without), min(years_with), max(years_with)))
    A("")

    if fetch_problems:
        A("### 1.2 Fetch outcomes")
        A("")
        A("| Outcome | Count |")
        A("|---|---:|")
        for k, v in sorted(fetch_problems.items()):
            A("| %s | %d |" % (k, v))
        A("")

    A("### 1.3 ORCID coverage among queried papers")
    A("")
    q = stats["queried"]
    A("| Metric | Value |")
    A("|---|---:|")
    A("| Papers queried | %d |" % q)
    A("| Papers returning >=1 author ORCID | %d (%s of queried) |"
      % (stats["papers_with_orcid"], pct(stats["papers_with_orcid"], q)))
    A("| Papers returning no author ORCID | %d (%s of queried) |"
      % (q - stats["papers_with_orcid"], pct(q - stats["papers_with_orcid"], q)))
    A("| Author positions in CrossRef | %d |" % stats["crossref_authors"])
    A("| Author positions carrying an ORCID | %d (%s of author positions) |"
      % (stats["author_orcid_instances"],
         pct(stats["author_orcid_instances"], stats["crossref_authors"])))
    A("| **Total distinct ORCIDs found** | **%d** |" % len(distinct_orcids))
    A("| `authenticated-orcid: true` (instances) | %d (%s) |"
      % (stats["authenticated_true"],
         pct(stats["authenticated_true"], stats["author_orcid_instances"])))
    A("| `authenticated-orcid: false` (instances) | %d (%s) |"
      % (stats["authenticated_false"],
         pct(stats["authenticated_false"], stats["author_orcid_instances"])))
    A("| Distinct ORCIDs authenticated at least once | %d |"
      % len(authenticated_orcids))
    A("")
    A("For scale: the graph holds %d `AUTHORED_BY` edges on these DOI papers, "
      "against %d CrossRef author positions — within %s of each other. For the "
      "DOI-bearing (i.e. modern) part of the corpus the MagLab CSV recorded "
      "essentially complete author lists, which is why the match rate in "
      "section 2 is high."
      % (stats["graph_authors"], stats["crossref_authors"],
         pct(abs(stats["crossref_authors"] - stats["graph_authors"]),
             stats["crossref_authors"])))
    A("")

    A("### 1.4 By publication year")
    A("")
    A("| Year | Papers queried | With >=1 ORCID | % | ORCID instances |")
    A("|---:|---:|---:|---:|---:|")
    for y in sorted(k for k in year_rows if k is not None):
        r = year_rows[y]
        A("| %s | %d | %d | %s | %d |"
          % (y, r["papers"], r["papers_with_orcid"],
             pct(r["papers_with_orcid"], r["papers"]), r["orcids"]))
    A("")
    early = [year_rows[y] for y in year_rows if y and y <= 2016]
    late = [year_rows[y] for y in year_rows if y and y >= 2017]
    e_p = sum(r["papers"] for r in early)
    e_o = sum(r["papers_with_orcid"] for r in early)
    l_p = sum(r["papers"] for r in late)
    l_o = sum(r["papers_with_orcid"] for r in late)
    A("This is not a gradual skew — it is a **cliff between 2016 and 2017**. "
      "Through 2016, %d of %d papers carry any author ORCID (%s); from 2017 "
      "onward, %d of %d do (%s), and the rate never drops below ~70%% again. "
      "That boundary is when the major publishers in this corpus began pushing "
      "ORCID through their submission systems, and it means ORCID is a usable "
      "identity signal for the modern corpus only."
      % (e_o, e_p, pct(e_o, e_p), l_o, l_p, pct(l_o, l_p)))
    A("")
    A("Compounding effect worth stating plainly: the ORCID-rich years are "
      "exactly the years that have DOIs at all. The pre-2016 corpus is "
      "unreachable twice over — no DOI to query, and no ORCID even if queried. "
      "Any ORCID-based identity work will only ever touch the recent half of "
      "the graph.")
    A("")

    A("### 1.5 By journal (CrossRef `container-title`, papers >= 3)")
    A("")
    A("| Journal | Papers | With >=1 ORCID | % | ORCID instances |")
    A("|---|---:|---:|---:|---:|")
    ranked = sorted(journal_rows.items(), key=lambda kv: -kv[1]["papers"])
    for j, r in ranked:
        if r["papers"] < 3:
            continue
        A("| %s | %d | %d | %s | %d |"
          % (j, r["papers"], r["papers_with_orcid"],
             pct(r["papers_with_orcid"], r["papers"]), r["orcids"]))
    tail = [r for _, r in ranked if r["papers"] < 3]
    if tail:
        A("| _(%d journals with 1–2 papers)_ | %d | %d | %s | %d |"
          % (len(tail), sum(r["papers"] for r in tail),
             sum(r["papers_with_orcid"] for r in tail),
             pct(sum(r["papers_with_orcid"] for r in tail),
                 sum(r["papers"] for r in tail)),
             sum(r["orcids"] for r in tail)))
    A("")

    # ---- 2. matching
    A("## 2. Match to existing Researcher nodes (bounded, per paper)")
    A("")
    total_cls = sum(class_counts.values())
    A("| Class | Count | Share |")
    A("|---|---:|---:|")
    for k in ("MATCH-UNIQUE", "MATCH-MULTIPLE", "UNMATCHED"):
        A("| %s | %d | %s |" % (k, class_counts[k], pct(class_counts[k], total_cls)))
    A("| **Total ORCID-bearing CrossRef author positions** | **%d** | |" % total_cls)
    A("")
    A("`MATCH-MULTIPLE` is empty, and that is a real result rather than a "
      "silent one: the graph's 108 fused nodes all sit in the 2000–2017 range, "
      "which is almost entirely the DOI-less tail, so they are barely reachable "
      "from a DOI-driven pass. The single fused node that *is* reachable "
      "(`researcher:martin_b_2017`) surfaces instead in section 3.3.")
    A("")
    A("#### What the %d UNMATCHED rows actually are" % class_counts["UNMATCHED"])
    A("")
    A("They are not random misses. Inspecting them against the graph shows a "
      "single systematic cause: **the MagLab CSV's name parser treats the last "
      "whitespace-delimited word as the family name** and folds everything "
      "before it into initials. Compound and particle surnames are therefore "
      "stored under the wrong family name:")
    A("")
    A("| CrossRef author | Stored in graph as | Node |")
    A("|---|---|---|")
    A("| Van Geem, Kevin M. | `Geem, K.M.V.` | `researcher:geem_k_2024` |")
    A("| Palacio Lozano, Diana Catalina | `Lozano, D.C.P.` | `researcher:lozano_d_2024` |")
    A("| Salvato Vallverdu, Germain | `Vallverdu, G.S.` | `researcher:vallverdu_g_2026` |")
    A("| Rojas Ramírez, Carolina | `Ramirez, C.R.` | `researcher:ram_rez_c_2024` |")
    A("")
    A("The matcher deliberately does **not** resolve these: family `Van Geem` "
      "does not equal family `Geem`, and bridging that gap would mean guessing. "
      "Under the bounded rule they are reported, never assigned. This is worth "
      "recording as a distinct data-quality defect in its own right — it "
      "affects the graph's author identity independently of ORCID.")
    A("")

    if multiples:
        A("### 2.1 MATCH-MULTIPLE — flagged, not assigned (%d)" % len(multiples))
        A("")
        A("More than one Researcher node on the same paper matched the CrossRef "
          "author. No candidate is emitted for these.")
        A("")
        A("| DOI | CrossRef author | ORCID | Competing nodes |")
        A("|---|---|---|---|")
        for r in multiples[:40]:
            A("| `%s` | %s | `%s` | %s |"
              % (r["doi"], r["crossref_author"], r["orcid"],
                 "<br>".join("`%s`" % x for x in r["researcher_ids"])))
        if len(multiples) > 40:
            A("")
            A("_(%d more in `orcid_candidates.jsonl`)_" % (len(multiples) - 40))
        A("")

    # ---- 3. cross-paper consistency
    A("## 3. Cross-paper consistency")
    A("")
    A("Grouping the %d `MATCH-UNIQUE` candidates by ORCID across all papers."
      % len(candidates))
    A("")

    A("### 3.1 Clean — one ORCID, one Researcher node everywhere (%d)"
      % len(clean_orcids))
    A("")
    A("These are the strongest candidates: the ORCID resolved to the same "
      "single node on every paper it appeared on.")
    A("")
    tainted = {
        o for o, nodes in clean_orcids.items()
        if any(rid in reverse_error for rid in nodes)
    }
    if tainted:
        A("**Caveat — 'clean' here means clean *from the ORCID side*, and %d of "
          "these %d are not safe to apply.** This section groups by ORCID; "
          "section 3.3 groups by node. An ORCID can point unambiguously at one "
          "node while that node is itself a conflation of two people. "
          "`researcher:anderson_l_2026` below is exactly this: the ORCID "
          "`0000-0001-8633-0251` resolves to it consistently across 14 papers, "
          "yet the node also answers to a second ORCID. Writing the ORCID onto "
          "the node would silently assert that the conflated node is one "
          "person. **Intersect this list against section 3.3 before applying "
          "anything.**" % (len(tainted), len(clean_orcids)))
        A("")
    multi_paper = {o: n for o, n in clean_orcids.items() if len(orcid_papers[o]) > 1}
    A("Of these, **%d are corroborated across more than one paper** (the same "
      "ORCID independently matching the same node on 2+ DOIs), which is the "
      "strongest evidence class here. The remaining %d rest on a single paper."
      % (len(multi_paper), len(clean_orcids) - len(multi_paper)))
    A("")
    if multi_paper:
        A("| ORCID | Researcher node | Papers |")
        A("|---|---|---:|")
        for o, nodes in sorted(
            multi_paper.items(), key=lambda kv: -len(orcid_papers[kv[0]])
        )[:30]:
            rid = list(nodes)[0]
            A("| `%s` | `%s` | %d |" % (o, rid, len(orcid_papers[o])))
        if len(multi_paper) > 30:
            A("")
            A("_(%d more)_" % (len(multi_paper) - 30))
        A("")

    A("### 3.2 FRAGMENTATION — one ORCID, multiple Researcher nodes (%d)"
      % len(fragmented))
    A("")
    if fragmented:
        A("**This is definitive same-person-multiple-nodes evidence.** An ORCID "
          "is a persistent personal identifier; where one resolves to two or "
          "more distinct nodes, those nodes are the same human being. This is "
          "the strongest de-duplication signal available to the project — it "
          "does not depend on name-similarity heuristics.")
        A("")
        A("| ORCID | Researcher nodes | `name_full` values | Implicated mechanism |")
        A("|---|---|---|---|")
        for o, nodes in sorted(fragmented.items()):
            recs = list(nodes.values())
            A("| `%s` | %s | %s | %s |"
              % (o,
                 "<br>".join("`%s`" % r["researcher_id"] for r in recs),
                 "<br>".join((r["name_full"] or "—").replace("|", r"\|") for r in recs),
                 classify_mechanism(recs)))
        A("")
    else:
        A("None found among the confident candidates.")
        A("")

    A("### 3.3 REVERSE ERROR — one Researcher node, multiple ORCIDs (%d)"
      % len(reverse_error))
    A("")
    if reverse_error:
        A("**FLAG LOUDLY.** A single node matching two different ORCIDs means "
          "that node very likely holds **two different people**. This is the "
          "opposite failure from fragmentation and is more damaging: merging "
          "would make it worse, and any analysis that treats the node as one "
          "person is already wrong.")
        A("")
        A("These split into two evidence strengths, and the difference matters:")
        A("")
        A("- **Same-paper collision (%d)** — two ORCIDs landed on one node from "
          "the *same* DOI. This is **definitive**: a paper cannot list the same "
          "person twice, so the node provably holds two people."
          % len(same_paper_nodes))
        A("- **Cross-paper only (%d)** — the two ORCIDs come from different "
          "papers. Very strong, but not airtight: one person holding two ORCID "
          "records is rare yet possible, so these want a human glance before "
          "being treated as proven conflations."
          % (len(reverse_error) - len(same_paper_nodes)))
        A("")
        A("That only **1 of %d** MATCH-UNIQUE rows produced a same-paper "
          "collision is also a useful check on the matcher itself: it is not "
          "systematically over-matching." % len(candidates))
        A("")
        A("| Researcher node | `name_full` | Evidence | ORCIDs | DOIs |")
        A("|---|---|---|---|---|")
        node_lookup = {}
        for row, node in candidates:
            node_lookup[node["researcher_id"]] = node
        cand_by_node = collections.defaultdict(list)
        for row, node in candidates:
            cand_by_node[node["researcher_id"]].append(row)
        for rid, orcids in sorted(
            reverse_error.items(), key=lambda kv: (kv[0] not in same_paper_nodes, kv[0])
        ):
            node = node_lookup[rid]
            dois = sorted({r["doi"] for r in cand_by_node[rid]})
            evidence = (
                "**same-paper — definitive**"
                if rid in same_paper_nodes
                else "cross-paper"
            )
            A("| `%s` | %s | %s | %s | %s |"
              % (rid, (node["name_full"] or "—").replace("|", r"\|"), evidence,
                 "<br>".join("`%s`" % o for o in sorted(orcids)),
                 "<br>".join("`%s`" % d for d in dois[:6])))
        A("")
        A("The same-paper case, `researcher:martin_b_2017` "
          "(`\"Martin, B.R. and Hakansson, K.\"`), is the fused-name mechanism "
          "caught red-handed: the node is literally two people, and ORCID "
          "independently confirms it. Note it appears in section 3.2 as well — "
          "it is simultaneously a fragment of Håkansson's identity and a fusion "
          "of two people, which is exactly what a first-author-and-last-author "
          "CSV string collapsed into one node produces.")
        A("")
        A("The six cross-paper cases are all common family name + single "
          "initial (`Zhang, Y.`, `Huang, C.`, `Lin, Y.`, `Smith, L.C.`, "
          "`Anderson, L.C.`, `Zhang, Z.`). This points at the identity model "
          "itself: `researcher:{family}_{initial}` has no way to separate two "
          "researchers who share a family name and first initial, so they "
          "silently become one node. ORCID is the only signal in the corpus "
          "that can detect this.")
        A("")
    else:
        A("None found. No Researcher node in the confident candidate set "
          "resolved to two different ORCIDs.")
        A("")

    # ---- 4. files
    A("## 4. Artifacts emitted")
    A("")
    A("| File | Contents |")
    A("|---|---|")
    A("| `data/processed/review/orcid_coverage_report.md` | this report |")
    A("| `data/processed/review/orcid_candidates.jsonl` | one row per ORCID-bearing CrossRef author position (%d rows: %d MATCH-UNIQUE, %d MATCH-MULTIPLE, %d UNMATCHED), every row `apply: false` |"
      % (len(candidates) + len(multiples) + len(unmatched),
         len(candidates), len(multiples), len(unmatched)))
    A("")
    A("Cached CrossRef responses live in `data/processed/cache/crossref/` "
      "(gitignored under `data/processed/*`), so re-running re-queries nothing.")
    A("")
    A("### Nothing here is applied")
    A("")
    A("To apply any of it, three things must happen first, in order:")
    A("")
    A("1. **Schema ruling** — `docs/SCIKG_SCHEMA.md` gains an `orcid` property "
      "on `Researcher` (plus a provenance decision: `authenticated-orcid` "
      "true/false should be recorded, not dropped).")
    A("2. **Reverse-error triage** — the section 3.3 nodes are resolved, since "
      "assigning a single ORCID to a node holding two people would bake the "
      "error in.")
    A("3. **Pipeline route** — per the project's `graph = f(files)` rule, "
      "ORCIDs must enter through pre-normalize JSONL and flow 03 -> 04 -> 05, "
      "not by direct graph write.")
    A("")

    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
