"""Test configuration for Restful-Booker API"""
import allure
import pytest
from utils.api_client.setup_api_client import setup_api_client
from utils.api_client.simple_api_client import BaseApiClient
from utils.api_helpers.api_request_helper import ApiRequestHelper

from .constants import API_NAME, \
    REQ_AUTH, REQ_CREATE, REQ_DELETE, \
    FIELD_BOOKING_ID, FIELD_BOOKING_INFO


@pytest.fixture(scope='session')
def api_client() -> BaseApiClient:
    '''Returns object inherited from `BaseApiClient` class.

       Actual class and options are selected by given name
       and configured in API config file defined by cmd option `--api-config`
       under the same name
    '''
    return setup_api_client(
        API_NAME,
        pytest.api_config
    )


@allure.title("Get Auth Token")
@pytest.fixture(scope="session")
def auth_token(api_client: BaseApiClient) -> dict:
    """Creates and returns token"""
    return ApiRequestHelper(api_client, track_request_count=False)\
        .by_name(REQ_AUTH)\
        .perform()\
        .get_json(True)


@allure.title("Create New Booking")
@pytest.fixture(scope="session")
def created_booking(api_client: BaseApiClient, auth_token: dict) -> dict:
    """Creates booking"""
    api = ApiRequestHelper(api_client, track_request_count=False)
    booking = api.by_name(REQ_CREATE)\
        .with_cookies(auth_token)\
        .perform()

    prepared = {
        "token": auth_token,
        "id": booking.get_json_value(FIELD_BOOKING_ID),
        "booking": booking.get_json_value(FIELD_BOOKING_INFO)
    }

    yield prepared

    api.by_name(REQ_DELETE) \
        .with_cookies(auth_token) \
        .with_path_params(id=prepared['id']) \
        .perform()


@allure.title("Handle Booking Entry")
@pytest.fixture(scope='session')
def handle_entry(api_client: BaseApiClient, auth_token: dict) -> list:
    """Handles deletion of booking created in the
    test."""
    response_collection = []
    yield response_collection

    # Filter response if it doesn't contain any json
    response_collection = [
        resp
        for resp in response_collection
        if resp.get_json() is not None
    ]

    if not response_collection:
        return

    api = ApiRequestHelper(api_client, track_request_count=False)
    for created_response in response_collection:
        booking_id = created_response.get_json_value(FIELD_BOOKING_ID)
        api.by_name(REQ_DELETE) \
            .with_cookies(auth_token) \
            .with_path_params(id=booking_id) \
            .perform()
