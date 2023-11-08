import string
from logging import getLogger
from typing import Any, ClassVar

from fastapi import HTTPException, status

logger = getLogger(__name__)

EXCEPTION_FORMATTER = string.Formatter()


class MoniteAppCreationError(Exception):
    pass


class InternalRequestError(HTTPException):
    def __init__(self, detail: str) -> None:
        # we can use actual detail for logging
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


class FormattableHTTPException(HTTPException):
    """A convenience class for writing readable exceptions.

    class PayableNotFoundException(FormattableHTTPException):
        status_code = status.HTTP_404_NOT_FOUND
        detail = "Payable with ID {id} not found."

    raise PayableNotFoundException(id=1)

    """

    status_code: ClassVar[int]
    detail: ClassVar[str]
    parsed_fields: ClassVar[set[str]]

    def __init__(self, **kwargs: Any):
        extra_kwargs = kwargs.keys() - self.parsed_fields
        if extra_kwargs:
            raise TypeError(f"Got unexpected keyword arguments: {extra_kwargs}")
        detail = self.detail.format(**kwargs)
        super().__init__(status_code=self.status_code, detail=detail)

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if not hasattr(cls, "status_code"):
            raise AttributeError(f"status_code is required when defining {cls.__name__}(FormattableHTTPException)")
        if not hasattr(cls, "detail"):
            raise AttributeError(f"detail is required when defining {cls.__name__}(FormattableHTTPException)")
        cls.parsed_fields = {field for (_, field, _, _) in EXCEPTION_FORMATTER.parse(cls.detail) if field}


class ExternalRequestError(HTTPException):
    pass
