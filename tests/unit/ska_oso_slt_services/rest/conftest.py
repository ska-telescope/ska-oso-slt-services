"""
pytest fixtures to be used by unit tests
"""
import pytest

from ska_oso_slt_services.rest import init_app, get_openapi_spec


@pytest.fixture(scope="module")
def spec():
    """
    Module scoped fixture so $refs are only resolved once
    """
    return get_openapi_spec()


@pytest.fixture()
def test_app(spec):  # pylint: disable=redefined-outer-name
    """
    Fixture to configure a test app instance
    """
    connexion = init_app(spec)
    connexion.app.config.update(
        {
            "TESTING": True,
        }
    )
    yield connexion.app


@pytest.fixture()
def client(test_app):  # pylint: disable=redefined-outer-name
    """
    Create a test client from the app instance, without running a live server
    """
    return test_app.test_client()
