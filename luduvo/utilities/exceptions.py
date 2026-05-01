"""

Contains exceptions used by luduvo.py.

"""

from typing import Optional, List, Dict, Type
from httpx import Response

import logging

logger = logging.getLogger(__name__)


# Generic exceptions


class LuduvoException(Exception):
    """
    Base exception for all of luduvo_api.
    """

    pass


# Other objects


class ResponseError:
    """
    Represents an error returned by a Luduvo server.

    Attributes:
        code: The error code.
        message: The error message.
        user_facing_message: A more simple error message intended for frontend use.
        field: The field causing this error.
        retryable: Whether retrying this exception could suppress this issue.
    """

    def __init__(self, data: dict):
        self.code: int = data["code"]
        self.message: Optional[str] = data.get("message")
        self.user_facing_message: Optional[str] = data.get("userFacingMessage")
        self.field: Optional[str] = data.get("field")
        self.retryable: Optional[str] = data.get("retryable")


# HTTP exceptions
# Exceptions that Luduvo endpoints do not respond with are not included here.


class HTTPException(LuduvoException):
    """
    Exception that's raised when an HTTP request fails.

    Attributes:
        response: The HTTP response object.
        status: The HTTP response status code.
        errors: A list of Luduvo response errors.
    """

    def __init__(self, response: Response, errors: Optional[list] = None):
        """
        Arguments:
            response: The raw response object.
            errors: A list of errors.
        """
        self.response: Response = response
        self.status: int = response.status_code
        self.errors: List[ResponseError]

        if errors:
            self.errors = [ResponseError(data=error_data) for error_data in errors]
        else:
            self.errors = []

        if self.errors:
            error_string = self._generate_string()
            super().__init__(
                f"{response.status_code} {response.reason_phrase}: {response.url}.\n\nErrors:\n{error_string}"
            )
        else:
            super().__init__(
                f"{response.status_code} {response.reason_phrase}: {response.url}"
            )

    def _generate_string(self) -> str:
        parsed_errors = []
        for error in self.errors:
            # Make each error into a parsed string
            parsed_error = f"\t{error.code}: {error.message}"
            error_messages = []

            error.user_facing_message and error_messages.append(
                f"User-facing message: {error.user_facing_message}"
            )
            error.field and error_messages.append(f"Field: {error.field}")
            error.retryable and error_messages.append(f"Retryable: {error.retryable}")

            if error_messages:
                error_message_string = "\n\t\t".join(error_messages)
                parsed_error += f"\n\t\t{error_message_string}"

            parsed_errors.append(parsed_error)

        # Turn the parsed errors into a joined string
        return "\n".join(parsed_errors)


class BadRequest(HTTPException):
    """HTTP exception raised for status code 400."""

    pass


class Unauthorized(HTTPException):
    """HTTP exception raised for status code 401. This usually means you aren't properly authenticated."""


class Forbidden(HTTPException):
    """HTTP exception raised for status code 403."""

    pass


class NotFound(HTTPException):
    """
    HTTP exception raised for status code 404.
    This usually means we have an internal URL issue - please make a GitHub issue about this!
    """

    pass


class TooManyRequests(HTTPException):
    """
    HTTP exception raised for status code 429.
    This means that Luduvo has [ratelimited](https://en.wikipedia.org/wiki/Rate_limiting) you.
    """

    pass


class InternalServerError(HTTPException):
    """
    HTTP exception raised for status code 500.
    """

    pass


_codes_exceptions: Dict[int, Type[HTTPException]] = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    429: TooManyRequests,
    500: InternalServerError,
}


def get_exception_from_status_code(code: int) -> Type[HTTPException]:
    """
    Gets an exception that should be raised instead of the generic HTTPException for this status code.
    """
    exception = _codes_exceptions.get(code) or HTTPException
    logger.debug(
        "Mapped HTTP status code %s to exception %s",
        code,
        exception.__name__,
    )
    return exception


# Exceptions raised for certain Client methods
class ItemNotFound(LuduvoException):
    """
    Raised for invalid items.
    """

    def __init__(self, message: str, response: Optional[Response] = None):
        """
        Arguments:
            response: The raw response object.
        """
        self.response: Optional[Response] = response
        self.status: Optional[int] = response.status_code if response else None
        super().__init__(message)


class UserNotFound(ItemNotFound):
    """
    Raised for invalid user IDs or usernames.
    """

    pass


class PlaceNotFound(ItemNotFound):
    """
    Raised for invalid place IDs.
    """

    pass


class GroupNotFound(ItemNotFound):
    """
    Raised for invalid group IDs.
    """

    pass


class UserNotMemberOfGroup(ItemNotFound):
    """
    Raised for invalid group member IDs.
    """

    pass


class MemberNotBanned(ItemNotFound):
    """
    Raised for invalid banned group member IDs.
    """
