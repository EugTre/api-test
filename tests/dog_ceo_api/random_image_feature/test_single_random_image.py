"""
Tests for DOG.CEO API: https://dog.ceo/dog-api/
Epic:    'DOG CEO API'
Feautre: 'Random image'
Story:   'Getting single random image of random breed.'
"""
import allure
from utils.api_helpers.api_request_helper import ApiRequestHelper

@allure.epic('DOG CEO API')
@allure.feature('Random image')
@allure.story('Getting single random image of random breed.')
class TestRandomImageSingleImage:
    """Group of tests related to DOG_API - Random image story"""

    @allure.title('Get single random image')
    def test_get(self, api_request: ApiRequestHelper):
        """Verifies random image API call is successful and
           return URI to image MIME type file"""

        r = api_request.by_name('GetSingleRandomImage') \
            .perform() \
            .validate_against_schema()

        print(r.json.expected)
        print(r.json.content)

    @allure.title('Get single random image, unexpected query params')
    def test_get_with_query_params(self, api_request: ApiRequestHelper):
        """Verifies random image API call is successful and
           return URI to image MIME type file, even when there are
           unexpected query params were passed"""

        api_request.by_name('GetSingleRandomImage') \
            .with_query_params(q=10, size=100, amount=500) \
            .perform() \
            .validate_against_schema() \
            .json.equals()


"""
{
    'status': 'success',
    'message': match.AnyTextLike(r'^(http|https):\/\/.*(\.jpg)$')
})
"""






    # @pytest.mark.parametrize('number_of_images', [1, 3, 5, 10])
    # def test_multiple_random_images(self, api_client, number_of_images):
    #     """Verifies several random image API call is successful and
    #        return several URI of image MIME type files"""
    #     response = api_client.get(
    #         path=DOG_API__GET_MULTIPLE_RANDOM_IMAGE_REL_URI % number_of_images)

    #     assert response.status_code == 200

    #     content = response.json()
    #     print(content)
    #     assert content['status'] == 'success'

    #     data = content['message']
    #     assert isinstance(data, list)
    #     assert len(data) == number_of_images

    #     for uri in data:
    #         assert check_uri_is_image(uri)

    # def test_breed_list(self, breeds_dict):
    #     """Verifies breeds list API call is successful and return proper JSON message
    #        (keys names are alphabetic and values is always an array)"""
    #     print(breeds_dict)
    #     schema = {
    #         'type': 'object',
    #         'patternProperties': {
    #             '^[a-z]*$': {'type': 'array'}
    #         },
    #         'additionalProperties': False,
    #         'minProperties': 1,
    #     }

    #     validate(breeds_dict, schema=schema)

    # def test_random_image_from_breed(self, api_client, breeds_dict):
    #     """Verifies random image from breeds list API call is successful and
    #        return proper image URI"""
    #     breed = random.choice(list(breeds_dict.keys()))
    #     print(breed)

    #     response = api_client.get(path=DOG_API__GET_BREED_RANDOM_IMAGE_REL_URI % breed)
    #     assert response.status_code == 200

    #     content = response.json()
    #     assert content['status'] == 'success'
    #     assert check_uri_is_image(content['message'])

    # @pytest.mark.parametrize('number_of_images', [1, 3, 5, 10])
    # def test_multiple_random_images_from_breed(self, number_of_images, api_client, breeds_dict):
    #     """Verifies multiple random image from breeds list API call is successful and
    #        return proper number of images URIs"""
    #     breed = random.choice(list(breeds_dict.keys()))
    #     print(breed)

    #     response = api_client.get(path=DOG_API__GET_BREED_MULTIPLE_RANDOM_IMAGE_REL_URI % (
    #         breed, number_of_images))
    #     assert response.status_code == 200

    #     content = response.json()
    #     assert content['status'] == 'success'

    #     data = content['message']
    #     assert isinstance(data, list)
    #     print(data)
    #     assert len(data) == number_of_images

    #     for uri in data:
    #         assert check_uri_is_image(uri)
