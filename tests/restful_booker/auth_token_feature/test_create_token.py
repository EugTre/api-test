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

from .constants import USERNAME, PASSWORD


@allure.epic("Restful-Booker API")
@allure.feature("Auth Token")
@allure.story('Token creation')
class TestCreateToken:
    """Tests related to auth token creation"""

    @allure.title("Create token with valid creds")
    def test_create(self, api_request: ApiRequestHelper):
        """Token can be created when both username and
        password was sent"""

        with given("valid username and password"):
            username = USERNAME
            password = PASSWORD

        with when("CreateToken POST request with creds successfull (200 OK)"):
            response = api_request.by_name("Auth") \
                .with_json_payload({
                    "username": username,
                    "password": password
                }) \
                .perform()

        with then("token is present in the response"):
            response.validates_against_schema() \
                .headers.are_like()

    # title("No token creation on empty fields")
    @pytest.mark.parametrize("username, password", (
        pytest.param("", "",            id="Empty-Empty"),
        pytest.param("user", "",        id="user-Empty"),
        pytest.param("", "pass",        id="Empty-pass"),
        pytest.param(None, None,        id="null-null"),
        pytest.param("user", None,      id="user-null"),
        pytest.param(None, "pass",      id="null-pass"),
    ))
    def test_empty_fields_fails(self, api_request: ApiRequestHelper,
                                username, password,
                                test_id):
        """Token creation fails if credentials are empty"""

        allure.dynamic.title(
            f"No token creation on empty fields [{test_id}]"
        )

        with given(f'incomplete creds "{username}"/"{password}"'):
            pass

        with when("CreateToken POST request with given creds "
                  "is successfull (200 OK)"):
            response = api_request \
                .by_name("Auth_BadCredentials") \
                .with_json_payload({
                    "username": username,
                    "password": password
                }) \
                .perform()

        with then("response contain only error message"):
            response.validates_against_schema() \
                .headers.are_like() \
                .json.equals()

    # title("No token creation on missing fields")
    @pytest.mark.parametrize("payload", (
        pytest.param({}, id="No_Fields"),
        pytest.param({"username": "user"}, id="User_Field_Only"),
        pytest.param({"password": "pass"}, id="Pass_Field_Only"),
        pytest.param({"other": "field"}, id="Non_Expected_Fields_Only")
    ))
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
    @pytest.mark.parametrize("username, password", (
        pytest.param(142, "pass",        id="Number-String"),
        pytest.param(True, "pass",       id="Bool-String"),
        pytest.param([1, 2], "pass",     id="Array-String"),
        pytest.param({"obj": 1}, "pass", id="Object-String"),

        pytest.param("user", 142,        id="String-Number"),
        pytest.param("user", True,       id="String-Bool"),
        pytest.param("user", [1, 2],     id="String-Array"),
        pytest.param("user", {"obj": 1}, id="String-Object"),
    ))
    def test_invalid_data_types_fails(self, api_request: ApiRequestHelper,
                                      username, password,
                                      test_id):
        """Token creation fails if credentials are missing"""

        allure.dynamic.title(
            f"No token creation on invalid fields data types [{test_id}]"
        )

        with given('creds of types: '
                   f'"{username}" (type: {type(username).__name__})'
                   f'/"{password}" (type: {type(password).__name__})'):
            pass

        with when("CreateToken POST request with given creds "
                  "is successfull (200 OK)"):
            response = api_request \
                .by_name("Auth_BadCredentials") \
                .with_json_payload({
                    "username": username,
                    "password": password
                }) \
                .perform()

        with then("response contain only error message"):
            response.validates_against_schema() \
                .headers.are_like() \
                .json.equals()

    # title("Request with malformed payload is handled")
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
            f"No token creation on invalid fields data types [{test_id}]"
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
            response.equals("Bad Request") \
                .headers.are_like({
                    "Content-Type": "text/plain; charset=utf-8"
                })

    @allure.title("HEAD method returns headers only")
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
                .headers.are_like({
                    "Allow": "POST"
                })

    # title("Request with unsupported method is handled")
    @pytest.mark.parametrize("method", (
        HTTPMethod.GET,
        HTTPMethod.PUT,
        HTTPMethod.PATCH,
        HTTPMethod.DELETE
    ))
    def test_unsupported_methods(self, method: HTTPMethod,
                                 api_request: ApiRequestHelper):
        # TBD
        pass