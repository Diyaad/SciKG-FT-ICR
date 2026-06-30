"""
Tests for scripts/02c_extract_rawfiles.py (SciKG pipeline stage 2c — RAW files).

Covers:
- Sample identifier: same key for files with matching sample fields, null
  fields skipped, distinct key when fields differ
- Instrument / Software dedupe: shared values collapse to a single node
- no ANALYZED_IN relationship is ever produced
- provenance integrity (six keys on every record, entity and relationship)
- run_number is preserved as an int
- per-entity provenance source_type matches the task spec

Standard library only (unittest). The module under test has a digit-prefixed
filename, so it is loaded by path via importlib. The Extractor runs purely in
memory, so these tests touch the filesystem only to read the module itself.
"""

import importlib.util
import unittest
from pathlib import Path

# --- Load scripts/02c_extract_rawfiles.py by path (name starts with a digit) -
_MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "02c_extract_rawfiles.py"
_spec = importlib.util.spec_from_file_location("extract_rawfiles", _MODULE_PATH)
extract_rawfiles = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(extract_rawfiles)


def make_record(filename, fm=None, instrument_name="LTQ Orbitrap Velos",
                instrument_model="LTQ FT Ultra", software_name="Xcalibur",
                software_version="2.7.0 SP2"):
    """Build a minimal enriched-FOXDEN record dict, shaped like the real files."""
    filename_metadata = {
        "operator_initials": "DSB",
        "operator_name": "David S. Butcher",
        "date_acquired": "2019-06-12",
        "sample_organism_strain": "MG1655",
        "sample_state": "lysate",
        "sample_growth_medium": None,
        "sample_growth_date": None,
        "bioreplicate_id": None,
        "sample_prep_method": None,
        "fractionation_method": "GELFrEE",
        "fraction_id": "GF01",
        "experimental_parameters": "screen",
        "run_number": 1,
    }
    if fm:
        filename_metadata.update(fm)
    instrument = {}
    if instrument_name is not None:
        instrument = {"name": instrument_name, "model": instrument_model}
    software = {}
    if software_name is not None:
        software = {"name": software_name, "softwareVersion": software_version}
    return {
        "filename": filename,
        "filepath": f"\\\\zdrive\\icr\\{filename}",
        "sha256_hash": "0" * 64,
        "dateCreated": "2021-06-09T12:44:05",
        "dateModified": "2019-06-12T15:16:00",
        "filename_metadata": filename_metadata,
        "user_metadata": {
            "hasPart": [{"instrument": instrument, "software": software}],
        },
    }


def run_extractor(records, existing_ids=None):
    """Run the in-memory Extractor over a list of (path_name, record) tuples."""
    base = {etype: set() for etype in extract_rawfiles.ENTITY_FILES}
    base["Researcher"] = {extract_rawfiles.OPERATOR_RESEARCHER_ID}
    if existing_ids:
        base.update(existing_ids)
    ex = extract_rawfiles.Extractor(existing_ids=base)
    for name, rec in records:
        ex._cur_source_id = f"rawfiles_enriched:{name}"
        ex._cur_evidence = f"Extracted from {name}"
        # Drive the same per-file logic process_file() uses, but from an
        # in-memory record (process_file reads from disk).
        ex.counts["files_processed"] += 1
        _extract_from_record(ex, name, rec)
    return ex


def _extract_from_record(ex, name, record):
    """Mirror of process_file()'s body operating on an in-memory record."""
    fm = record.get("filename_metadata") or {}
    hp = extract_rawfiles.first_haspart(record)
    instrument = hp.get("instrument") or {}
    software = hp.get("software") or {}
    filename = extract_rawfiles.clean(record.get("filename"))
    rawfile_id = f"rawfile:{filename}"

    props = {k: extract_rawfiles.clean(fm.get(k))
             for k in extract_rawfiles.FILENAME_METADATA_FIELDS}
    props.update({
        "filename": filename,
        "original_filepath": extract_rawfiles.clean(record.get("filepath")),
        "sha256_hash": extract_rawfiles.clean(record.get("sha256_hash")),
        "date_file_created": extract_rawfiles.clean(record.get("dateCreated")),
        "date_file_modified": extract_rawfiles.clean(record.get("dateModified")),
        "instrument_name_raw": extract_rawfiles.clean(instrument.get("name")),
        "instrument_model_raw": extract_rawfiles.clean(instrument.get("model")),
        "acquisition_software_name": extract_rawfiles.clean(software.get("name")),
        "acquisition_software_version": extract_rawfiles.clean(
            software.get("softwareVersion")),
    })
    ex.add_entity("RawDataFile", rawfile_id, props,
                  extract_rawfiles.SOURCE_RAWFILE, "rawfiles_written")

    sample_id = extract_rawfiles.sample_identifier(fm)
    sample_props = {k: extract_rawfiles.clean(fm.get(k))
                    for k in extract_rawfiles.SAMPLE_IDENTITY_FIELDS}
    ex.add_entity("Sample", sample_id, sample_props,
                  extract_rawfiles.SOURCE_SAMPLE, "samples_written")
    ex.add_relationship("CONTAINS_SAMPLE", rawfile_id, sample_id, "Sample",
                        extract_rawfiles.SOURCE_SAMPLE)
    ex.add_relationship("OPERATED_BY", rawfile_id,
                        extract_rawfiles.OPERATOR_RESEARCHER_ID, "Researcher",
                        extract_rawfiles.SOURCE_SAMPLE)

    instrument_name = extract_rawfiles.clean(instrument.get("name"))
    if instrument_name:
        instrument_id = f"instrument:raw:{extract_rawfiles.slugify(instrument_name)}"
        ex.add_entity("Instrument", instrument_id, {
            "name_raw": instrument_name,
            "model_raw": extract_rawfiles.clean(instrument.get("model")),
            "canonical_name": None,
            "psi_ms_id": None,
        }, extract_rawfiles.SOURCE_INSTRUMENT, "instruments_written")
        ex.add_relationship("COLLECTED_ON", rawfile_id, instrument_id,
                            "Instrument", extract_rawfiles.SOURCE_INSTRUMENT)

    software_name = extract_rawfiles.clean(software.get("name"))
    if software_name:
        software_version = extract_rawfiles.clean(software.get("softwareVersion"))
        software_id = (f"software:{extract_rawfiles.slugify(software_name)}"
                       f":{extract_rawfiles.slugify(software_version)}")
        ex.add_entity("Software", software_id, {
            "name": software_name,
            "version": software_version,
        }, extract_rawfiles.SOURCE_SOFTWARE, "software_written")
        ex.add_relationship("ACQUIRED_WITH", rawfile_id, software_id,
                            "Software", extract_rawfiles.SOURCE_SOFTWARE)


class TestSampleIdentifier(unittest.TestCase):
    def test_matching_sample_fields_share_identifier(self):
        a = make_record("a.raw")
        b = make_record("b.raw")  # identical sample fields
        self.assertEqual(
            extract_rawfiles.sample_identifier(a["filename_metadata"]),
            extract_rawfiles.sample_identifier(b["filename_metadata"]),
        )

    def test_null_fields_skipped_in_key(self):
        # organism=MG1655, state=lysate, medium/date null -> two parts only.
        fm = make_record("a.raw")["filename_metadata"]
        self.assertEqual(
            extract_rawfiles.sample_identifier(fm), "sample:mg1655_lysate")

    def test_distinct_fields_distinct_identifier(self):
        a = make_record("a.raw")["filename_metadata"]
        b = make_record("b.raw", fm={
            "sample_organism_strain": None, "sample_state": None,
            "sample_growth_medium": "M9", "sample_growth_date": "2019-04-04",
        })["filename_metadata"]
        self.assertNotEqual(
            extract_rawfiles.sample_identifier(a),
            extract_rawfiles.sample_identifier(b))
        self.assertEqual(
            extract_rawfiles.sample_identifier(b), "sample:m9_2019_04_04")

    def test_real_data_three_sample_nodes(self):
        records = [
            ("f1.raw", make_record("f1.raw")),  # mg1655_lysate
            ("f2.raw", make_record("f2.raw")),  # mg1655_lysate (dup)
            ("f3.raw", make_record("f3.raw", fm={
                "sample_organism_strain": None, "sample_state": None,
                "sample_growth_medium": "M9", "sample_growth_date": "2019-04-04",
            })),
            ("f4.raw", make_record("f4.raw", fm={
                "sample_growth_medium": "M9", "sample_growth_date": "2019-04-04",
            })),  # mg1655_lysate_m9_2019_04_04
        ]
        ex = run_extractor(records)
        self.assertEqual(ex.counts["samples_written"], 3)


class TestDedupe(unittest.TestCase):
    def test_instrument_and_software_dedupe(self):
        records = [(f"f{i}.raw", make_record(f"f{i}.raw")) for i in range(5)]
        ex = run_extractor(records)
        self.assertEqual(ex.counts["instruments_written"], 1)
        self.assertEqual(ex.counts["software_written"], 1)
        self.assertEqual(ex.counts["rawfiles_written"], 5)

    def test_instrument_skipped_when_already_in_output(self):
        existing = {"Instrument": {"instrument:raw:ltq_orbitrap_velos"}}
        ex = run_extractor([("f1.raw", make_record("f1.raw"))],
                           existing_ids=existing)
        self.assertEqual(ex.counts["instruments_written"], 0)
        # but the COLLECTED_ON edge is still produced and resolves
        rels = [r for r in ex.relationships if r["relationship_type"] == "COLLECTED_ON"]
        self.assertEqual(len(rels), 1)


class TestRelationships(unittest.TestCase):
    def test_no_analyzed_in_relationship(self):
        records = [(f"f{i}.raw", make_record(f"f{i}.raw")) for i in range(5)]
        ex = run_extractor(records)
        types = {r["relationship_type"] for r in ex.relationships}
        self.assertNotIn("ANALYZED_IN", types)
        self.assertEqual(types, {"CONTAINS_SAMPLE", "OPERATED_BY",
                                 "COLLECTED_ON", "ACQUIRED_WITH"})

    def test_operator_uses_existing_researcher_id(self):
        ex = run_extractor([("f1.raw", make_record("f1.raw"))])
        op = [r for r in ex.relationships if r["relationship_type"] == "OPERATED_BY"]
        self.assertEqual(len(op), 1)
        self.assertEqual(op[0]["object_id"], "researcher:butcher_d_2024")

    def test_four_relationships_per_rawfile(self):
        ex = run_extractor([("f1.raw", make_record("f1.raw"))])
        self.assertEqual(len(ex.relationships), 4)

    def test_no_instrument_means_no_collected_on(self):
        rec = make_record("f1.raw", instrument_name=None)
        ex = run_extractor([("f1.raw", rec)])
        types = {r["relationship_type"] for r in ex.relationships}
        self.assertNotIn("COLLECTED_ON", types)
        self.assertEqual(ex.counts["instruments_written"], 0)


class TestProvenance(unittest.TestCase):
    def test_six_provenance_keys_on_every_record(self):
        records = [(f"f{i}.raw", make_record(f"f{i}.raw")) for i in range(3)]
        ex = run_extractor(records)
        all_records = [r for recs in ex.entities.values() for r in recs]
        all_records += ex.relationships
        self.assertTrue(all_records)
        for r in all_records:
            self.assertTrue(
                extract_rawfiles.PROVENANCE_KEYS.issubset(r),
                msg=f"missing provenance keys: {r}")

    def test_source_type_per_entity(self):
        ex = run_extractor([("f1.raw", make_record("f1.raw"))])
        got = {etype: {r["source_type"] for r in recs}
               for etype, recs in ex.entities.items() if recs}
        self.assertEqual(got["RawDataFile"], {"merged_csv_foxden"})
        self.assertEqual(got["Sample"], {"manual_annotation"})
        self.assertEqual(got["Instrument"], {"fisher_py"})
        self.assertEqual(got["Software"], {"fisher_py"})

    def test_all_identifiers_well_formed(self):
        records = [(f"f{i}.raw", make_record(f"f{i}.raw")) for i in range(3)]
        ex = run_extractor(records)
        all_records = [r for recs in ex.entities.values() for r in recs]
        for r in all_records:
            self.assertRegex(r["identifier"], extract_rawfiles.ID_RE)
        for r in ex.relationships:
            self.assertRegex(r["subject_id"], extract_rawfiles.ID_RE)
            self.assertRegex(r["object_id"], extract_rawfiles.ID_RE)


class TestRunNumberInt(unittest.TestCase):
    def test_run_number_is_int(self):
        ex = run_extractor([("f1.raw", make_record("f1.raw", fm={"run_number": 2}))])
        raw = ex.entities["RawDataFile"][0]
        self.assertIsInstance(raw["properties"]["run_number"], int)
        self.assertEqual(raw["properties"]["run_number"], 2)


if __name__ == "__main__":
    unittest.main()
