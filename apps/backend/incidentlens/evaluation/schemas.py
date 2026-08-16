"""Validated data contracts for IncidentLens golden incidents."""

from datetime import datetime
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

IncidentId = Annotated[str, Field(pattern=r"^INC-\d{3,}$")]
EvidenceId = Annotated[str, Field(pattern=r"^E-\d{3,}$")]
Severity = Literal["sev-1", "sev-2", "sev-3", "sev-4"]
IncidentStatus = Literal["open", "investigating", "mitigated", "resolved"]
EvidenceSourceType = Literal[
    "alert",
    "deployment",
    "log",
    "metric",
    "repository",
    "runbook",
    "trace",
]


class ContractModel(BaseModel):
    """Base model that rejects unknown fields and accidental mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class IncidentMetadata(ContractModel):
    """Stable metadata describing a single production incident."""

    id: IncidentId
    title: str = Field(min_length=1)
    service: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    severity: Severity
    status: IncidentStatus
    started_at: datetime
    resolved_at: datetime | None = None

    @model_validator(mode="after")
    def resolution_cannot_precede_start(self) -> Self:
        if self.resolved_at is not None and self.resolved_at < self.started_at:
            raise ValueError("resolved_at cannot be earlier than started_at")
        return self


class IncidentQuestion(ContractModel):
    """The investigation question presented to the retrieval system."""

    incident_id: IncidentId
    text: str = Field(min_length=1)


class EvidenceManifestItem(ContractModel):
    """Metadata and local location for one retrievable evidence document."""

    id: EvidenceId
    source_type: EvidenceSourceType
    title: str = Field(min_length=1)
    path: str = Field(min_length=1)
    observed_at: datetime | None

    @field_validator("path")
    @classmethod
    def path_must_be_safe_and_retrievable(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("evidence path must stay inside the fixture directory")
        if "ground-truth" in path.parts:
            raise ValueError("ground truth cannot be registered as retrievable evidence")
        return value


class EvidenceManifest(ContractModel):
    """The complete set of evidence exposed to the retrieval system."""

    incident_id: IncidentId
    items: tuple[EvidenceManifestItem, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def evidence_ids_must_be_unique(self) -> Self:
        evidence_ids = [item.id for item in self.items]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence IDs must be unique")
        return self


class ExpectedAnswer(ContractModel):
    """Hidden ground truth used only to score a generated answer."""

    incident_id: IncidentId
    root_cause_code: str = Field(min_length=1)
    expected_summary: str = Field(min_length=1)
    required_evidence_ids: tuple[EvidenceId, ...] = Field(min_length=1)
    distractor_evidence_ids: tuple[EvidenceId, ...] = ()
    expected_remediation: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def evidence_labels_must_be_consistent(self) -> Self:
        required = set(self.required_evidence_ids)
        distractors = set(self.distractor_evidence_ids)
        if len(required) != len(self.required_evidence_ids):
            raise ValueError("required evidence IDs must be unique")
        if len(distractors) != len(self.distractor_evidence_ids):
            raise ValueError("distractor evidence IDs must be unique")
        if required & distractors:
            raise ValueError("evidence cannot be both required and distracting")
        return self


class EvidenceDocument(ContractModel):
    """One manifest entry together with the text that RAG may retrieve."""

    metadata: EvidenceManifestItem
    content: str = Field(min_length=1)


class GoldenIncident(ContractModel):
    """A complete, internally consistent evaluation scenario."""

    incident: IncidentMetadata
    question: IncidentQuestion
    manifest: EvidenceManifest
    evidence: tuple[EvidenceDocument, ...]
    expected_answer: ExpectedAnswer

    @model_validator(mode="after")
    def references_must_be_consistent(self) -> Self:
        incident_id = self.incident.id
        referenced_incident_ids = {
            self.question.incident_id,
            self.manifest.incident_id,
            self.expected_answer.incident_id,
        }
        if referenced_incident_ids != {incident_id}:
            raise ValueError("all fixture files must reference the same incident ID")

        manifest_ids = {item.id for item in self.manifest.items}
        loaded_ids = {document.metadata.id for document in self.evidence}
        if loaded_ids != manifest_ids or len(self.evidence) != len(self.manifest.items):
            raise ValueError("loaded evidence must exactly match the manifest")

        labelled_ids = set(self.expected_answer.required_evidence_ids) | set(
            self.expected_answer.distractor_evidence_ids
        )
        unknown_ids = labelled_ids - manifest_ids
        if unknown_ids:
            unknown = ", ".join(sorted(unknown_ids))
            raise ValueError(f"ground truth references unknown evidence IDs: {unknown}")

        return self
