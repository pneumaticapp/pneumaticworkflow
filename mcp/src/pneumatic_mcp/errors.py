"""Stable public errors; upstream bodies and exception text never leave the
service."""

from dataclasses import dataclass


@dataclass
class CoreError(Exception):
    code: str
    status: int | None = None
    required_scopes: tuple[str, ...] | None = None

    def __str__(self) -> str:
        return self.code


class AuthUnavailable(Exception):
    """The verifier cannot determine token validity; the client should not
    reconnect."""


MESSAGES = {
    "invalid_arguments": (
        "Invalid tool arguments. Check the tool input schema."
    ),
    "unknown_tool": "Unknown tool.",
    "unauthorized": (
        "Authorization expired or was revoked. Reconnect and try again."
    ),
    "insufficient_scope": "This connection does not grant the required scope.",
    "forbidden": (
        "This connection cannot perform the requested action on this object."
    ),
    "not_found": "The requested object is unavailable to this connection.",
    "conflict": ("The request conflicts with current object state."),
    "validation_error": (
        "Core rejected the request. Check field values and "
        "current object state."
    ),
    "rate_limited": "Core is busy. Try again later.",
    "timeout": "Core did not respond within the time limit.",
    "unavailable": "Core is temporarily unavailable.",
    "authorization_unavailable": (
        "The authorization service is temporarily unavailable."
    ),
    "invalid_response": "Core returned an invalid response.",
    "internal_error": "The tool could not be completed.",
}


def public_error(error: CoreError, *, write: bool) -> dict:
    message = MESSAGES.get(error.code, MESSAGES["internal_error"])
    if write and error.code in {
        "timeout",
        "unavailable",
        "invalid_response",
        "internal_error",
    }:
        message += (
            " The outcome may be unknown; check state before "
            "retrying the action."
        )
    return {
        "error": {
            "code": error.code,
            "message": message,
            "retryable": not write
            and error.code
            in {
                "timeout",
                "unavailable",
                "rate_limited",
                "authorization_unavailable",
            },
            **({"status": error.status} if error.status else {}),
            **(
                {"required_scopes": list(error.required_scopes)}
                if error.required_scopes
                else {}
            ),
        }
    }
