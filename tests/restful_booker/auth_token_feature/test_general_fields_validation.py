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

from .constants import AUTH_REQUEST_PAYLOAD_REFERENCE as PAYLOAD_REF


@allure.epic("Restful-Booker API")
@allure.feature("Auth Token")
@allure.story('Token creation')
@allure.tag('negative')
class TestCreateTokenFieldsValidationNegative:
    """Negative test related to Auth Token feature"""

    @allure.title("No token creation on empty fields [{test_id}]")
    @pytest.mark.parametrize(
        "test_id, payload",
        ParamsGenerator.get_payloads_with_empty_null_fields(
            PAYLOAD_REF
        )
    )
    def test_empty_fields_fails(self, test_id, payload: dict,
                                api_request: ApiRequestHelper):
        """Token creation fails if credentials are empty"""
        with given(f'incomplete creds {payload}'):
            pass

        with when("CreateToken POST request with given creds "
                  "is successfull (200 OK)"):
            response = api_request \
                .by_name("Auth_BadCredentials") \
                .with_json_payload(payload) \
                .perform()

        with then("response contain only error message"):
            response.validates_against_schema() \
                .headers.are_like() \
                .json.equals()

    @allure.title("No token creation on missing fields [{test_id}]")
    @pytest.mark.parametrize(
        "test_id, payload",
        ParamsGenerator.get_payloads_with_missing_fields(
            PAYLOAD_REF
        )
    )
    def test_missing_fields_fails(self, test_id, payload: dict,
                                  api_request: ApiRequestHelper):
        """Token creation fails if JSON have missing fields"""

        with given(f'incomplete request body: {payload}'):
            pass

        with when("CreateToken POST request with given creds "
                  "is successfull (200 OK)"):
            response = api_request \
                .by_name("Auth_BadCredentials") \
                .with_json_payload(payload) \
                .perform()

        with then("response contain only error message"):
            response.validates_against_schema() \
                .headers.are_like() \
                .json.equals()

    @allure.title("No token creation on invalid type of"
                  "data in fields [{test_id}]")
    @pytest.mark.parametrize(
        "test_id, payload",
        ParamsGenerator.get_payloads_with_invalid_types_fields(
            PAYLOAD_REF
        )
    )
    def test_invalid_data_types_fails(self, test_id, payload: dict,
                                      api_request: ApiRequestHelper):
        """Token creation fails if credentials fields have
        data of invalid types"""

        username = payload['username']
        password = payload['password']
        with given('creds of types: '
                   f'"{username}" (type: {type(username).__name__})'
                   f'/"{password}" (type: {type(password).__name__})'):
            pass

        with when("CreateToken POST request with given creds "
                  "is successfull (200 OK)"):
            response = api_request \
                .by_name("Auth_BadCredentials") \
                .with_json_payload(payload) \
                .perform()

        with then("response contain only error message"):
            response.validates_against_schema() \
                .headers.are_like() \
                .json.equals()
