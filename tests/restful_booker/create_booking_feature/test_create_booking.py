"""
Tests for Restful-Booker API: https://restful-booker.herokuapp.com/
Epic:    'Restful-Booker API'
Feautre: 'Auth Token'
Story:   'Token creation'
"""

import allure
import pytest

from utils.bdd import given, when, then
from utils.api_helpers.api_request_helper import ApiRequestHelper
from utils.generators import ParamsGenerator
# from utils.api_client.models import HTTPMethod

from ..constants import REQ_GET, REQ_CREATE, \
    FIELD_BOOKING_ID, FIELD_BOOKING_INFO, FIELD_ADDITIONAL_NEEDS
from .constants import CREATE_REQUEST_PAYLOAD_REFERENCE as PAYLOAD_REF


@allure.epic("Restful-Booker API")
@allure.feature("Create Booking")
@allure.story('New booking may be created')
class TestCreateBooking:
    """Tests related to CreateBooking feature"""

    @allure.title("Non-Authenticated user can create booking")
    def test_create_booking_no_auth(self, api_request: ApiRequestHelper,
                                    handle_entry_deletion: list):
        """Non-authenticated user can create bookings new bookings
        with valid params"""

        with given("non-authenticated user with valid request payload"):
            pass

        with when("CreateBooking request perfromed with 200 OK"):
            created_booking_response = \
                api_request.by_name(REQ_CREATE) \
                .perform()

            handle_entry_deletion.append(created_booking_response)

        with then("response contains booking id and booking info"):
            created_booking_response \
                .validates_against_schema() \
                .json.equals()

        with then("booking entry is created and may be obtained"):
            booking_id = \
                created_booking_response.get_json_value(FIELD_BOOKING_ID)
            booking_entry = \
                created_booking_response.get_json_value(FIELD_BOOKING_INFO)

            api_request.by_name(REQ_GET) \
                .with_path_params(id=booking_id) \
                .perform() \
                .validates_against_schema() \
                .json.equals(booking_entry)

    @allure.title("Authenticated user can create booking")
    def test_create_booking_auth(self,
                                 api_request: ApiRequestHelper,
                                 auth_token: str,
                                 handle_entry_deletion: list):
        """Authenticated user can create bookings new bookings
        with valid params"""

        with given("authenticated user with valid request payload"):
            pass

        with when("CreateBooking request perfromed with 200 OK"):
            created_booking_response = \
                api_request.by_name(REQ_CREATE) \
                .with_cookies(auth_token) \
                .perform()

            handle_entry_deletion.append(created_booking_response)

        with then("response contains booking id and booking info"):
            created_booking_response \
                .validates_against_schema() \
                .json.equals()

        with then("booking entry is created and may be obtained"):
            booking_id = \
                created_booking_response.get_json_value(FIELD_BOOKING_ID)
            booking_entry = \
                created_booking_response.get_json_value(FIELD_BOOKING_INFO)

            api_request.by_name(REQ_GET) \
                .with_path_params(id=booking_id) \
                .perform() \
                .validates_against_schema() \
                .json.equals(booking_entry)


@allure.epic("Restful-Booker API")
@allure.feature("Create Booking")
@allure.story('New booking may be created')
@allure.tag('negative')
class TestCreateBookingNegative:
    """Tests related to CreateBooking feature, negative tests"""

    # title("Empty/null fields")
    @pytest.mark.parametrize(
        "payload",
        ParamsGenerator.get_empty_null_fields(
            PAYLOAD_REF,
            skip=[FIELD_ADDITIONAL_NEEDS]
        )
    )
    def test_empty_fields(self, api_request: ApiRequestHelper,
                          payload: dict, test_id: str,
                          handle_entry_deletion: dict):
        """Entry creation fails if field is empty string or null"""

        allure.dynamic.title(
            f"No booking creation on empty fields [{test_id}]"
        )

        with given(f'incomplete payload with {test_id}'):
            pass

        with when("POST request performed with given payload"):
            created_response = \
                api_request.by_name(REQ_CREATE) \
                .with_json_payload(payload) \
                .perform(check_status_code=False)

            handle_entry_deletion.append(created_response)

        with then("response is 400 Bad Request"):
            created_response.status_code_equals(400) \
                .json.params_not_present(FIELD_BOOKING_ID)

    # title("Missing fields ")
