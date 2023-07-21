"""
Test related helpers
"""
import os
import logging.handlers
from logging.config import fileConfig

import allure
import pytest

from utils.api_client.models import ApiClientsConfigurationCollection
from utils.api_client.setup_api_client import setup_api_client
from utils.api_client.api_configuration_reader import ApiConfigurationReader

from utils.helper import Helper
from utils.log_database_handler import DatabaseHandler

from utils.api_client.basic_api_client import BasicApiClient
from utils.api_helpers.request_helper import ApiRequestHelper

# from tests.tests_l3.rest_api_2.open_brewery_db_api import OpenBreweryDBAPI

def pytest_addoption(parser):
    """Add custom CLI arguments"""
    parser.addoption(
        "--logging-config",
        action="store",
        default="config/logging.ini",
        help="Configuration file for logging"
    )
    parser.addoption(
        "--api-config",
        action="store",
        default="config/api_clients.ini",
        help="Configuration file for API Clients"
    )

def pytest_configure(config):
    """Registers custom pytest markers"""
    config.addinivalue_line("markers",
                            "api(name): set name of API Client to use")
    config.addinivalue_line("markers",
                            "api_dog_ceo: value")
    config.addinivalue_line("markers",
                            "logger(name): set name of logger to use")

@pytest.fixture(scope='session')
def helper() -> Helper:
    """Returns `Helper` class object to use inside tests/fixtures"""
    return Helper()

@pytest.fixture(scope='session')
def setup_loggers(request):
    """Setups loggers by configuration provided by --logging-config command-line argument"""
    logger_config = request.config.getoption("--logging-config")
    if not os.path.exists(logger_config):
        raise FileNotFoundError('Missing logging config file provided by --logging-config option '
                                f'with name "{logger_config}".')
    logging.handlers.DatabaseHandler = DatabaseHandler
    fileConfig(logger_config)

@pytest.fixture(scope='session')
def api_clients_configurations(request) -> ApiClientsConfigurationCollection:
    """Setups api by configuration provided by --api-config command-line argument"""
    api_config_file = request.config.getoption("--api-config")
    if not os.path.exists(api_config_file):
        raise FileNotFoundError(
                'Missing API config file provided by `--api-config` option '
                f'with name "{api_config_file}".')

    return ApiConfigurationReader(api_config_file).read_configurations()

@pytest.fixture()
def logger(request, setup_loggers):
    """Returns logger defined by name defined by tests mark @pytest.mark.logger()"""
    logger_name = 'root'
    logger_name_params = request.node.get_closest_marker('logger')
    if logger_name_params:
        logger_name = logger_name_params.args[0]

    logger = logging.getLogger(logger_name)
    if not logger.hasHandlers():
        raise ValueError(f'Logger {logger_name} has no handlers. '
                         'Possible missing configuration!')

    return logger

@pytest.fixture(scope='class')
def api_client(
    request,
    setup_loggers,
    api_clients_configurations: ApiClientsConfigurationCollection
) -> BasicApiClient:
    '''Returns object inherited from `BasicApiClient` class.

       Actual class and options are selected by name defined in `@pytest.mark.api`
       and configured in API config file defined by cmd option `--api-config`
       under the same name
    '''
    api_name = request.node.get_closest_marker("api").args[0]
    return setup_api_client(api_name, api_clients_configurations)


@pytest.fixture(scope='function')
def api_request(api_client: BasicApiClient) -> ApiRequestHelper:
    '''Returns instance of `ApiRequestHelper` class.'''
    allure.dynamic.parameter('API', api_client.get_api_url())
    return ApiRequestHelper(api_client=api_client)
