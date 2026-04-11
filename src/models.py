"""Data models for the Insurance Claim Processor."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UploadResult:
    s3_key: str
    bucket: str
    timestamp: str


@dataclass
class ExtractedFields:
    claimant_name: str = "not found"
    claim_date: str = "not found"
    claim_amount: str = "not found"
    incident_description: str = "not found"
    policy_number: str = "not found"


@dataclass
class ValidationReport:
    status: str  # "pass" or "fail"
    missing_fields: list[str] = field(default_factory=list)
    redacted_fields: list[str] = field(default_factory=list)


@dataclass
class InvocationResult:
    response_text: str
    latency_ms: float
    model_id: str


@dataclass
class ClaimSummary:
    extracted_fields: ExtractedFields
    narrative_summary: Optional[str] = None
    validation: Optional[ValidationReport] = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class ModelResult:
    model_id: str
    response_text: Optional[str] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None


@dataclass
class ComparisonReport:
    results: list[ModelResult] = field(default_factory=list)


@dataclass
class EnrichedPromptResult:
    prompt: str
    policy_found: bool
    warning: Optional[str] = None


@dataclass
class FeedbackEntry:
    summary_id: str
    rating: int  # 1-5
    comment: str = ""
    timestamp: str = ""
