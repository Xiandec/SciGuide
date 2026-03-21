"""Exceptions used across the pipeline library."""


class PipelineDomainError(Exception):
    """Base exception for pipeline-related failures."""


class PipelineInitializationError(PipelineDomainError):
    """Raised when infrastructure initialization fails."""


class MissingDependencyError(PipelineInitializationError):
    """Raised when an optional runtime dependency is not installed."""
