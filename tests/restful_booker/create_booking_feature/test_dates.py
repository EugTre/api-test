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
@allure.story('New booking may be created - dates validation')
class TestCreateBookingDates:
    """Validation of dates fields"""

    @allure.title("Booking created with dates in format "
                  "[{test_id}]")
    @pytest.mark.parametrize(*pytest.format_params(
        "test_id, booking_dates",
        ("YYYY MM DD", ("2027 05 25", "2027 05 26")),
        ("MM/DD/YYYY", ("05/25/2027", "05/26/2027")),
        ("ISO8601_Datetime",
         ("2027-05-25T00:00:00.000Z", "2027-05-26T00:00:00.000Z"))
    ))
    def test_date_format(self,
                         test_id, booking_dates: tuple,
                         api_request: ApiRequestHelper,
                         handle_entry_deletion: list):
        """Create booking with valid dates in various formats"""
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

    @pytest.mark.xfail(reason="Dates mismatch is not handled",
                       **pytest.efx)
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

    @pytest.mark.xfail(reason="Invalid formats validation is not handled",
                       **pytest.efx)
    @allure.title("No booking created with dates "
                  "in invalid format [{test_id}]")
    @pytest.mark.parametrize(*pytest.format_params(
        "test_id, booking_dates",
        ("DD.MM.YYYY",  ("25.05.2020", "26.05.2020")),
        ("YYYY-MM",     ("2020-05", "2020-06")),
        ("YYYY",       ("2020", "2021"))
    ))
    def test_date_invalid_format_fails(
        self,
        test_id, booking_dates: tuple,
        api_request: ApiRequestHelper,
        handle_entry_deletion: list
    ):
        """No booking creation if date is in invalid format"""
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
