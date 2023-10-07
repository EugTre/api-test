"""Test configuration for Restful-Booker API"""
import pytest
from utils.api_client.setup_api_client import setup_api_client
from utils.api_client.simple_api_client import SimpleApiClient
from utils.api_helpers.api_request_helper import ApiRequestHelper

from .constants import API_NAME, \
    REQ_AUTH, REQ_CREATE, REQ_DELETE, \
    FIELD_BOOKING_ID, FIELD_BOOKING_INFO


@pytest.fixture(scope='session')
def api_client() -> SimpleApiClient:
    '''Returns object inherited from `BaseApiClient` class.

       Actual class and options are selected by given name
       and configured in API config file defined by cmd option `--api-config`
       under the same name
    '''
    return setup_api_client(
        API_NAME,
        pytest.api_config
    )


@pytest.fixture()
def auth_token(api_request: ApiRequestHelper) -> dict:
    """Creates and returns token"""
    response = api_request.by_name(REQ_AUTH).perform()
    return response.get_json(True)


@pytest.fixture
def created_booking(api_request: ApiRequestHelper) -> dict:
    """Creates booking"""
    response = api_request.by_name(REQ_AUTH).perform()
    token = response.get_json(True)
    booking = api_request.by_name(REQ_CREATE)\
        .with_cookies(token).perform()

    prepared = {
        "token": token,
        "id": booking.get_json_value(FIELD_BOOKING_ID),
        "booking": booking.get_json_value(FIELD_BOOKING_INFO)
    }

    yield prepared

    api_request.by_name(REQ_DELETE) \
        .with_cookies(token) \
        .with_path_params(id=prepared['id']) \
        .perform()


@pytest.fixture
def handle_entry_deletion(api_request: ApiRequestHelper) -> list:
    """Handles deletion of booking created in the
    test."""
    response_collection = []
    yield response_collection

    # Filter response if it doesn't contain any json (e.g.
    # failed request)
    response_collection = [
        resp
        for resp in response_collection
        if resp.get_json() is not None
    ]

    if not response_collection:
        return

    auth = api_request.by_name(REQ_AUTH).perform()
    for created_response in response_collection:
        booking_id = created_response.get_json_value(FIELD_BOOKING_ID)
        api_request.by_name(REQ_DELETE) \
            .with_cookies(auth.get_json(True)) \
            .with_path_params(id=booking_id) \
            .perform()
