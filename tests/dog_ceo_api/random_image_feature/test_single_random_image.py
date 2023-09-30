"""
Tests for DOG.CEO API: https://dog.ceo/dog-api/
Epic:    'DOG CEO API'
Feautre: 'Random image'
Story:   'Getting single random image of random breed.'
"""

import pytest
import allure
from utils.bdd import given, when, then
from utils.api_helpers.api_request_helper import ApiRequestHelper
from .constants import NOT_ALLOWED_METHODS


@allure.epic('DOG CEO API')
@allure.feature('Random image')
@allure.story('Getting single random image of random breed')
class TestRandomImageSingleImage():
    """Group of tests related to DOG_API - Random image story"""

    @allure.title('Get single random image')
    def test_get(self, api_request: ApiRequestHelper):
        """Verifies random image API call is successful and
           return URI to image MIME type file"""

        with given("Get request with no params"):
            api_request.by_name("GetSingleRandomImage")

        with when("request performed with 200 OK"):
            response = api_request.perform()

        with then("response should match expected"):
            response.validates_against_schema() \
                    .headers.are_like() \
                    .json.equals()

    @allure.title('Get single random image with unexpected query params')
    @allure.severity(allure.severity_level.MINOR)
    def test_get_with_query_params(self, api_request: ApiRequestHelper):
        """Verifies random image API call is successful and
           return URI to image MIME type file, even when there are
           unexpected query params were passed"""

        with given("GET request with additional params"):
            api_request.by_name("GetSingleRandomImage") \
                       .with_query_params(q=10, size=100, amount=500)
        with when("request performed with 200 OK"):
            response = api_request.perform()
        with then("response should match expected"):
            response.validates_against_schema() \
                    .headers.are_like() \
                    .json.equals()

    @allure.title("Get single random image HEAD request")
    @allure.severity(allure.severity_level.MINOR)
    def test_head_request(self, api_request: ApiRequestHelper):
        """HEAD method request returns headers, but no body"""

        with given("Head request"):
            api_request.by_name("GetSingleRandomImage") \
                       .with_method("HEAD")

        with when("request performed with 200 OK"):
            response = api_request.perform()

        with then("response should be headers only"):
            response.headers.are_like() \
                    .is_empty()

    @allure.title("Request single random image with "
                  "unsupported method \"{method}\" is handled")
    @allure.tag('negative')
    @pytest.mark.parametrize('method', NOT_ALLOWED_METHODS)
    def test_unsupported_method_is_handled(self, method,
                                           api_request: ApiRequestHelper):
        """Unsupported methods return error message and list of
        supported methods in headers"""

        with given(f"unsupported request method {method}"):
            api_request.by_name("GetSingleRandomImage_MethodNotAllowed") \
                       .with_method(method)

        with when("request performed with 405 status code"):
            response = api_request.perform()

        with then("error message for 405 error is returned"):
            response.validates_against_schema() \
                    .headers.are_like() \
                    .json.equals()
