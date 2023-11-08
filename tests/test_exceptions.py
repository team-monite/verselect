import pytest

from verselect import create_app
from verselect.exceptions import FormattableHTTPException
from tests._resources.app_with_duplicate_schemas import router


def test__add_header_route__duplicate_openapi_schema_names__error(caplog: pytest.LogCaptureFixture):
    app = create_app()
    app.add_header_versioned_routers(
        router,
        header_value="2022-01-01",
    )

    assert caplog.records[-1].name == "verselect.apps"
    assert (
        caplog.records[-1].message
        == "The server cannot start because there are duplicate schema names:\nMySchema in the following modules: ['tests._resources.app_with_duplicate_schemas.create_schemas', 'tests._resources.app_with_duplicate_schemas.update_schemas']; \nPlease remove or rename the duplicate schema(s) to ensure unique schema names across all modules.\n\nTo fix this error, you can:\n- Rename duplicate schemas to ensure that each schema has a unique name across all modules.\n- Remove duplicate schemas if they are not required for your application or can be replaced\nby other existing schemas."  # noqa: E501
    )


async def test__formattable_exception():
    class TestException(FormattableHTTPException):
        status_code = 200
        detail = "test {id}"

    with pytest.raises(TestException) as e:
        raise TestException(id=1)

    assert e.value.detail == "test 1"


async def test__formattable_exception__no_detail__error():
    with pytest.raises(AttributeError):

        class TestException(FormattableHTTPException):
            status_code = 200


async def test__formattable_exception__no_status_code__error():
    with pytest.raises(AttributeError):

        class TestException(FormattableHTTPException):
            detail = "test"


async def test__formattable_exception__not_enough_args__error():
    class TestException(FormattableHTTPException):
        status_code = 200
        detail = "test {id}"

    with pytest.raises(KeyError, match="id"):
        raise TestException


async def test__formattable_exception__too_many_args__error():
    class TestException(FormattableHTTPException):
        status_code = 200
        detail = "test {id}"

    with pytest.raises(TypeError, match="Got unexpected keyword arguments: {'extra'}"):
        raise TestException(id=1, extra=2)
