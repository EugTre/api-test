"""
Tests for Restful-Booker API: https://restful-booker.herokuapp.com/
Epic:    'Restful-Booker API'
Feautre: 'Create Booking'
Story:   'Input data validation'
"""

import allure
import pytest

from utils.bdd import given, when, then
from utils.api_helpers.api_request_helper import ApiRequestHelper
from utils.generators import ParamsGenerator

from ..constants import REQ_CREATE, \
    FIELD_BOOKING_ID, FIELD_ADDITIONAL_NEEDS

from .constants import CREATE_REQUEST_PAYLOAD_REFERENCE as PAYLOAD_REF


@allure.epic("Restful-Booker API")
@allure.feature("Create Booking")
@allure.story('Input data validation')
@allure.tag('negative')
class TestCreateBookingFieldsValidation:
    """Tests related to CreateBooking feature, negative tests"""

    # Note:
    # Spec is missing details related to fields validation,
    # so tests expect general 400 Bad Request error as some
    # common sense minimum

    # title("Empty/null fields")
    @pytest.mark.xfail(reason="Empty/null fields aren't validated")
    @pytest.mark.parametrize(
        "payload",
        ParamsGenerator.get_payloads_with_empty_null_fields(
            PAYLOAD_REF,
            skip=[FIELD_ADDITIONAL_NEEDS]
        )
    )
    def test_empty_fields(self, api_request: ApiRequestHelper,
                          payload: dict, test_id: str,
                          handle_entry_deletion: dict):
        """Entry creation fails if field is empty string or null"""

        allure.dynamic.title(
            f"No booking creation on empty field [{test_id}]"
        )

        with given(f'incomplete payload with {test_id}'):
            pass

        with when("request performed with given payload"):
            created_response = \
                api_request.by_name(REQ_CREATE) \
                .with_json_payload(payload) \
                .perform(check_status_code=False)

            handle_entry_deletion.append(created_response)

        with then("response is 400 Bad Request and "
                  "no new booking was created"):
            created_response.status_code_equals(400) \
                .json.params_not_present(FIELD_BOOKING_ID)

    # title("Missing fields")
    @pytest.mark.xfail(reason="Missing fields aren't validated")
    @pytest.mark.parametrize(
        "payload",
        ParamsGenerator.get_payloads_with_missing_fields(
            PAYLOAD_REF
        )
    )
    def test_missing_fields(self, api_request: ApiRequestHelper,
                            payload: dict, test_id: str,
                            handle_entry_deletion: dict):
        """Entry creation fails if field is missing"""

        allure.dynamic.title(
            f"No booking creation on missing field [{test_id}]"
        )

        with given(f'incomplete payload with {test_id}'):
            pass

        with when("request performed with given payload"):
            created_response = \
                api_request.by_name(REQ_CREATE) \
                .with_json_payload(payload) \
                .perform(check_status_code=False)

            handle_entry_deletion.append(created_response)

        with then("response is 400 Bad Request and "
                  "no new booking was created"):
            created_response.status_code_equals(400) \
                .json.params_not_present(FIELD_BOOKING_ID)

    # title("Invalid data")
    @pytest.mark.xfail(reason="Invalid data types in fields aren't validated")
    @pytest.mark.parametrize(
        "payload",
        ParamsGenerator.get_payloads_with_invalid_types_fields(
            PAYLOAD_REF
        )
    )
    def test_invalid_data_fields(self,
                                 api_request: ApiRequestHelper,
                                 payload: dict, test_id: str,
                                 handle_entry_deletion: dict):
        """Entry creation fails if field contain invalid data
        types"""

        allure.dynamic.title(
            "No booking creation "
            f"on invalid type of data in fields [{test_id}]"
        )

        with given(f'incomplete payload with {test_id}'):
            pass

        with when("request performed with given payload"):
            created_response = \
                api_request.by_name(REQ_CREATE) \
                .with_json_payload(payload) \
                .perform(check_status_code=False)

            handle_entry_deletion.append(created_response)

        with then("response is 400 Bad Request and "
                  "no new booking was created"):
            created_response.status_code_equals(400) \
                .json.params_not_present(FIELD_BOOKING_ID)
