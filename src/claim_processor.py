"""Claim Processor orchestrator for the Insurance Claim Processor."""

import json
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

from src.content_validator import ContentValidator
from src.exceptions import (
    FileTooLargeError,
    ModelInvocationError,
    StorageUnavailableError,
    UnsupportedFormatError,
)
from src.model_invoker import ModelInvoker
from src.models import (
    ClaimSummary,
    ComparisonReport,
    ExtractedFields,
    ModelResult,
    UploadResult,
)
from src.prompt_template_manager import PromptTemplateManager
from src.rag_component import PolicyKnowledgeBase, RAGComponent

_SUPPORTED_FORMATS = {".pdf", ".png", ".jpeg", ".jpg", ".txt"}
_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class ClaimProcessor:
    """Orchestrates document upload, extraction, summarization, and comparison."""

    def __init__(
        self,
        s3_bucket: str,
        model_id: str,
        region: str = "us-east-1",
        knowledge_base: PolicyKnowledgeBase | None = None,
    ) -> None:
        self._s3_bucket = s3_bucket
        self._model_id = model_id
        self._s3_client = boto3.client("s3", region_name=region)
        self._template_manager = PromptTemplateManager()
        self._model_invoker = ModelInvoker(region=region)
        self._content_validator = ContentValidator()
        self._rag = RAGComponent(knowledge_base or PolicyKnowledgeBase())

    def upload_document(self, file_path: str) -> UploadResult:
        """Upload a claim document to S3.

        Validates format and size, then uploads.
        Returns UploadResult with s3_key, bucket, and timestamp.
        """
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in _SUPPORTED_FORMATS:
            raise UnsupportedFormatError(
                f"Unsupported file format '{ext}'. Supported: {', '.join(sorted(_SUPPORTED_FORMATS))}"
            )

        file_size = os.path.getsize(file_path)
        if file_size > _MAX_FILE_SIZE:
            raise FileTooLargeError(
                f"File size {file_size} bytes exceeds 10 MB limit"
            )

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = os.path.basename(file_path)
        s3_key = f"claims/{timestamp}/{filename}"

        try:
            with open(file_path, "rb") as f:
                self._s3_client.put_object(
                    Bucket=self._s3_bucket, Key=s3_key, Body=f.read()
                )
        except (ClientError, EndpointConnectionError, ConnectionError) as exc:
            raise StorageUnavailableError(
                f"Failed to upload to S3: {exc}"
            ) from exc

        return UploadResult(s3_key=s3_key, bucket=self._s3_bucket, timestamp=timestamp)

    def process_document(self, s3_key: str) -> ClaimSummary:
        """Full pipeline: extract → validate → enrich → summarize.

        Returns ClaimSummary with extracted fields, narrative summary, and validation.
        On summarization failure, returns extracted fields with a warning.
        """
        warnings: list[str] = []

        # Retrieve document text from S3
        response = self._s3_client.get_object(Bucket=self._s3_bucket, Key=s3_key)
        document_text = response["Body"].read().decode("utf-8")

        # Render extraction prompt and invoke model
        extraction_prompt = self._template_manager.render(
            "extraction", {"document_text": document_text}
        )

        # Enrich with RAG — need a first-pass policy number extraction
        # We'll do a simple parse after extraction; enrich the extraction prompt first
        # with any policy number hint from the document text
        enriched = self._rag.enrich_prompt(extraction_prompt, self._extract_policy_hint(document_text))
        if enriched.warning:
            warnings.append(enriched.warning)

        extraction_result = self._model_invoker.invoke(enriched.prompt, self._model_id)

        # Parse extracted fields
        extracted_fields = self._parse_extracted_fields(extraction_result.response_text)

        # Validate extracted fields
        fields_dict = {
            "claimant_name": extracted_fields.claimant_name,
            "claim_date": extracted_fields.claim_date,
            "claim_amount": extracted_fields.claim_amount,
            "incident_description": extracted_fields.incident_description,
            "policy_number": extracted_fields.policy_number,
        }
        validation = self._content_validator.validate(fields_dict)

        # Summarization
        try:
            summary_prompt = self._template_manager.render(
                "summarization", {"extracted_fields": json.dumps(fields_dict, indent=2)}
            )
            summary_result = self._model_invoker.invoke(summary_prompt, self._model_id)
            narrative = self._truncate_to_word_limit(summary_result.response_text, 300)
        except (ModelInvocationError, Exception) as exc:
            warnings.append(f"Summarization failed: {exc}")
            narrative = None

        return ClaimSummary(
            extracted_fields=extracted_fields,
            narrative_summary=narrative,
            validation=validation,
            warnings=warnings,
        )

    def _extract_policy_hint(self, text: str) -> str:
        """Try to find a policy number pattern in raw text."""
        import re
        match = re.search(r"(?:policy\s*(?:number|#|no\.?)?[\s:]*)([\w-]+)", text, re.IGNORECASE)
        return match.group(1) if match else ""

    def _parse_extracted_fields(self, response_text: str) -> ExtractedFields:
        """Parse model response into ExtractedFields, defaulting missing to 'not found'."""
        import re
        fields = ExtractedFields()
        # Strip markdown code blocks (```json ... ``` or ``` ... ```)
        cleaned = re.sub(r"```(?:json)?\s*", "", response_text).strip()
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                # Normalize keys: try snake_case and Title Case variants
                def get(d, *keys):
                    for k in keys:
                        if k in d and d[k]:
                            return d[k]
                    return "not found"
                fields.claimant_name = get(data, "claimant_name", "Claimant Name", "claimant")
                fields.claim_date = get(data, "claim_date", "Claim Date", "date")
                fields.claim_amount = get(data, "claim_amount", "Claim Amount", "amount")
                fields.incident_description = get(data, "incident_description", "Incident Description", "description")
                fields.policy_number = get(data, "policy_number", "Policy Number", "policy")
        except (json.JSONDecodeError, TypeError):
            pass  # Return defaults
        return fields

    def compare_models(self, s3_key: str, model_ids: list[str]) -> ComparisonReport:
        """Run extraction+summarization across multiple models and return comparison.

        On model failure, records error and continues with remaining models.
        """
        response = self._s3_client.get_object(Bucket=self._s3_bucket, Key=s3_key)
        document_text = response["Body"].read().decode("utf-8")

        prompt = self._template_manager.render(
            "extraction", {"document_text": document_text}
        )

        results: list[ModelResult] = []
        for mid in model_ids:
            try:
                invocation = self._model_invoker.invoke(prompt, mid)
                results.append(
                    ModelResult(
                        model_id=mid,
                        response_text=invocation.response_text,
                        latency_ms=invocation.latency_ms,
                    )
                )
            except ModelInvocationError as exc:
                results.append(ModelResult(model_id=mid, error=str(exc)))

        return ComparisonReport(results=results)

    @staticmethod
    def _truncate_to_word_limit(text: str, max_words: int) -> str:
        """Truncate text to max_words."""
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words])
