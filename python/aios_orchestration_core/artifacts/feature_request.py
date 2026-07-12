from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class FeatureRequestArtifact:
    """Typed representation of a single feature request created from a strategic opportunity."""

    artifact_version: str
    artifact_id: str
    source_opportunity_number: int
    title: str
    body: str
    priority_score: int
    produced_at: str

    def validate(self) -> None:
        if not self.title.strip():
            raise ValueError("title is required")
        if not self.body.strip():
            raise ValueError("body is required")
        if not (1 <= self.priority_score <= 100):
            raise ValueError("priority_score must be between 1 and 100")
        if self.source_opportunity_number <= 0:
            raise ValueError("source_opportunity_number must be a positive issue number")
        if not self.artifact_id.strip():
            raise ValueError("artifact_id is required")
