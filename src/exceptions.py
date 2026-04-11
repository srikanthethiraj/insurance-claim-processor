"""Exception hierarchy for the Insurance Claim Processor."""


class ClaimProcessorError(Exception):
    """Base exception for all claim processor errors."""


class FileTooLargeError(ClaimProcessorError):
    """Raised when uploaded file exceeds size limit."""


class UnsupportedFormatError(ClaimProcessorError):
    """Raised when file format is not supported."""


class StorageUnavailableError(ClaimProcessorError):
    """Raised when S3 is unreachable."""


class ModelInvocationError(ClaimProcessorError):
    """Raised when Bedrock model invocation fails after retries."""


class TemplateNotFoundError(ClaimProcessorError):
    """Raised when a referenced template does not exist."""


class MissingVariableError(ClaimProcessorError):
    """Raised when a required template variable is not provided."""
