"""
Tests for DOG.CEO API: https://dog.ceo/dog-api/
Epic:    'DOG CEO API'
Feautre: 'Random image'
Story:   'Getting multiple random images of random breed'
"""
import pytest
import allure
from utils.api_helpers.api_request_helper import ApiRequestHelper
import utils.matchers.matcher as match
from utils.bdd import given, when, then

from .constants import NOT_ALLOWED_METHODS


@allure.epic('DOG CEO API')
@allure.feature('Random image')
@allure.story('Getting multiple random images of random breed')
class TestRandomImageMultipleImages:
    """Group of tests related to DOG_API - Multiple random image story"""

    @allure.title('Get multiple ({amount}) random image(s)')
    @pytest.mark.parametrize('amount', [1, 3, 50])
    def test_multiple_images(self, api_request: ApiRequestHelper,
                             amount):
        allure.dynamic.description(
            f'Verifies random image API call for {amount} image(s) '
            f'is successful and returns {amount} random image(s)'
        )

        with given("Get request with valid desired number of images"):
            api_request.by_name("GetMultipleRandomImages") \
                       .with_path_params(amount=amount)

        with when("request performed with 200 OK"):
            response = api_request.perform()

        with then(f"response should be valid and contains {amount} images"):
            response.validates_against_schema() \
                .headers.are_like() \
                .json.equals() \
                .json.param_equals(
                    '/message',
                    match.AnyListOf(size=amount)
                )

    @allure.title('Get over the limit number of random images '
                  '({amount}) return exactly 50 items')
    @pytest.mark.parametrize('amount', (51, 100))
    def test_over_the_limit_amount(self, amount,
                                   api_request: ApiRequestHelper):
        """Verifies random image API call for >50 images is successfull
        and returns exactly 50 images"""

        with given("Get request with desired number of images above limit"):
            api_request.by_name("GetMultipleRandomImages") \
                       .with_path_params(amount=amount)

        with when("request performed with 200 OK"):
            response = api_request.perform()

        with then("response should be valid and contains only 50 images"):
            response.validates_against_schema() \
                    .headers.are_like() \
                    .json.equals() \
                    .json.param_equals(
                        '/message',
                        match.AnyListOf(size=50)
                    )

    @allure.title('Get invalid number of images ({amount}) return '
                  'at least 1 image')
    @allure.tag('negative')
    @pytest.mark.parametrize('amount', (0, -5, "text"))
    def test_below_limit(self, api_request: ApiRequestHelper, amount):
        """Verifies random image API call for invalid number of images
        successfully returns 1 image"""

        with given("Get request with invalid number of desired images"):
            api_request.by_name("GetMultipleRandomImages") \
                       .with_path_params(amount=amount)

        with when("request performed with 200 OK"):
            response = api_request.perform()

        with then("response should be valid and contains only 1 image"):
            response.validates_against_schema() \
                    .headers.are_like() \
                    .json.equals() \
                    .json.param_equals(
                        '/message',
                        match.AnyListOf(size=1)
                    )

    @allure.title('Get random images with unexpected query params')
    @allure.severity(allure.severity_level.MINOR)
    def test_get_with_query_params(self, api_request: ApiRequestHelper):
        """Verifies multiple random image API call is successful and
           return URI to image MIME type file, even when there are
           unexpected query params were passed"""

        with given("Get request with valid number of desired images "
                   "and extra query params"):
            api_request.by_name("GetMultipleRandomImages") \
                       .with_path_params(amount=10) \
                       .with_query_params(q=10, size=100, amount=33)

        with when("request performed with 200 OK"):
            response = api_request.perform()

        with then("response should be valid and contains dersired"
                  "number of images"):
            response.validates_against_schema() \
                    .headers.are_like() \
                    .json.equals() \
                    .json.param_equals(
                        '/message',
                        match.AnyListOf(size=10)
                    )

    @allure.title("Get multiple random images HEAD request")
    @allure.severity(allure.severity_level.MINOR)
    def test_head_request(self, api_request: ApiRequestHelper):
        """HEAD method request returns headers, but no body"""

        with given("Head request with valid number of desired images"):
            api_request.by_name("GetMultipleRandomImages") \
                        .with_method("HEAD") \
                        .with_path_params(amount=3) \

        with when("request performed with 200 OK"):
            response = api_request.perform()

        with then("response should have headers, but empty body"):
            response.is_empty() \
                    .headers.are_like()

    @allure.title("Request multiple random image with "
                  "unsupported method \"{method}\" is handled")
    @allure.tag('negative')
    @pytest.mark.parametrize('method', NOT_ALLOWED_METHODS)
    def test_unsupported_method_is_handled(self, method,
                                           api_request: ApiRequestHelper):
        """Unsupported methods return error message and list of
        supported methods in headers"""

        with given(f"unsupported request method {method}"):
            api_request.by_name("GetMultipleRandomImages_MethodNotAllowed") \
                       .with_path_params(amount=3) \
                       .with_method(method)

        with when("request performed with 405 status code"):
            response = api_request.perform()

        with then("error message for 405 error is returned"):
            response.validates_against_schema() \
                    .headers.are_like() \
                    .json.equals()

    @allure.title("Get multiple random image with "
                  "invalid sub-route is handled")
    @allure.tag('negative')
    @pytest.mark.request("GetMultipleRandomImages_InvalidSubPath")
    def test_invalid_subpath_is_handled(self, api_request: ApiRequestHelper):
        """Unsupported methods return error message and list of
        supported methods in headers"""

        with given("Get request to invalid sub-path"):
            api_request.by_name("GetMultipleRandomImages_InvalidSubPath") \
                       .with_path_params(amount=3)

        with when("request performed with 404 status code"):
            response = api_request.perform()

        with then("error message for 404 error is returned"):
            response.validates_against_schema() \
                    .headers.are_like() \
                    .json.equals()
