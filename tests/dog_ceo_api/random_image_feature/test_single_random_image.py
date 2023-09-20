"""
Tests for DOG.CEO API: https://dog.ceo/dog-api/
Epic:    'DOG CEO API'
Feautre: 'Random image'
Story:   'Getting single random image of random breed.'
"""
import pytest
import allure
from utils.api_helpers.api_request_helper import ApiRequestHelper
from utils.api_helpers.api_response_helper import ApiResponseHelper
from .constants import NOT_ALLOWED_METHODS

@allure.epic('DOG CEO API')
@allure.feature('Random image')
@allure.story('Getting single random image of random breed')
class TestRandomImageSingleImage:
    """Group of tests related to DOG_API - Random image story"""

    @allure.title('Get single random image')
    @pytest.mark.request("GetSingleRandomImage")
    def test_get(self, api_response: ApiResponseHelper):
        """Verifies random image API call is successful and
           return URI to image MIME type file"""
        api_response.validate_against_schema() \
            .headers.are_like() \
            .json.equals()


    @allure.title('Get single random image with unexpected query params')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.request("GetSingleRandomImage")
    def test_get_with_query_params(self, api_request: ApiRequestHelper):
        """Verifies random image API call is successful and
           return URI to image MIME type file, even when there are
           unexpected query params were passed"""
        api_request.with_query_params(q=10, size=100, amount=500) \
                    .perform() \
                    .validate_against_schema() \
                    .headers.are_like() \
                    .json.equals()


    @allure.title("Get single random image HEAD request")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.request("GetSingleRandomImage")
    def test_head_request(self, api_request: ApiRequestHelper):
        """HEAD method request returns headers, but no body"""
        api_request.with_method("HEAD") \
            .perform() \
            .headers.are_like() \
            .is_empty()


    @allure.title("Request single random image with "
                  "unsupported method \"{method}\" is handled")
    @allure.tag('negative')
    @pytest.mark.request("GetSingleRandomImage_MethodNotAllowed")
    @pytest.mark.parametrize('method', NOT_ALLOWED_METHODS)
    def test_unsupported_method_is_handled(self, api_request: ApiRequestHelper, method):
        """Unsupported methods return error message and list of
        supported methods in headers"""
        api_request.with_method(method) \
            .perform() \
            .validate_against_schema() \
            .headers.are_like() \
            .json.equals()
