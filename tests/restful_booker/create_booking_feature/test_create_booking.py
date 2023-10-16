"""
Tests for Restful-Booker API: https://restful-booker.herokuapp.com/
Epic:    'Restful-Booker API'
Feautre: 'Create Booking'
Story:   'New booking may be created'
"""
import pytest
import allure

from utils.bdd import given, when, then
from utils.api_helpers.api_request_helper import ApiRequestHelper
from utils.api_client.models import HTTPMethod
from utils.generators import GeneratorsManager
from ..constants import (
    REQ_GET,
    REQ_CREATE,
    FIELD_BOOKING_ID
)


@allure.epic("Restful-Booker API")
@allure.feature("Create Booking")
@allure.story('New booking may be created')
class TestCreateBooking:
    """Tests related to CreateBooking feature"""

    @allure.title("Non-Authenticated user can create booking")
    def test_create_booking_no_auth(self, api_request: ApiRequestHelper,
                                    handle_entry: list,
                                    generator_manager: GeneratorsManager):
        """Non-authenticated user can create new bookings
        with valid params"""

        with given("non-authenticated user with valid request payload"):
            pass

        with when("CreateBooking request perfromed with 200 OK"):
            created_booking_response = \
                api_request.by_name(REQ_CREATE) \
                .perform()

            handle_entry.append(created_booking_response)

        with then("response contains booking id and booking info"):
            created_booking_response \
                .validates_against_schema() \
                .json.equals()

        with then("booking entry is created and may be obtained"):
            booking_id = \
                created_booking_response.get_json_value(FIELD_BOOKING_ID)
            booking_entry = generator_manager.generate(
                "Booking",
                correlation_id="Create_01"
            )

            api_request.by_name(REQ_GET) \
                .with_path_params(id=booking_id) \
                .perform() \
                .validates_against_schema() \
                .json.equals(booking_entry)

    @allure.title("Authenticated user can create booking")
    def test_create_booking_auth(self,
                                 api_request: ApiRequestHelper,
                                 auth_token: str,
                                 handle_entry: list,
                                 generator_manager: GeneratorsManager):
        """Authenticated user can create new bookings
        with valid params"""

        with given("authenticated user with valid request payload"):
            pass

        with when("CreateBooking request perfromed with 200 OK"):
            created_booking_response = \
                api_request.by_name(REQ_CREATE) \
                .with_cookies(auth_token) \
                .perform()

            handle_entry.append(created_booking_response)

        with then("response contains booking id and booking info"):
            created_booking_response \
                .validates_against_schema() \
                .json.equals()

        with then("booking entry is created and may be obtained"):
            booking_id = \
                created_booking_response.get_json_value(FIELD_BOOKING_ID)
            booking_entry = generator_manager.generate(
                "Booking",
                correlation_id="Create_01"
            )

            api_request.by_name(REQ_GET) \
                .with_path_params(id=booking_id) \
                .perform() \
                .validates_against_schema() \
                .json.equals(booking_entry)

    @allure.title("HEAD method returns only headers")
    def test_head_method(self, api_request: ApiRequestHelper):
        """HEAD method handled"""
        with given("HEAD request with no payload"):
            method = HTTPMethod.HEAD
            payload = {}

        with when("request performed with 200 OK"):
            response = \
                api_request.by_name(REQ_CREATE) \
                .with_method(method) \
                .with_json_payload(payload) \
                .perform()

        with then("response has headers "
                  "and empty body"):
            response \
                .is_empty() \
                .headers.header_equals(
                    "Content-Type",
                    "application/json; charset=utf-8"
                )

    @allure.title("OPTIONS method return headers with allowed methods")
    def test_options_method(self, api_request: ApiRequestHelper):
        """OPTIONS method handled"""
        with given("OPTIONS request with no payload"):
            method = HTTPMethod.OPTIONS
            payload = {}

        with when("request performed with 200 OK"):
            response = \
                api_request.by_name(REQ_CREATE) \
                .with_method(method) \
                .with_json_payload(payload) \
                .perform()

        with then("response has 'Allow' header "
                  "with list of supporeted methods"):
            response \
                .headers.present("Allow") \
                .headers.header_contains("Allow", "POST")


@allure.epic("Restful-Booker API")
@allure.feature("Create Booking")
@allure.story('New booking may be created')
@allure.tag('negative')
class TestCreateBookingNegative:
    """Tests related to CreateBooking feature, negative tests"""

    @allure.title("Request with "
                  "unsupported method \"{method}\" is handled")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("method", (
        HTTPMethod.PATCH,
        HTTPMethod.PUT,
        HTTPMethod.DELETE
    ))
    def test_head_method(self, api_request: ApiRequestHelper,
                         method: HTTPMethod,
                         handle_entry: list):
        """Unsupported method should return 400-like error code"""

        with given(f"{method} request with valid payload"):
            pass

        with when("request performed with 404 Not Found"):
            response = \
                api_request.by_name(REQ_CREATE) \
                .with_method(method) \
                .with_expected(status_code=404) \
                .perform()
            handle_entry.append(response)

        with then("response is empty"):
            response.equals('Not Found')
