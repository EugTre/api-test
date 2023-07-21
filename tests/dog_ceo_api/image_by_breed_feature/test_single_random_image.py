"""
Tests for DOG.CEO API: https://dog.ceo/dog-api/
Epic:    'DOG CEO API'
Feautre: 'Random image by breed'
Story:   'Random image from a breed collection.'
"""
import pytest
import allure
from utils.api_helpers.api_request_helper import ApiRequestHelper
from utils.helper import Helper

@allure.epic('DOG CEO API')
@allure.feature('Random image by breed')
class Test_RandomImageByBreed_SingleImage:
    """Group of tests related to DOG_API - Random image story"""

    @allure.story('Random image from a breed collection')
    @allure.title('Get single random image by "{breed}" breed')
    @pytest.mark.parametrize('breed', [
        'pug',
        'terrier',
        'borzoi'
    ])
    def test_single_random_image_by_breed(self, api_request: ApiRequestHelper,
                                          helper: Helper,
                                          breed):
        '''Verifies random image API call is successful and
           return URI to image MIME type file'''
        (api_request.by_name('GetRandomImageByBreed')
                    .with_path_params(breed=breed)
                    .perform()
                    .validate()
                    .value_equals('status', 'success')
                    .value_is_not_empty('message')
                    .verify_value('message', helper.is_image_url)
         )
