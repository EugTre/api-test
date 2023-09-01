"""
Test related helpers
"""
import os
import logging.handlers
from logging.config import fileConfig

import allure
import pytest

from utils.api_client.models import ApiClientsSpecificationCollection
from utils.api_client.setup_api_client import setup_api_client
from utils.api_client.api_configuration_reader import ApiConfigurationReader

from utils.helper import Helper
from utils.log_database_handler import DatabaseHandler

from utils.api_client.basic_api_client import AbstractApiClient
from utils.api_helpers.api_request_helper import ApiRequestHelper

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
        default="config/api_clients.json",
        help="Configuration file for API Clients"
    )

def pytest_configure(config):
    """Registers custom pytest markers"""
    config.addinivalue_line("markers",
                            "api(name): set name of API Client to use")
    config.addinivalue_line("markers",
                            "logger(name): set name of logger to use")


@pytest.fixture(scope='session')
def helper() -> Helper:
    """Returns `Helper` class object to use inside tests/fixtures"""
    return Helper()

# --- Setup fixtures ---
# Read configs of loggers and api clients, setup loggers and
# compile api clients specification
@pytest.fixture(scope='session', name='setup_loggers')
def perform_logger_setup(request):
    """Setups loggers by configuration provided by --logging-config command-line argument"""
    logger_config = request.config.getoption("--logging-config")

    if not os.path.exists(logger_config):
        raise FileNotFoundError(
            'Missing logging config file provided by --logging-config option '
            f'with name "{logger_config}".'
        )

    logging.handlers.DatabaseHandler = DatabaseHandler
    fileConfig(logger_config)

@pytest.fixture(scope='session', name='api_clients_configurations')
def configure_api_clients(request, setup_loggers) -> ApiClientsSpecificationCollection:
    """Setups api by configuration provided by --api-config command-line argument"""
    # pylint: disable=unused-argument
    api_config_file = request.config.getoption("--api-config")

    if not os.path.exists(api_config_file):
        raise FileNotFoundError(
            'Missing API config file provided by `--api-config` option '
            f'with name "{api_config_file}".'
        )

    return ApiConfigurationReader(api_config_file).read_configurations()


@pytest.fixture(name='logger')
def get_logger(request):
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


@pytest.fixture(scope='class', name="api_client")
def get_api_client(
    request,
    api_clients_configurations: ApiClientsSpecificationCollection
) -> AbstractApiClient:
    '''Returns API Client object of class that implements
    `AbstractApiClient` class using API name provided by '@pytest.mark.api(...)'
    test mark.

    Actual class and it's configuration is selected by given name that
    should be configured in API config file (defined by cli option
    `--api-config` under the same name)
    '''
    api_name = request.node.get_closest_marker("api").args[0]
    return setup_api_client(api_name, api_clients_configurations)


@pytest.fixture(name='api_request')
def get_api_request_instance(api_client: AbstractApiClient) -> ApiRequestHelper:
    '''Returns instance of `ApiRequestHelper` class.'''
    allure.dynamic.parameter('API', api_client.get_api_url())
    return ApiRequestHelper(api_client=api_client)
