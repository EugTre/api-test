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
from utils.api_client.models import HTTPMethod
from utils.generators import ParamsGenerator

from .constants import AUTH_REQUEST_PAYLOAD_REFERENCE


@allure.epic("Restful-Booker API")
@allure.feature("Auth Token")
@allure.story('Token creation')
class TestCreateToken:
    """Tests related to auth token creation"""

    @allure.title("Creates token with valid creds")
    def test_create(self, api_request: ApiRequestHelper):
        """Token can be created when both username and
        password was sent"""

        with given("valid username and password"):
            # picked from requests.json
            pass

        with when("CreateToken POST request with creds successfull (200 OK)"):
            response = api_request.by_name("Auth") \
                .perform()

        with then("token is present in the response"):
            response.validates_against_schema() \
                .headers.are_like()

    @allure.title("Does not creates token with unsuitable creds")
    def test_create_fails(self, api_request: ApiRequestHelper):
        """Token can not be created when not registered creds
        are used"""

        with given("valid username and password"):
            username = "MyUser"
            password = "MyPassword"

        with when("CreateToken POST request with creds successfull (200 OK)"):
            response = api_request.by_name("Auth_BadCredentials") \
                .with_json_payload({
                    "username": username,
                    "password": password
                }) \
                .perform()

        with then("token is not present in the response"):
            response.validates_against_schema() \
                .headers.are_like() \
                .json.equals()

    @allure.title("HEAD method returns headers only")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.xfail(reason="API returns 404 Not Found")
    def test_head(self, api_request: ApiRequestHelper):
        """HEAD method returns headers only"""
        with given("request with no payload"):
            pass

        with when("HEAD request performed with 200 OK"):
            response = api_request.by_name("Auth") \
                .with_method(HTTPMethod.HEAD) \
                .with_json_payload(None) \
                .perform()

        with then("response should be headers only"):
            response.is_empty() \
                .headers.present("Content-Type", "Date")

    @allure.title("OPTIONS method returns supported methods")
    @allure.severity(allure.severity_level.MINOR)
    def test_options(self, api_request: ApiRequestHelper):
        """OPTIONS method returns headers only"""
        with given("request with no payload"):
            pass

        with when("OPTIONS request performed with 200 OK"):
            response = api_request.by_name("Auth") \
                .with_method(HTTPMethod.OPTIONS) \
                .with_json_payload(None) \
                .perform()

        with then("supported methods reported in the response"):
            response.equals('POST') \
                .headers.are_like({"Allow": "POST"})


@allure.epic("Restful-Booker API")
@allure.feature("Auth Token")
@allure.story('Token creation')
@allure.tag('negative')
class TestCreateTokenNegative:
    """Negative test related to Auth Token feature"""

    # title("No token creation on empty fields")
    @pytest.mark.parametrize(
        "payload",
        ParamsGenerator.get_empty_null_fields(
            AUTH_REQUEST_PAYLOAD_REFERENCE
        )
    )
    def test_empty_fields_fails(self, api_request: ApiRequestHelper,
                                payload,
                                test_id):
        """Token creation fails if credentials are empty"""

        allure.dynamic.title(
            f"No token creation on empty fields [{test_id}]"
        )

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

    # title("No token creation on missing fields")
    @pytest.mark.parametrize(
        "payload",
        ParamsGenerator.get_payloads_with_missing_fields(
            AUTH_REQUEST_PAYLOAD_REFERENCE
        )
    )
    def test_missing_fields_fails(self, api_request: ApiRequestHelper,
                                  payload,
                                  test_id):
        """Token creation fails if JSON have missing fields"""

        allure.dynamic.title(
            f"No token creation on missing fields [{test_id}]"
        )

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

    # title("No token creation on non-string creds")
    @pytest.mark.parametrize(
        "payload",
        ParamsGenerator.get_payloads_with_invalid_types(
            AUTH_REQUEST_PAYLOAD_REFERENCE
        )
    )
    def test_invalid_data_types_fails(self, api_request: ApiRequestHelper,
                                      payload: dict,
                                      test_id):
        """Token creation fails if credentials are missing"""

        allure.dynamic.title(
            f"No token creation on invalid fields data types [{test_id}]"
        )

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

    @allure.title("Request with "
                  "unsupported method \"{method}\" is handled")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("method", (
        HTTPMethod.GET,
        HTTPMethod.PUT,
        HTTPMethod.PATCH,
        HTTPMethod.DELETE
    ))
    def test_unsupported_methods(self, method: HTTPMethod,
                                 api_request: ApiRequestHelper):
        """Unsupported method should return 400-like error code"""

        with given(f"unsupported request method {method}"):
            api_request.by_name("Auth_UnsupportedMethod") \
                       .with_json_payload(None) \
                       .with_method(method)

        with when("request performed with 404 status code"):
            response = api_request.perform()

        with then("error message is returned"):
            response.equals()

    # title("Request with malformed payload is handled")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("payload", (
        '{"username": "user", "password": "password", }',
        '{"username", "pasword"}',
        '"user"'
    ), ids=(
        "Extra comma",
        "Missing value",
        "Plain text"
    ))
    def test_malformed_payload(self, api_request: ApiRequestHelper,
                               payload,
                               test_id):
        """Token creation fails if credentials are missing"""

        allure.dynamic.title(
            f"Request with malformed payload is handled [{test_id}]"
        )

        with given('malformed payload'):
            pass

        with when("CreateToken POST request with given creds "
                  "is successfull (200 OK)"):
            response = api_request \
                .by_name("Auth_BadRequest") \
                .with_text_payload(payload) \
                .perform()

        with then("response contain only error message"):
            response.equals()
