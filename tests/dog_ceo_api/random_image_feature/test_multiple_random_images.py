"""
Tests for DOG.CEO API: https://dog.ceo/dog-api/
Epic:    'DOG CEO API'
Feautre: 'Random image'
Story:   'Display multiple random images from all dogs collection'
"""
import pytest
import allure

from utils.api_helpers.api_request_helper import ApiRequestHelper
from utils.helper import Helper


@allure.epic('DOG CEO API')
@allure.feature('Random image')
@allure.story('Display multiple random images from all dogs collection')
class Test_RandomImage_MultipleImages:
    """Tests for mupltiple random images story"""

    @allure.title('Get multiple ({amount}) random image(s)')
    @pytest.mark.parametrize('amount', [1, 2, 50])
    def test_multiple_random_image(self, api_request: ApiRequestHelper,
                                   amount, helper: Helper):
        allure.dynamic.description(
            f'Verifies random image API call for {amount} image(s) '
            f'is successful and returns {amount} random image(s)'
        )

        (api_request.by_name("GetMultipleRandomImages")
                    .with_path_params(amount=amount)
                    .perform()
                    .validate()
                    .value_equals('status', 'success')
                    .elements_count_is('message', amount)
                    .verify_each('message', helper.is_image_url)
        )

    @pytest.mark.xfail(reason='API returns at least 1 image')
    @allure.title('Get zero random images')
    @allure.tag('Negative')
    def test_negative_get_zero_random_images(self, api_request: ApiRequestHelper):
        '''Request with zero (0) param returns empty list of images'''
        (api_request.by_name("GetMultipleRandomImages")
                    .with_path_params(amount=0)
                    .perform()
                    .validate()
                    .value_equals('status', 'success')
                    .elements_count_is('message', 0)
        )

    #@allute.title('Get more than 50 random images')
    #@allure.story('Display multiple random images ')
