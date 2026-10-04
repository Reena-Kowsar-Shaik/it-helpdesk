"""Custom exceptions for IT Helpdesk System."""

class HelpdeskException(Exception):
    """Base exception class for the application."""
    def __init__(self, message: str = "An application error occurred"):
        self.message = message
        super().__init__(self.message)


class DatabaseConnectionError(HelpdeskException):
    """Raised when connecting to the database fails."""
    def __init__(self, message: str = "Failed to connect to database."):
        super().__init__(message)


class UserAlreadyExistsError(HelpdeskException):
    """Raised when attempting to register a user that already exists."""
    def __init__(self, username_or_email: str):
        super().__init__(f"User with identifier '{username_or_email}' already exists.")


class InvalidLoginError(HelpdeskException):
    """Raised when authentication fails due to bad credentials."""
    def __init__(self, message: str = "Invalid username or password."):
        super().__init__(message)


class TicketNotFoundError(HelpdeskException):
    """Raised when a specified ticket is not found."""
    def __init__(self, ticket_id: int):
        super().__init__(f"Ticket with ID '{ticket_id}' was not found.")


class UnauthorizedAccessError(HelpdeskException):
    """Raised when a user lacks permissions to perform an operation."""
    def __init__(self, action: str = "perform this action"):
        super().__init__(f"You are not authorized to {action}.")


class SLAConfigurationError(HelpdeskException):
    """Raised when an SLA rule or configuration is invalid."""
    def __init__(self, message: str = "Invalid SLA configuration."):
        super().__init__(message)


class EntityNotFoundError(HelpdeskException):
    """Generic entity not found error."""
    def __init__(self, entity_name: str, entity_id: any):
        super().__init__(f"{entity_name} with ID '{entity_id}' not found.")


class ValidationError(HelpdeskException):
    """Raised when domain validation fails."""
    def __init__(self, message: str):
        super().__init__(message)
