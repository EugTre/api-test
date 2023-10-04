"""
Tests for Restful-Booker API: https://restful-booker.herokuapp.com/
Epic:    'Restful-Booker API'
Feautre: 'Auth Token'
Story:   'Token creation'
"""

import allure
# import pytest

from utils.bdd import given, when, then
from utils.api_helpers.api_request_helper import ApiRequestHelper
# from utils.api_client.models import HTTPMethod

# from .constants import USERNAME, PASSWORD


@allure.epic("Restful-Booker API")
@allure.feature("Create Booking")
@allure.story('New booking may be created')
class TestCreateBooking:
    """Tests related to CreateBooking feature"""

    @allure.title("Non-Authenticated user can create booking")
    def test_create_booking_no_auth(self, api_request: ApiRequestHelper):
        """Non-authenticated user can create bookings new bookings
        with valid params"""

        with given("non-authenticated user with valid request payload"):
            pass

        with when("CreateBooking request perfromed with 200 OK"):
            response = api_request.by_name("CreateBooking") \
                .perform()

        with then("response contains booking id and booking info"):
            response.validates_against_schema() \
                .json.equals()

    @allure.title("Authenticated user can create booking")
    def test_create_booking_auth(self,
                                 api_request: ApiRequestHelper,
                                 auth_token: str):
        """Authenticated user can create bookings new bookings
        with valid params"""

        with given("authenticated user with valid request payload"):
            pass

        with when("CreateBooking request perfromed with 200 OK"):
            response = api_request.by_name("CreateBooking") \
                .with_cookies({"token": auth_token}) \
                .perform()

        with then("response contains booking id and booking info"):
            response.validates_against_schema() \
                .json.equals()


@allure.epic("Restful-Booker API")
@allure.feature("Create Booking")
@allure.story('New booking may be created')
@allure.tag('negative')
class TestCreateBookingNegative:
    """Tests related to CreateBooking feature, negative tests"""

    # title("Missing fields ")