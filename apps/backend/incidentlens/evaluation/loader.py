"""Filesystem loader for validated golden-incident fixtures."""

import json
from pathlib import Path
from typing import Any

from .schemas import (
    EvidenceDocument,
    EvidenceManifest,
    ExpectedAnswer,
    GoldenIncident,
    IncidentMetadata,
    IncidentQuestion,
)


class FixtureLoadError(ValueError):
    """Raised when a fixture file is missing, unreadable, or malformed JSON."""


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        raw_data = path.read_text(encoding="utf-8")
    except OSError as error:
        raise FixtureLoadError(f"could not read fixture file: {path}") from error

    try:
        parsed = json.loads(raw_data)
    except json.JSONDecodeError as error:
        raise FixtureLoadError(f"invalid JSON in fixture file: {path}") from error

    if not isinstance(parsed, dict):
        raise FixtureLoadError(f"fixture JSON must contain an object: {path}")
    return parsed


def _resolve_evidence_path(fixture_root: Path, relative_path: str) -> Path:
    resolved_root = fixture_root.resolve()
    resolved_path = (resolved_root / relative_path).resolve()
    if not resolved_path.is_relative_to(resolved_root):
        raise FixtureLoadError(
            f"evidence path escapes the fixture directory: {relative_path}"
        )
    return resolved_path


def load_golden_incident(fixture_directory: str | Path) -> GoldenIncident:
    """Load and cross-validate one golden incident from a directory."""

    fixture_root = Path(fixture_directory)
    if not fixture_root.is_dir():
        raise FixtureLoadError(f"fixture directory does not exist: {fixture_root}")

    incident = IncidentMetadata.model_validate(
        _read_json_object(fixture_root / "incident.json")
    )
    question = IncidentQuestion.model_validate(
        _read_json_object(fixture_root / "question.json")
    )
    manifest = EvidenceManifest.model_validate(
        _read_json_object(fixture_root / "evidence-manifest.json")
    )
    expected_answer = ExpectedAnswer.model_validate(
        _read_json_object(fixture_root / "ground-truth" / "expected-answer.json")
    )

    evidence_documents: list[EvidenceDocument] = []
    for item in manifest.items:
        evidence_path = _resolve_evidence_path(fixture_root, item.path)
        try:
            content = evidence_path.read_text(encoding="utf-8")
        except OSError as error:
            raise FixtureLoadError(f"could not read evidence file: {evidence_path}") from error

        evidence_documents.append(
            EvidenceDocument(metadata=item, content=content.strip())
        )

    return GoldenIncident(
        incident=incident,
        question=question,
        manifest=manifest,
        evidence=tuple(evidence_documents),
        expected_answer=expected_answer,
    )
