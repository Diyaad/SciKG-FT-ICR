"""
Tests for scripts/02b_extract_csv.py (SciKG pipeline stage 2b — MagLab CSV).

Covers:
- DOI normalization (lowercase, strip doi.org prefix, reject publisher URLs)
- publication identifier minting (doi: vs pub:maglab: fallback)
- multi-value Data Set Urls splitting + whitespace stripping
- ProteoSAFe-without-MSV exclusion
- email privacy (no email ever reaches researcher output)
- provenance integrity (six keys on every record)
- relationship endpoint integrity (no orphans)

Standard library only (unittest). The module under test has a digit-prefixed
filename, so it is loaded by path via importlib.
"""

import importlib.util
import unittest
from pathlib import Path

# --- Load scripts/02b_extract_csv.py by path (name starts with a digit) ------
_MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "02b_extract_csv.py"
_spec = importlib.util.spec_from_file_location("extract_csv", _MODULE_PATH)
extract_csv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(extract_csv)


def make_row(**overrides):
    """Build a full 48-column CSV row dict, blank by default, with overrides."""
    columns = [
        "Id", "Published Year", "Authors",
        "Corr Auth 1 Last, First Name", "Corr Author 1 Email",
        "Corr Auth 1 NHMFL", "Corr Auth 1 Ext",
        "Corr Auth 2 Last, First Name", "Corr Auth 2 Email",
        "Corr Auth 2 NHMFL", "Corr Auth 2 Ext",
        "Corr Auth 3 Last, First Name", "Corr Auth 3 Email",
        "Corr Auth 3 NHMFL", "Corr Auth 3 Ext",
        "% of NHMFL Authors", "% of Ext Authors", "Title", "Note",
        "Facilities", "Journal Name", "Journal Abbreviation",
        "MagLab Significant", "Volume", "Issue", "Pages", "Url",
        "Digital Object Identifier", "Data Set Urls", "Magnet System Status",
        "Magnet Systems", "Acknowledgement of the MagLab's NSF core grant",
        "Should have acknowledged the MagLab's NSF core grant",
        "Month Published", "Day Published", "Name of Conference",
        "Type of Conference", "Type of Presentation", "Virtual",
        "International", "City", "State", "Country", "University",
        "Department", "Advisor", "Degrees", "UCGP Supported",
    ]
    row = {c: "" for c in columns}
    row.update(overrides)
    return row


class TestDoiNormalization(unittest.TestCase):
    def test_doi_normalization(self):
        # Lowercases.
        self.assertEqual(
            extract_csv.normalize_doi("10.1021/ACS.AnalChem.5C06165"),
            ("10.1021/acs.analchem.5c06165", True),
        )
        # Strips https:// and http:// doi.org prefixes.
        self.assertEqual(
            extract_csv.normalize_doi("https://doi.org/10.1021/acs.est.5c08206"),
            ("10.1021/acs.est.5c08206", True),
        )
        self.assertEqual(
            extract_csv.normalize_doi("http://doi.org/10.1016/j.watres.2025.125251"),
            ("10.1016/j.watres.2025.125251", True),
        )
        # Rejects a publisher landing-page URL (one of the 4 non-DOI rows).
        doi, valid = extract_csv.normalize_doi(
            "https://www.nature.com/articles/ncomms6844"
        )
        self.assertFalse(valid)
        self.assertIsNone(doi)
        # Blank / placeholder -> not valid.
        self.assertEqual(extract_csv.normalize_doi(""), (None, False))
        self.assertEqual(extract_csv.normalize_doi("N/A"), (None, False))


class TestPublicationIdentifier(unittest.TestCase):
    def test_publication_identifier_with_doi(self):
        self.assertEqual(
            extract_csv.publication_identifier("10.1021/acs.analchem.5c06165", 18517),
            "doi:10.1021/acs.analchem.5c06165",
        )

    def test_publication_identifier_no_doi(self):
        self.assertEqual(
            extract_csv.publication_identifier(None, 18517),
            "pub:maglab:18517",
        )

    def test_invalid_doi_column_becomes_url(self):
        # A publisher URL in the DOI column => no doi, original kept as url.
        doi, url = extract_csv.resolve_doi_and_url(
            "https://www.nature.com/articles/ncomms6844", ""
        )
        self.assertIsNone(doi)
        self.assertEqual(url, "https://www.nature.com/articles/ncomms6844")

    def test_redundant_doi_org_url_dropped(self):
        # Url column duplicating the DOI is dropped to null.
        doi, url = extract_csv.resolve_doi_and_url(
            "10.1021/acs.est.5c08206",
            "https://doi.org/10.1021/acs.est.5c08206",
        )
        self.assertEqual(doi, "10.1021/acs.est.5c08206")
        self.assertIsNone(url)


class TestDatasetUrls(unittest.TestCase):
    def test_multi_value_dataset_url_split(self):
        # Comma-separated cell with surrounding whitespace -> multiple records.
        ext = extract_csv.Extractor()
        row = make_row(
            Id="1", **{"Published Year": "2020", "Title": "T",
                       "Data Set Urls": " https://osf.io/ab4zv/ ,  https://osf.io/cd5yw/ "}
        )
        ext.process_row(row)
        datasets = ext.entities["Dataset"]
        self.assertEqual(len(datasets), 2)
        ids = {d["identifier"] for d in datasets}
        self.assertEqual(ids, {"dataset:osf:ab4zv", "dataset:osf:cd5yw"})
        # Every dataset got a HAS_DATASET relationship.
        has = [r for r in ext.relationships if r["relationship_type"] == "HAS_DATASET"]
        self.assertEqual(len(has), 2)

    def test_proteosafe_excluded(self):
        # massive.ucsd.edu ProteoSAFe task link with no MSV accession is skipped.
        result = extract_csv.classify_dataset_url(
            "https://massive.ucsd.edu/ProteoSAFe/status.jsp?task=abc123def456"
        )
        self.assertEqual(result[0], "__SKIP__")

        ext = extract_csv.Extractor()
        row = make_row(
            Id="2", **{"Published Year": "2020", "Title": "T",
                       "Data Set Urls":
                       "https://massive.ucsd.edu/ProteoSAFe/status.jsp?task=abc123"}
        )
        ext.process_row(row)
        self.assertEqual(len(ext.entities["Dataset"]), 0)
        self.assertEqual(ext.counts["datasets_skipped_proteosafe"], 1)

    def test_massive_with_msv_kept(self):
        repo, acc, review = extract_csv.classify_dataset_url(
            "https://massive.ucsd.edu/ProteoSAFe/dataset.jsp?accession=MSV000087890"
        )
        self.assertEqual(repo, "MassIVE")
        self.assertEqual(acc, "MSV000087890")

    def test_other_url_flagged_for_review(self):
        repo, acc, review = extract_csv.classify_dataset_url(
            "http://data.gulfresearchinitiative.org"
        )
        self.assertEqual(repo, "Other")
        self.assertTrue(review)
        self.assertEqual(len(acc), 8)  # md5 fingerprint


class TestEmailPrivacy(unittest.TestCase):
    def test_email_never_written(self):
        # A row carrying corr-author emails must produce 0 emails in any output.
        ext = extract_csv.Extractor()
        row = make_row(
            Id="3",
            **{
                "Published Year": "2019",
                "Title": "Privacy test",
                "Authors": "Butcher, D.; Marshall, A.G.",
                "Corr Auth 1 Last, First Name": "Butcher, D.",
                "Corr Author 1 Email": "butcher@magnet.fsu.edu",
                "Corr Auth 1 NHMFL": "X",
            },
        )
        ext.process_row(row)
        blob = ""
        for recs in ext.entities.values():
            for r in recs:
                blob += extract_csv.json.dumps(r)
        for r in ext.relationships:
            blob += extract_csv.json.dumps(r)
        self.assertNotIn("@", blob)
        self.assertNotIn("butcher@magnet.fsu.edu", blob)

    def test_corresponding_author_flags(self):
        ext = extract_csv.Extractor()
        row = make_row(
            Id="4",
            **{
                "Published Year": "2019",
                "Title": "Flags",
                "Authors": "Butcher, D.; Marshall, A.G.",
                "Corr Auth 1 Last, First Name": "Butcher, D.",
                "Corr Auth 1 NHMFL": "X",
            },
        )
        ext.process_row(row)
        butcher = next(r for r in ext.entities["Researcher"]
                       if r["identifier"] == "researcher:butcher_d_2019")
        self.assertTrue(butcher["properties"]["is_corresponding_author"])
        self.assertTrue(butcher["properties"]["is_nhmfl_author"])
        # Non-corresponding author keeps null flags.
        marshall = next(r for r in ext.entities["Researcher"]
                        if r["identifier"].startswith("researcher:marshall_"))
        self.assertIsNone(marshall["properties"]["is_corresponding_author"])


class TestProvenance(unittest.TestCase):
    def test_provenance_on_every_record(self):
        ext = extract_csv.Extractor()
        row = make_row(
            Id="5",
            **{
                "Published Year": "2021",
                "Title": "Provenance",
                "Authors": "Smith, J.A.",
                "Journal Name": "Analytical Chemistry",
                "Facilities": "ICR Facility",
                "Magnet Systems": "21T ICR",
                "Magnet System Status": "Yes",
                "Data Set Urls": "https://osf.io/ab4zv/",
                "Acknowledgement of the MagLab's NSF core grant": "Yes",
                "Digital Object Identifier": "10.1021/test.1234",
            },
        )
        ext.process_row(row)
        records = [r for recs in ext.entities.values() for r in recs]
        records += ext.relationships
        self.assertTrue(records)
        for r in records:
            for key in ("source_type", "confidence", "extracted_at",
                        "evidence_note", "source_id", "schema_version"):
                self.assertIn(key, r, f"missing {key} in {r}")
            self.assertEqual(r["source_type"], "csv")
            self.assertEqual(r["confidence"], "high")
            self.assertEqual(r["source_id"], "maglab:5")
            self.assertEqual(r["schema_version"], "v1.0")


class TestRelationshipIntegrity(unittest.TestCase):
    def test_relationship_subject_object_exist(self):
        ext = extract_csv.Extractor()
        row = make_row(
            Id="6",
            **{
                "Published Year": "2018",
                "Title": "Integrity",
                "Authors": "Doe, A.; Roe, B.",
                "Journal Name": "Energy Fuels",
                "Facilities": "ICR Facility, NMR Facility",
                "Magnet Systems": "21T ICR",
                "Data Set Urls": "https://osf.io/zz9yy/",
                "Acknowledgement of the MagLab's NSF core grant": "Yes",
                "Digital Object Identifier": "10.1021/ef.9999",
            },
        )
        ext.process_row(row)
        # Build the set of all written entity identifiers (subjects seeded from
        # the publication that was just written this run).
        entity_ids = {}
        for etype, recs in ext.entities.items():
            entity_ids[etype] = {r["identifier"] for r in recs}
        self.assertTrue(ext.relationships)
        for rel in ext.relationships:
            self.assertIn(rel["subject_id"], entity_ids.get(rel["subject_type"], set()),
                          f"orphan subject in {rel}")
            self.assertIn(rel["object_id"], entity_ids.get(rel["object_type"], set()),
                          f"orphan object in {rel}")

    def test_no_id_row_skipped(self):
        ext = extract_csv.Extractor()
        row = make_row(Id="", **{"Title": "No id"})
        processed = ext.process_row(row)
        self.assertFalse(processed)
        self.assertEqual(ext.counts["rows_skipped_no_id"], 1)
        self.assertEqual(ext.counts["rows_processed"], 0)

    def test_idempotency_skips_existing_publication(self):
        ext = extract_csv.Extractor(
            seen_publication_ids={"doi:10.1021/exists.1"}
        )
        row = make_row(
            Id="7",
            **{"Published Year": "2020", "Title": "Existing",
               "Digital Object Identifier": "10.1021/exists.1",
               "Authors": "Lone, A."},
        )
        ext.process_row(row)
        # Publication is skipped...
        self.assertEqual(ext.counts["publications_skipped"], 1)
        self.assertEqual(len(ext.entities["Publication"]), 0)
        # ...but additive entities/relationships are still written.
        self.assertEqual(len(ext.entities["Researcher"]), 1)
        self.assertTrue(any(r["relationship_type"] == "AUTHORED_BY"
                            for r in ext.relationships))


if __name__ == "__main__":
    unittest.main()
