"""Test configuration for Restful-Booker API"""
import pytest
from utils.api_client.setup_api_client import setup_api_client
from utils.api_client.simple_api_client import SimpleApiClient

from .constants import API_NAME


@pytest.fixture(scope='session')
def api_client(api_clients_configurations) -> SimpleApiClient:
    '''Returns object inherited from `BaseApiClient` class.

       Actual class and options are selected by given name
       and configured in API config file defined by cmd option `--api-config`
       under the same name
    '''
    return setup_api_client(
        API_NAME,
        api_clients_configurations
    )


@pytest.fixture()
def auth_token(api_request) -> str:
    """Creates and returns token"""
    response = api_request.by_name('Auth').perform()
    return response.get_json_value('/token')
