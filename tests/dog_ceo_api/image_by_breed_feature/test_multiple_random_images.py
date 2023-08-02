"""
Tests for DOG.CEO API: https://dog.ceo/dog-api/
Epic:    'DOG CEO API'
Feautre: 'Random image by breed'
Story:   'Multiple images from a breed collection.'
"""
import pytest
import allure
from utils.api_helpers.api_request_helper import ApiRequestHelper
from utils.api_helpers.comparators import List
from utils.helper import Helper

@allure.epic('DOG CEO API')
@allure.feature('Random image by breed')
@allure.story('Multiple images from a breed collection')
class Test_RandomImageByBreed_SingleImage:
    """Group of tests related to DOG_API - Random image story"""
    @allure.title('Get {amount} random images by "{breed}" breed')
    @pytest.mark.parametrize('breed,amount', [
        #('akita', 1),
        ('collie',2),
        #('terrier', 50)
    ])
    def test_multiple_random_images_by_breed(self, api_request: ApiRequestHelper,
                                             helper: Helper,
                                             breed, amount):
        allure.dynamic.description(
            f'Verifies random image API call for {amount} image(s) '
            f'for breed {breed} '
            f'is successful and returns {amount} random image(s)'
        )

        (api_request.by_name("GetMultipleRandomImageByBreed")
                    .with_path_params(breed=breed, amount=amount)
                    .perform()
                    .validate()
                    .value_equals('status', 'success')
                    .verify_value('message', List.count_is_greater_than, 10)
                    .elements_count_is('message', amount)
                    .verify_each('message', helper.is_image_url)
        )

    @pytest.mark.xfail(reason='API returns at least 1 image')
    @allure.title('Get zero random images by breed')
    @allure.tag('Negative')
    def test_negative_get_zero_random_images(self, api_request: ApiRequestHelper):
        '''Request with zero (0) param returns empty list of images'''
        (api_request.by_name("GetMultipleRandomImageByBreed")
                    .with_path_params(breed='akita', amount=0)
                    .perform()
                    .validate()
                    .value_equals('status', 'success')
                    .elements_count_is('message', 0)
        )
