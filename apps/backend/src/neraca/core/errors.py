from __future__ import annotations


class DomainError(Exception):
    """Base class for errors that map to a client-facing API response."""

    code = "DOMAIN_ERROR"
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    code = "NOT_FOUND"
    status_code = 404


class DataUnavailableError(DomainError):
    """The requested layer exists but its real data has not been obtained."""

    code = "DATA_UNAVAILABLE"
    status_code = 409


class RoleForbiddenError(DomainError):
    """The selected role may not see this view. This is a UI gate, not authentication."""

    code = "ROLE_FORBIDDEN"
    status_code = 403


class InvalidScenarioError(DomainError):
    code = "INVALID_SCENARIO"
    status_code = 422


class InvalidFeedbackError(DomainError):
    code = "INVALID_FEEDBACK"
    status_code = 422
