"""
Tests for DOG.CEO API: https://dog.ceo/dog-api/
Epic:    'DOG CEO API'
Feautre: 'List breeds'
Story:   'Getting list of all breeds'
"""
import allure
from utils.bdd import given, when, then
from utils.api_helpers.api_request_helper import ApiRequestHelper


@allure.epic('DOG CEO API')
@allure.feature('List breeds')
@allure.story('Getting list of all breeds')
class TestListAllBreeds():
    """Group of tests related to DOG_API - List all breeds"""

    @allure.title("Get List of All Breeds")
    def test_get_all_breeds(self, api_request: ApiRequestHelper):
        """It's possible to request a full list of breeds."""

        with given("Get request without params"):
            api_request.by_name("GetListOfAllBreeds")

        with when("request performed with 200 OK"):
            response = api_request.perform()

        with then("response should be valid and contain list of breeds"):
            response.validates_against_schema() \
                .headers.are_like() \
                .json.is_like()
