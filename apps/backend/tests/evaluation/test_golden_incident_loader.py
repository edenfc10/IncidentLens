import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from incidentlens.evaluation.loader import FixtureLoadError, load_golden_incident

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SOURCE_FIXTURE = PROJECT_ROOT / "fixtures" / "golden-incidents" / "inc-001"


def copy_fixture(tmp_path: Path) -> Path:
    fixture = tmp_path / "inc-001"
    shutil.copytree(SOURCE_FIXTURE, fixture)
    return fixture


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def test_loads_complete_golden_incident() -> None:
    golden_incident = load_golden_incident(SOURCE_FIXTURE)

    assert golden_incident.incident.id == "INC-001"
    assert golden_incident.question.incident_id == "INC-001"
    assert len(golden_incident.evidence) == 5
    assert golden_incident.evidence[0].metadata.id == "E-001"
    assert "DB_POOL_SIZE" in golden_incident.evidence[0].content


def test_rejects_missing_evidence_file(tmp_path: Path) -> None:
    fixture = copy_fixture(tmp_path)
    (fixture / "evidence" / "e-002-application.log").unlink()

    with pytest.raises(FixtureLoadError, match="could not read evidence file"):
        load_golden_incident(fixture)


def test_rejects_duplicate_evidence_ids(tmp_path: Path) -> None:
    fixture = copy_fixture(tmp_path)
    manifest_path = fixture / "evidence-manifest.json"
    manifest = read_json(manifest_path)
    items = manifest["items"]
    assert isinstance(items, list)
    items[1]["id"] = items[0]["id"]
    write_json(manifest_path, manifest)

    with pytest.raises(ValidationError, match="evidence IDs must be unique"):
        load_golden_incident(fixture)


def test_rejects_ground_truth_leakage(tmp_path: Path) -> None:
    fixture = copy_fixture(tmp_path)
    manifest_path = fixture / "evidence-manifest.json"
    manifest = read_json(manifest_path)
    items = manifest["items"]
    assert isinstance(items, list)
    items[0]["path"] = "ground-truth/expected-answer.json"
    write_json(manifest_path, manifest)

    with pytest.raises(ValidationError, match="ground truth cannot be registered"):
        load_golden_incident(fixture)


def test_rejects_unknown_ground_truth_evidence_id(tmp_path: Path) -> None:
    fixture = copy_fixture(tmp_path)
    expected_path = fixture / "ground-truth" / "expected-answer.json"
    expected = read_json(expected_path)
    expected["required_evidence_ids"] = ["E-999"]
    write_json(expected_path, expected)

    with pytest.raises(ValidationError, match="unknown evidence IDs: E-999"):
        load_golden_incident(fixture)


def test_rejects_mismatched_incident_ids(tmp_path: Path) -> None:
    fixture = copy_fixture(tmp_path)
    question_path = fixture / "question.json"
    question = read_json(question_path)
    question["incident_id"] = "INC-999"
    write_json(question_path, question)

    with pytest.raises(ValidationError, match="same incident ID"):
        load_golden_incident(fixture)
