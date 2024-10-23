from typing import Optional

from pydantic import BaseModel, ConfigDict


class AppModel(BaseModel):
    """
    Base class for application data models - as distinct from SLT objects
    :param model_config: The configuration for the model
    """

    model_config = ConfigDict(
        extra="forbid", validate_default=True, validate_assignment=True
    )


class ValidationResponse(AppModel):
    """
    :param valid: A boolean indicating whether the input is valid.
    :param messages: A dictionary mapping field names to error messages
    """

    valid: bool
    messages: dict[str, str]


class ErrorResponseTraceback(AppModel):
    """
    :param key: The key of the error
    :param type: The type of the error
    :param full_traceback: The full traceback of the error
    """

    key: str
    type: str
    full_traceback: str


class ErrorDetails(AppModel):
    """
    :param status: The status code of the error
    :param title: The title of the error
    :param detail: The detail of the error
    :param traceback: The traceback of the error
    """

    status: int
    title: str
    detail: str
    traceback: Optional[ErrorResponseTraceback] = None
