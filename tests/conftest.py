"""Test related helpers"""
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

from utils.api_client.simple_api_client import BaseApiClient
from utils.api_helpers.api_request_helper import ApiRequestHelper
from utils.api_helpers.api_response_helper import ApiResponseHelper


def perform_logger_setup(logging_config_file: str):
    """Setups loggers using given configuration file"""
    if not os.path.exists(logging_config_file):
        raise FileNotFoundError(
            'Missing logging config file provided by --logging-config option '
            f'with name "{logging_config_file}".'
        )

    logging.handlers.DatabaseHandler = DatabaseHandler
    fileConfig(logging_config_file)


def prepare_api_clients_configurations(
    api_config_file: str
) -> ApiClientsSpecificationCollection:
    """Setups api by configuration provided by --api-config command-line
    argument"""
    if not os.path.exists(api_config_file):
        raise FileNotFoundError(
            'Missing API config file provided by `--api-config` option '
            f'with name "{api_config_file}".'
        )

    return ApiConfigurationReader(api_config_file).read_configurations()


# --- Initialization hooks ----
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
    config.addinivalue_line("markers",
                            "request(names): used by api_request/api_response"
                            "fixture to pre-select request from catalog")

    # Setup logging from file passed in cmd args
    perform_logger_setup(config.getoption("--logging-config"))

    # Setup API configuration from file parsed in cmd args
    pytest.api_config = prepare_api_clients_configurations(
        config.getoption("--api-config")
    )

# --- Common fixtures ---
# ----------------------
@pytest.fixture(name='logger')
def get_logger(request):
    """Returns logger defined by name defined by tests
    mark @pytest.mark.logger()"""
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
def get_api_client(request) -> BaseApiClient:
    '''Returns API Client object of class that implements
    `AbstractApiClient` class using API name provided by
    '@pytest.mark.api(...)' test mark.

    Actual class and it's configuration is selected by given name that
    should be configured in API config file (defined by cli option
    `--api-config` under the same name)
    '''
    api_name = request.node.get_closest_marker("api").args[0]
    return setup_api_client(api_name, pytest.api_config)


@pytest.fixture(name='api_request')
def get_api_request_instance(api_client: BaseApiClient,
                             request) -> ApiRequestHelper:
    '''Returns instance of `ApiRequestHelper` class.'''
    allure.dynamic.parameter('API', api_client.get_api_url())

    api_request = ApiRequestHelper(api_client=api_client)

    request_mark = request.node.get_closest_marker('request')
    if request_mark is None:
        return api_request

    return api_request.by_name(request_mark.args[0])


@pytest.fixture(name='api_response')
def get_api_response_instance(api_request: ApiRequestHelper
                              ) -> ApiResponseHelper:
    """Performs request and return response wrapped in
    `ApiResponseHelper` class.
    Requires `@pytest.mark.request('request_name')` mark for test."""
    return api_request.perform()


# --- Other fixtures ----
@pytest.fixture
def test_id(request):
    """Returns ID for parametrized test (like 'param1-param2-param3')."""
    return request.node.callspec.id


@pytest.fixture(scope='session')
def helper() -> Helper:
    """Returns `Helper` class object to use inside tests/fixtures"""
    return Helper()
