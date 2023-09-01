"""Tests 'setup_api_client' function:

pytest -s -vv ./utils/api_client/test_setup_api_client.py
"""
import pytest
from utils.conftest import AppendableFilePath
from utils.api_client.api_configuration_reader import ApiConfigurationReader
from utils.api_client.setup_api_client import setup_api_client
from utils.api_client.basic_api_client import DEFAULT_TIMEOUT

# Constnats
API_NAME = "TEST_API"

# Tests
# --- Positive tests
def test_setup_api_client_no_requests(json_file: AppendableFilePath):
    """Initialize ApiClient, with defaults and winthout requests"""
    expected_fq_url = 'http://some.com/api'
    content = {
        "url": 'http://some.com/',
        "endpoint": 'api',
        "client": 'utils.api_client.basic_api_client.BasicApiClient'
    }

    json_file.write_as_json({  API_NAME: content })

    configs = ApiConfigurationReader(str(json_file)).read_configurations()
    api_client = setup_api_client(API_NAME, configs)

    assert api_client.base_url == content['url'].rstrip('/')
    assert api_client.endpoint == content['endpoint']
    assert api_client.name == API_NAME
    assert api_client.logger is None
    assert api_client.request_defaults == {'timeout': DEFAULT_TIMEOUT,
                                           'headers': None,
                                           'cookies': None,
                                           'auth': None}
    assert api_client.request_catalog is None
    assert api_client.get_api_url() == expected_fq_url

def test_setup_api_clint_request_defaults_applied(json_file: AppendableFilePath):
    """Initialize ApiClient, with request defaults"""
    headers = {"header1": "value1"}
    auth = ("user", "pass")
    cookies = {"cookie1": "value2"}
    timeout = 20

    content = {
        'url': 'http://some.com/',
        'endpoint': '/api',
        'client': 'utils.api_client.basic_api_client.BasicApiClient',
        'headers': headers,
        'cookies': cookies,
        'auth': auth,
        'timeout': timeout
    }

    json_file.write_as_json({ API_NAME: content })

    configs = ApiConfigurationReader(str(json_file)).read_configurations()
    api_client = setup_api_client(API_NAME, configs)

    assert api_client.request_defaults['headers'] == headers
    assert api_client.request_defaults['cookies'] == cookies
    assert api_client.request_defaults['auth'] == auth
    assert api_client.request_defaults['timeout'] == timeout

def test_setup_api_client_with_request_catalog(get_file):
    """Initialize ApiClient with request catalog"""
    cfg_file = get_file(ext='json')
    req_cat_file = get_file(ext='json')

    content = {
        'url': 'http://some.com/',
        'endpoint': '/api',
        'client': 'utils.api_client.basic_api_client.BasicApiClient',
        'requests': {"!include": str(req_cat_file)}
    }
    req_catalog = {
        "GetImage": {
            "request": {
                "method": "GET",
                "path": "path/to/"
            },
            "response": {
                "status_code": 200
            }
        }
    }

    cfg_file.write_as_json({API_NAME: content})
    req_cat_file.write_as_json(req_catalog)

    configs = ApiConfigurationReader(str(cfg_file)).read_configurations()
    api_client = setup_api_client(API_NAME, configs)

    assert api_client.request_catalog != {}
    assert api_client.get_from_catalog("GetImage")
    assert api_client.get_from_catalog("GetImage").request.method == \
        req_catalog['GetImage']['request']['method']
    assert api_client.get_from_catalog("GetImage").request.path == \
        req_catalog['GetImage']['request']['path']
    assert api_client.get_from_catalog("GetImage").response.status_code == \
        req_catalog['GetImage']['response']['status_code']

# --- Negative tests
def test_setup_api_client_no_config_fails(json_file: AppendableFilePath):
    """ApiClient setup fails if API name can't be retrieved from config"""
    json_file.write_as_json({
        API_NAME: {
            'url': 'http://some.com/',
            'endpoint': '/api',
            'client': 'utils.api_client.basic_api_client.BasicApiClient'
        }
    })

    configs = ApiConfigurationReader(str(json_file)).read_configurations()
    with pytest.raises(ValueError, match="There is no config for API .* in .*"):
        setup_api_client("NON_EXISTENT", configs)

def test_setup_api_client_invalid_client_module_fails(json_file: AppendableFilePath):
    """ApiClient setup fails if API config contains invalid client class"""
    json_file.write_as_json({
        API_NAME: {
            'url': 'http://some.com/',
            'endpoint': '/api',
            'client': 'utils.api_client.unknown.ApiClient'
        }
    })

    configs = ApiConfigurationReader(str(json_file)).read_configurations()
    with pytest.raises(ModuleNotFoundError,
                       match=f'Failed to find API client module named .* for "{API_NAME}".*'):
        setup_api_client(API_NAME, configs)

def test_setup_api_client_invalid_client_class_fails(json_file: AppendableFilePath):
    """ApiClient setup fails if API config contains invalid client class"""
    json_file.write_as_json({
        API_NAME: {
            'url': 'http://some.com/',
            'endpoint': '/api',
            'client': 'utils.api_client.basic_api_client.BasicApiClient3'
        }
    })

    configs = ApiConfigurationReader(str(json_file)).read_configurations()
    with pytest.raises(ModuleNotFoundError,
                       match='Failed to find API client class "BasicApiClient3" in '
                              "module 'utils.api_client.basic_api_client'.*"):
        setup_api_client(API_NAME, configs)
