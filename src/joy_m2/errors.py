"""Stable domain exceptions for the maintained Joy M2 pipeline."""


class PipelineError(Exception):
    """Base class for maintained pipeline failures."""


class ConfigurationError(PipelineError):
    """Raised when explicit pipeline configuration is invalid."""


class InputError(PipelineError):
    """Base class for unusable pipeline inputs."""


class InputMissingError(InputError):
    """Raised when a required input does not exist."""


class InputFormatError(InputError):
    """Raised when an input cannot be parsed or interpreted."""


class BaselineMismatchError(InputError):
    """Raised when a frozen baseline does not match its contract."""


class AuditBlockedError(PipelineError):
    """Raised when blocking audit issues prevent further processing."""


class DatabaseBuildError(PipelineError):
    """Base class for candidate database build failures."""


class ForeignKeyViolationError(DatabaseBuildError):
    """Raised when candidate database foreign keys are invalid."""


class DatabaseIntegrityError(DatabaseBuildError):
    """Raised when candidate database integrity checks fail."""


class OutputConflictError(PipelineError):
    """Raised when a declared output already exists."""


class PromotionError(PipelineError):
    """Raised when a candidate cannot be promoted safely."""
