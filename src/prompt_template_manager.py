"""Prompt Template Manager for the Insurance Claim Processor."""

import re

from src.exceptions import MissingVariableError, TemplateNotFoundError

# Regex to find {variable} placeholders (not escaped)
_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")

# Default templates registered on init
_DEFAULT_EXTRACTION_TEMPLATE = (
    "Extract the following fields from the insurance claim document below.\n"
    "Return ONLY a JSON object with these exact keys:\n"
    "- claimant_name\n"
    "- claim_date\n"
    "- claim_amount\n"
    "- incident_description\n"
    "- policy_number\n\n"
    "If a field cannot be found, set its value to \"not found\".\n\n"
    "Document:\n{document_text}\n\n"
    "Return ONLY the JSON object, no other text."
)

_DEFAULT_SUMMARIZATION_TEMPLATE = (
    "Generate a concise narrative summary (max 300 words) of the following "
    "insurance claim based on the extracted fields:\n\n"
    "{extracted_fields}\n\n"
    "The summary should highlight the key details of the claim."
)


class PromptTemplateManager:
    """Manages named prompt templates with variable substitution."""

    def __init__(self) -> None:
        """Initialize with built-in extraction and summarization templates."""
        self._templates: dict[str, str] = {}
        self.add_template("extraction", _DEFAULT_EXTRACTION_TEMPLATE)
        self.add_template("summarization", _DEFAULT_SUMMARIZATION_TEMPLATE)

    def add_template(self, name: str, template: str) -> None:
        """Register a named template. Template uses {variable} placeholders."""
        self._templates[name] = template

    def render(self, name: str, variables: dict[str, str]) -> str:
        """Render a template by name with provided variables.

        Raises:
            TemplateNotFoundError: If the template name is not registered.
            MissingVariableError: If a required placeholder variable is missing.
        """
        if name not in self._templates:
            raise TemplateNotFoundError(
                f"Template '{name}' not found"
            )

        template = self._templates[name]
        required_vars = set(_PLACEHOLDER_RE.findall(template))
        missing = required_vars - set(variables.keys())

        if missing:
            missing_name = sorted(missing)[0]
            raise MissingVariableError(
                f"Missing required variable '{missing_name}' for template '{name}'"
            )

        return _PLACEHOLDER_RE.sub(
            lambda m: variables[m.group(1)], template
        )

    def list_templates(self) -> list[str]:
        """Return all registered template names."""
        return list(self._templates.keys())
