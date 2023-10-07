"""
Tests for Restful-Booker API: https://restful-booker.herokuapp.com/
Epic:    'Restful-Booker API'
Feautre: 'Create Booking'
Story:   'Booking price'
"""
import pytest
import allure

from utils.bdd import given, when, then
from utils.api_helpers.api_request_helper import ApiRequestHelper
from utils.generators import generate_booking

from ..constants import REQ_GET, REQ_CREATE, \
    FIELD_BOOKING_ID, FIELD_TOTAL_PRICE


@allure.epic("Restful-Booker API")
@allure.feature("Create Booking")
@allure.story('New booking may be created - price validation')
class TestCreateBookingPrice:
    """Tests related to 'totalprice' field
    of CreateBooking request validation"""

    @allure.title("Booking price should be saved as integer")
    def test_price_as_float(self,
                            api_request: ApiRequestHelper,
                            handle_entry_deletion: list):
        """If booking price is defined as float - it should be
        saved as integer (decimal part omitted)"""

        price = 55.95
        expected_price = 55
        with given("booking entry with price as float number "
                   f"{55.95}"):
            booking = generate_booking(total_price=price)

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
                    f'/booking{FIELD_TOTAL_PRICE}',
                    expected_price
                )

        with then("booking entry is created and may be obtained"):
            booking_id = \
                created_response.get_json_value(FIELD_BOOKING_ID)

            api_request.by_name(REQ_GET) \
                .with_path_params(id=booking_id) \
                .perform() \
                .validates_against_schema() \
                .json.param_equals(
                    FIELD_TOTAL_PRICE,
                    expected_price
                )

    @pytest.mark.xfail(reason="Negative price is not handled",
                       **pytest.efx)
    @allure.title("No booking on negative total price")
    @allure.tag("negative")
    def test_negative_price(self,
                            api_request: ApiRequestHelper,
                            handle_entry_deletion: list):
        """If total price is negative - validation
        error should be returned and no new booking should be created"""

        price = -100
        with given("booking entry with negative total price"):
            booking = generate_booking(total_price=price)

        with when("CreateBooking request perfromed"):
            created_response = \
                api_request.by_name(REQ_CREATE) \
                .with_json_payload(booking) \
                .perform(check_status_code=False)
            handle_entry_deletion.append(created_response)

        with then("response is 400 Bad Request and "
                  "no new booking was created"):
            created_response.status_code_equals(404) \
                .json.params_not_present(FIELD_BOOKING_ID)
