"""Custom exceptions for SecOp."""


class SecOpError(Exception):
    """Base exception for SecOp."""

    def __init__(self, message: str, code: str = "SECOP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(SecOpError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class AuthorizationError(SecOpError):
    """Authorization/permission denied."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, "AUTHZ_ERROR")


class DatabaseError(SecOpError):
    """Database operation failed."""

    def __init__(self, message: str = "Database error"):
        super().__init__(message, "DB_ERROR")


class ScannerError(SecOpError):
    """Scanner operation failed."""

    def __init__(self, message: str = "Scanner error", scanner_type: str = "unknown"):
        self.scanner_type = scanner_type
        super().__init__(message, "SCANNER_ERROR")


class ValidationError(SecOpError):
    """Validation failed."""

    def __init__(self, message: str = "Validation error", field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class ConnectionError(SecOpError):
    """Connection to external service failed."""

    def __init__(self, message: str = "Connection failed", service: str = "unknown"):
        self.service = service
        super().__init__(message, "CONNECTION_ERROR")


class ConfigurationError(SecOpError):
    """Configuration error."""

    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, "CONFIG_ERROR")
