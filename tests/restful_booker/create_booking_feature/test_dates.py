"""
Tests for Restful-Booker API: https://restful-booker.herokuapp.com/
Epic:    'Restful-Booker API'
Feautre: 'Create Booking'
Story:   'Booking dates '
"""
import allure
import pytest

from utils.bdd import given, when, then
from utils.api_helpers.api_request_helper import ApiRequestHelper
from utils.generators import generate_booking

from ..constants import REQ_GET, REQ_CREATE, \
    FIELD_BOOKING_ID, FIELD_BOOKING_DATES


@allure.epic("Restful-Booker API")
@allure.feature("Create Booking")
@allure.story('Booking dates')
class TestCreateBookingDates:
    """Validation of dates fields"""

    # title("Booking date in valid ISO formats")
    @pytest.mark.parametrize("booking_dates", {
        ("2027 05 25", "2027 05 26"),
        ("05/25/2027", "05/26/2027"),
        ("2027-05-25T00:00:00.000Z", "2027-05-26T00:00:00.000Z"),
    }, ids=[
        "YYYY MM DD",
        "MM/DD/YYYY",
        "ISO8601_Datetime"
    ])
    def test_date_format(self,
                         booking_dates: tuple,
                         api_request: ApiRequestHelper,
                         test_id: str,
                         handle_entry_deletion: list):
        """Create booking with valid dates in various formats"""

        allure.dynamic.title(
            f"Booking created with dates in format [{test_id}]"
        )

        dates = {
            "checkin": booking_dates[0],
            "checkout": booking_dates[1]
        }
        expected_dates = {
            "checkin": "2027-05-25",
            "checkout": "2027-05-26",
        }
        with given("booking entry with dates in format "
                   f"{booking_dates}"):
            booking = generate_booking(booking_date=dates)

        with when("CreateBooking request perfromed with 200 OK"):
            created_response = \
                api_request.by_name(REQ_CREATE) \
                .with_json_payload(booking) \
                .perform()

            handle_entry_deletion.append(created_response)

        with then("new booking is created and total price "
                  "is integer"):
            created_response.validates_against_schema() \
                .json.param_equals(
                    f"/booking{FIELD_BOOKING_DATES}",
                    expected_dates
                )

        with then("booking entry is created and may be obtained"):
            booking_id = \
                created_response.get_json_value(FIELD_BOOKING_ID)

            api_request.by_name(REQ_GET) \
                .with_path_params(id=booking_id) \
                .perform() \
                .validates_against_schema() \
                .json.param_equals(
                    FIELD_BOOKING_DATES,
                    expected_dates
                )

    @pytest.mark.xfail(reason="Dates mismatch is not handled")
    @allure.title("No booking on checkout date before checkin date")
    @allure.tag("negative")
    def test_checkin_checkout_dates_order(
        self,
        api_request: ApiRequestHelper,
        handle_entry_deletion: list
    ):
        """If checkout date is before checkin date - validation
        error should be returned and no new booking should be created"""

        dates = {
            'checkin': '2027-01-25',
            'checkout': '2027-01-01'
        }
        with given("booking entry with invalid order of "
                   "checkin/checkout dates"):
            booking = generate_booking(booking_date=dates)

        with when("CreateBooking request perfromed"):
            created_response = \
                api_request.by_name(REQ_CREATE) \
                .with_json_payload(booking) \
                .perform(check_status_code=False)
            handle_entry_deletion.append(created_response)

        with then("response is 400 Bad Request"):
            created_response.status_code_equals(400) \
                .json.params_not_present(FIELD_BOOKING_ID)

    # title("Booking date in invalid formats")
    @pytest.mark.xfail(reason="Invalid formats validation is not handled")
    @pytest.mark.parametrize("booking_dates", {
        ("25.05.2020", "26.05.2020"),
        ("2020-05", "2020-06"),
        ("2020", "2021")
    }, ids=[
        "DD.MM.YYYY",
        "YYYY-MM",
        "YYYY"
    ])
    def test_date_invalid_format_fails(
        self,
        booking_dates: tuple,
        api_request: ApiRequestHelper,
        test_id: str,
        handle_entry_deletion: list
    ):
        """No booking creation if date is in invalid format"""

        allure.dynamic.title(
            f"No booking created with dates in invalid format [{test_id}]"
        )

        dates = {
            "checkin": booking_dates[0],
            "checkout": booking_dates[1]
        }
        with given("booking entry with dates in invalid format "
                   f"{booking_dates}"):
            booking = generate_booking(booking_date=dates)

        with when("CreateBooking request perfromed"):
            created_response = \
                api_request.by_name(REQ_CREATE) \
                .with_json_payload(booking) \
                .perform(check_status_code=False)

            handle_entry_deletion.append(created_response)

        with then("no booking was creaderd and 400 error returned"):
            created_response.status_code_equals(400) \
                .json.params_not_present(FIELD_BOOKING_ID)
