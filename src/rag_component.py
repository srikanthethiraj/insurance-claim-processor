"""RAG Component for the Insurance Claim Processor."""

from typing import Optional

from src.models import EnrichedPromptResult


class PolicyKnowledgeBase:
    """Simple policy knowledge base for retrieving policy context."""

    def __init__(self) -> None:
        self._policies: dict[str, str] = {}

    def add_policy(self, policy_number: str, context: str) -> None:
        """Register policy information."""
        self._policies[policy_number] = context

    def retrieve(self, policy_number: str) -> Optional[str]:
        """Retrieve policy context by policy number. Returns None if not found."""
        return self._policies.get(policy_number)


class RAGComponent:
    """Retrieves policy context and enriches prompts before model invocation."""

    def __init__(self, knowledge_base: PolicyKnowledgeBase) -> None:
        self._knowledge_base = knowledge_base

    def enrich_prompt(self, prompt: str, policy_number: str) -> EnrichedPromptResult:
        """Retrieve policy info and append to prompt.

        Returns EnrichedPromptResult with warning if no policy found.
        """
        policy_context = self._knowledge_base.retrieve(policy_number)

        if policy_context is None:
            return EnrichedPromptResult(
                prompt=prompt,
                policy_found=False,
                warning=f"No policy information found for policy number '{policy_number}'",
            )

        enriched = f"{prompt}\n\nPolicy Context:\n{policy_context}"
        return EnrichedPromptResult(
            prompt=enriched,
            policy_found=True,
        )
