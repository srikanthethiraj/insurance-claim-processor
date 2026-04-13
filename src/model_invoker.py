"""Model Invoker for the Insurance Claim Processor."""

import random
import time

import boto3
from botocore.exceptions import ClientError

from src.exceptions import ModelInvocationError
from src.models import InvocationResult


class ModelInvoker:
    """Sends prompts to Amazon Bedrock models with retry and latency tracking."""

    def __init__(self, region: str = "us-east-1", max_retries: int = 3) -> None:
        """Initialize Bedrock runtime client with retry configuration."""
        self._client = boto3.client("bedrock-runtime", region_name=region)
        self._max_retries = max_retries

    def invoke(self, prompt: str, model_id: str) -> InvocationResult:
        """Send prompt to Bedrock model using the Converse API.

        Retries up to max_retries on throttling with exponential backoff.
        Raises ModelInvocationError on non-throttle errors or when retries exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            start = time.monotonic()
            try:
                response = self._client.converse(
                    modelId=model_id,
                    messages=[
                        {
                            "role": "user",
                            "content": [{"text": prompt}],
                        }
                    ],
                    inferenceConfig={"maxTokens": 4096},
                )
                latency_ms = (time.monotonic() - start) * 1000
                response_text = response["output"]["message"]["content"][0]["text"]
                return InvocationResult(
                    response_text=response_text,
                    latency_ms=latency_ms,
                    model_id=model_id,
                )
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code", "")
                if error_code == "ThrottlingException" and attempt < self._max_retries:
                    last_error = exc
                    base_delay = 2 ** attempt
                    jitter = random.uniform(0, base_delay * 0.5)
                    time.sleep(base_delay + jitter)
                    continue
                raise ModelInvocationError(
                    f"Model '{model_id}' invocation failed: {exc}"
                ) from exc
            except Exception as exc:
                raise ModelInvocationError(
                    f"Model '{model_id}' invocation failed: {exc}"
                ) from exc

        raise ModelInvocationError(
            f"Model '{model_id}' invocation failed after {self._max_retries} retries: {last_error}"
        )
