"""
Tests for Restful-Booker API: https://restful-booker.herokuapp.com/
Epic:    'Restful-Booker API'
Feautre: 'Get Bookings'
Story:   'Get booking by i'
"""
import pytest
import allure

from utils.bdd import given, when, then
from utils.api_helpers.api_request_helper import ApiRequestHelper
from utils.api_client.models import HTTPMethod

from ..constants import REQ_GET


@allure.epic("Restful-Booker API")
@allure.feature("Get Bookings")
@allure.story('Get booking by id')
class TestGet:
    """Tests related to GetBookingByID request"""

    @allure.title("Get booking by existing ID returns booking entry "
                  "for unauthenticated user")
    def test_get_no_auth(self, api_request: ApiRequestHelper,
                         created_booking: dict):
        """Tests that non-authenticated user can retrieve booking entry
        by existing valid ID"""

        with given("non-authenticated user with "
                   "valid booking ID and booking entry"):
            booking_id = created_booking['id']
            booking_entry = created_booking['booking']

        with when("GET request is made with 200 OK"):
            response = \
                api_request.by_name(REQ_GET) \
                .with_path_params(id=booking_id) \
                .perform()

        with then("booking entry is returned in response"):
            response.headers.are_like() \
                .json.equals(booking_entry)

    @allure.title("Get booking by existing ID returns booking entry "
                  "for authenticared user")
    def test_get_auth(self, api_request: ApiRequestHelper,
                      created_booking: dict):
        """Tests that authenticated user can retrieve booking entry
        by existing valid ID"""

        with given("authenticated user with "
                   "valid booking ID and booking entry"):
            token = created_booking['token']
            booking_id = created_booking['id']
            booking_entry = created_booking['booking']

        with when("GET request is made with 200 OK"):
            response = \
                api_request.by_name(REQ_GET) \
                .with_path_params(id=booking_id) \
                .with_cookies(token) \
                .perform()

        with then("booking entry is returned in response"):
            response.headers.are_like() \
                .json.equals(booking_entry)

    @allure.title("OPTIONS method return headers with allowed methods")
    def test_options_method(self, api_request: ApiRequestHelper):
        """OPTIONS method handled"""
        with given("OPTIONS request with random booking ID"):
            method = HTTPMethod.OPTIONS

        with when("request performed with 200 OK"):
            response = \
                api_request.by_name(REQ_GET) \
                .with_method(method) \
                .with_path_params(id=12345678) \
                .perform()

        with then("response has 'Allow' header "
                  "with list of supporeted methods"):
            response \
                .headers.present("Allow") \
                .headers.header_contains("Allow", "GET")


@allure.epic("Restful-Booker API")
@allure.feature("Get Bookings")
@allure.story('Get booking by id')
@allure.tag('negative')
class TestGetNegative:
    """Negative tests related to GetBookingByID request"""

    @allure.title("Get booking by non-existing ID returns 404 Not Found")
    def test_get_by_non_existig_id(self, api_request: ApiRequestHelper):
        """Get by non-existing ID should be handled and 404 Not Found
        error should be returned"""

        with given("non-existing booking ID"):
            pass

        with when("GET request performed"):
            response = \
                api_request.by_name("GetBooking_NotFound") \
                .perform(check_status_code=False)

        with then("response is 404 Not Found error "
                  "and no booking entry returned"):
            response.status_code_equals() \
                .equals() \
                .headers.are_like()

    @allure.title("Get booking by invalid ID [{booking_id}] returns "
                  "404 Not Found")
    @pytest.mark.parametrize("booking_id", (
        "string",
        "    ",
        -124,
        "null"
    ), ids=["string", "whitespaces", "negative_int", "null"])
    def test_get_by_invalid_id(self, api_request: ApiRequestHelper,
                               booking_id: str):
        """Get by invalid (non-numeric) ID should be handled and 404 Not Found
        error should be returned"""

        with given(f"invalid booking ID = {booking_id}"):
            pass

        with when("GET request performed"):
            response = \
                api_request.by_name("GetBooking_NotFound") \
                .with_path_params(id=booking_id) \
                .perform(check_status_code=False)

        with then("response is 404 Not Found error "
                  "and no booking entry returned"):
            response.status_code_equals() \
                .equals() \
                .headers.are_like()

    @pytest.mark.xfail(reason="Leading integer is always parsed")
    @allure.title("Get booking by existing ID in non-integer format "
                  "{booking_id_format} returns 404 Not Found")
    @pytest.mark.parametrize("booking_id_format", (
        "{id}.0",
        "{id}.0.0.0.rwerrwr",
        "{id}text"
    ))
    def test_get_by_invalid_id_format(
        self, api_request: ApiRequestHelper,
        created_booking: dict,
        booking_id_format: str
    ):
        """Get by invalid (non-numeric) ID should be handled and 404 Not Found
        error should be returned"""

        booking_id = booking_id_format.format(id=created_booking['id'])
        with given(f"invalid booking ID = {booking_id}"):
            pass

        with when("GET request performed"):
            response = \
                api_request.by_name("GetBooking_NotFound") \
                .with_path_params(id=booking_id) \
                .perform(check_status_code=False)

        with then("response is 404 Not Found error "
                  "and no booking entry returned"):
            response.status_code_equals() \
                .equals() \
                .headers.are_like()
