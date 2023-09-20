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
from .constants import NOT_ALLOWED_METHODS


@allure.epic('DOG CEO API')
@allure.feature('Random image')
@allure.story('Getting multiple random images of random breed')
class TestRandomImageMultipleImages:
    """Group of tests related to DOG_API - Multiple random image story"""

    @allure.title('Get multiple ({amount}) random image(s)')
    @pytest.mark.request("GetMultipleRandomImages")
    @pytest.mark.parametrize('amount', [1, 3, 50])
    def test_multiple_images(self, api_request: ApiRequestHelper,
                                   amount):
        allure.dynamic.description(
            f'Verifies random image API call for {amount} image(s) '
            f'is successful and returns {amount} random image(s)'
        )

        api_request.with_path_params(amount=amount) \
            .perform() \
            .validates_against_schema() \
            .headers.are_like() \
            .json.equals() \
            .json.param_equals(
                '/message',
                match.AnyListOf(size=amount)
            )


    @allure.title('Get over the limit number of random images ({amount}) return exactly 50 items')
    @pytest.mark.request("GetMultipleRandomImages")
    @pytest.mark.parametrize('amount', (51, 100))
    def test_over_the_limit_amount(self, api_request: ApiRequestHelper, amount):
        """Verifies random image API call for >50 images is successfull
        and returns exactly 50 images"""
        api_request.with_path_params(amount=amount) \
            .perform() \
            .validates_against_schema() \
            .headers.are_like() \
            .json.equals() \
            .json.param_equals(
                '/message',
                match.AnyListOf(size=50)
            )


    @allure.title('Get invalid number of images ({amount}) return at least 1 image')
    @allure.tag('negative')
    @pytest.mark.request("GetMultipleRandomImages")
    @pytest.mark.parametrize('amount', (0, -5, "text"))
    def test_below_limit(self, api_request: ApiRequestHelper, amount):
        """Verifies random image API call for invalid number of images
        successfully returns 1 image"""
        api_request.with_path_params(amount=amount) \
            .perform() \
            .validates_against_schema() \
            .headers.are_like() \
            .json.equals() \
            .json.param_equals('/message', match.AnyListOf(size=1))


    @allure.title('Get random images with unexpected query params')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.request("GetMultipleRandomImages")
    def test_get_with_query_params(self, api_request: ApiRequestHelper):
        """Verifies multiple random image API call is successful and
           return URI to image MIME type file, even when there are
           unexpected query params were passed"""
        api_request.with_query_params(q=10, size=100, amount=33) \
                    .with_path_params(amount=10) \
                    .perform() \
                    .validates_against_schema() \
                    .headers.are_like() \
                    .json.equals() \
                    .json.param_equals('/message', match.AnyListOf(size=10))


    @allure.title("Get multiple random images HEAD request")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.request("GetMultipleRandomImages")
    def test_head_request(self, api_request: ApiRequestHelper):
        """HEAD method request returns headers, but no body"""
        api_request.with_path_params(amount=5) \
            .with_method("HEAD") \
            .perform() \
            .headers.are_like() \
            .is_empty()


    @allure.title("Request multiple random image with "
                  "unsupported method \"{method}\" is handled")
    @allure.tag('negative')
    @pytest.mark.request("GetMultipleRandomImages_MethodNotAllowed")
    @pytest.mark.parametrize('method', NOT_ALLOWED_METHODS)
    def test_unsupported_method_is_handled(self, api_request: ApiRequestHelper, method):
        """Unsupported methods return error message and list of
        supported methods in headers"""
        api_request.with_path_params(amount=5) \
            .with_method(method) \
            .perform() \
            .validates_against_schema() \
            .headers.are_like() \
            .json.equals()


    @allure.title("Get multiple random image with "
                  "invalid sub-route is handled")
    @allure.tag('negative')
    @pytest.mark.request("GetMultipleRandomImages_InvalidSubPath")
    def test_invalid_subpath_is_handled(self, api_request: ApiRequestHelper):
        """Unsupported methods return error message and list of
        supported methods in headers"""
        api_request.with_path_params(amount=5) \
            .perform() \
            .validates_against_schema() \
            .headers.are_like() \
            .json.equals()
