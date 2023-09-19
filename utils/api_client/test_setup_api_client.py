"""Tests 'setup_api_client' function:

pytest -s -vv ./utils/api_client/test_setup_api_client.py
"""
import pytest
from utils.conftest import AppendableFilePath
from .api_configuration_reader import ApiConfigurationReader
from .setup_api_client import setup_api_client
from .simple_api_client import DEFAULT_TIMEOUT
from .models import ApiClientIdentificator

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
        "client": 'utils.api_client.simple_api_client.SimpleApiClient'
    }

    json_file.write_as_json({  API_NAME: content })

    configs = ApiConfigurationReader(str(json_file)).read_configurations()
    api_client = setup_api_client(API_NAME, configs)

    assert api_client.base_url == content['url'].rstrip('/')
    assert api_client.endpoint == content['endpoint']

    assert isinstance(api_client.client_id, ApiClientIdentificator)
    assert  API_NAME in api_client.client_id.instance_id
    assert api_client.client_id.api_name == API_NAME
    assert api_client.client_id.url == f"{content['url']}{content['endpoint']}"

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
        'client': 'utils.api_client.simple_api_client.SimpleApiClient',
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
        'client': 'utils.api_client.simple_api_client.SimpleApiClient',
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
            'client': 'utils.api_client.simple_api_client.SimpleApiClient'
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
            'client': 'utils.api_client.simple_api_client.SimpleApiClient3'
        }
    })

    configs = ApiConfigurationReader(str(json_file)).read_configurations()
    with pytest.raises(ModuleNotFoundError,
                       match='Failed to find API client class "SimpleApiClient3" in '
                              "module 'utils.api_client.simple_api_client'.*"):
        setup_api_client(API_NAME, configs)
