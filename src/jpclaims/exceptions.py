"""Custom exceptions for jpclaims."""


class JPClaimsError(Exception):
    """Base exception for jpclaims."""


class SchemaValidationError(JPClaimsError):
    """Raised when input data fails schema validation."""


class ConfigurationError(JPClaimsError):
    """Raised when YAML or config is invalid."""
