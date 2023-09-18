import pytest
from utils.api_client.setup_api_client import setup_api_client
from utils.api_client.simple_api_client import SimpleApiClient

API_NAME = 'DOG.CEO'

@pytest.fixture(scope='package')
def api_client(api_clients_configurations) -> SimpleApiClient:
    '''Returns object inherited from `BasicApiClient` class.

       Actual class and options are selected by given name
       and configured in API config file defined by cmd option `--api-config`
       under the same name
    '''
    return setup_api_client(
        API_NAME,
        api_clients_configurations
    )
