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

from ..constants import REQ_AUTH


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
            response = \
                api_request.by_name(REQ_AUTH) \
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

    @pytest.mark.xfail(reason="API returns 404 Not Found", **pytest.efx)
    @allure.title("HEAD method returns headers only")
    @allure.severity(allure.severity_level.MINOR)
    def test_head(self, api_request: ApiRequestHelper):
        """HEAD method returns headers only"""
        with given("request with no payload"):
            pass

        with when("HEAD request performed with 200 OK"):
            response = api_request.by_name(REQ_AUTH) \
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
            response = api_request.by_name(REQ_AUTH) \
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

    @allure.title("Request with malformed payload is handled [{test_id}]")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize(*pytest.format_params(
        "test_id, payload",
        ("Tailing comma", '{"username": "user", "password": "password", }'),
        ("MalformedJSON", '{"username", "pasword"}'),
        ("Plain text", '"user"')
    ))
    def test_malformed_payload(self, test_id, payload,
                               api_request: ApiRequestHelper):
        """Token creation fails if credentials are missing"""
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
