"""Content validation and sensitive data redaction for insurance claims."""

import re

from src.models import ValidationReport


class ContentValidator:
    """Validates extracted fields for completeness and redacts sensitive data patterns."""

    REQUIRED_FIELDS: list[str] = [
        "claimant_name",
        "claim_date",
        "claim_amount",
        "incident_description",
        "policy_number",
    ]

    SENSITIVE_PATTERNS: dict[str, re.Pattern] = {
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
        "bank_account": re.compile(r"\b\d{8,17}\b"),
    }

    def validate(self, extracted: dict[str, str]) -> ValidationReport:
        """Check required fields and redact sensitive patterns. Returns ValidationReport.

        A field is considered missing if it is absent from the dict, empty,
        or set to the default "not found" value.
        """
        missing_fields: list[str] = []
        redacted_fields: list[str] = []

        for field_name in self.REQUIRED_FIELDS:
            value = extracted.get(field_name, "")
            if not value or value.strip() == "" or value.strip().lower() == "not found":
                missing_fields.append(field_name)

        # Redact sensitive patterns in field values
        redacted_extracted = {}
        for key, value in extracted.items():
            redacted_value = self.redact(value)
            if redacted_value != value:
                redacted_fields.append(key)
            redacted_extracted[key] = redacted_value

        # Status is "pass" only when no missing fields and no sensitive patterns remain
        has_sensitive = self._contains_sensitive(redacted_extracted)
        status = "pass" if not missing_fields and not has_sensitive else "fail"

        return ValidationReport(
            status=status,
            missing_fields=missing_fields,
            redacted_fields=redacted_fields,
        )

    def redact(self, text: str) -> str:
        """Replace all sensitive patterns in text with [REDACTED]."""
        result = text
        for pattern in self.SENSITIVE_PATTERNS.values():
            result = pattern.sub("[REDACTED]", result)
        return result

    def _contains_sensitive(self, fields: dict[str, str]) -> bool:
        """Check if any field values still contain sensitive patterns."""
        for value in fields.values():
            for pattern in self.SENSITIVE_PATTERNS.values():
                if pattern.search(value):
                    return True
        return False
