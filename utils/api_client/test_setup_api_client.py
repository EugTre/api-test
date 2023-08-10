"""Tests 'setup_api_client' function:

pytest -s -vv ./utils/api_client/test_setup_api_client.py
"""
import shutil
import pathlib
import json

import pytest
from utils.api_client.api_configuration_reader import ApiConfigurationReader
from utils.api_client.setup_api_client import setup_api_client

@pytest.fixture(name='tmp_folder', scope='session')
def handle_tmp_path(tmp_path_factory):
    """Creates temporary directory and deletes on session end"""
    tmpdir = tmp_path_factory.mktemp('api_config', numbered=False)
    yield tmpdir
    shutil.rmtree(tmpdir)


def test_setup_api_client_no_requests(tmp_folder: pathlib.Path):
    """Initialize ApiClient, with defaults and winthout requests"""
    filename = tmp_folder / "api_cfg.ini"
    filename.write_text('[API_NAME]\n\n'
                        'url = http://some.com/\n'
                        'endpoint = /api\n'
                        'client = utils.api_client.basic_api_client.BasicApiClient\n',
                        encoding='utf-8')
    configs = ApiConfigurationReader(filename).read_configurations()
    api_client = setup_api_client("API_NAME", configs)

    assert api_client.base_url == 'http://some.com'
    assert api_client.endpoint == 'api'
    assert api_client.name == 'API_NAME'
    assert api_client.logger is None
    assert api_client.request_defaults == {'timeout': 240, 'headers': {}, 'cookies': {}, 'auth': ()}
    assert api_client.request_catalog == {}
    assert api_client.get_api_url() == 'http://some.com/api/'

def test_setup_api_clint_request_defaults_applied(tmp_folder: pathlib.Path):
    """Initialize ApiClient, with request defaults"""
    headers = {"header1": "value1"}
    auth = ("user", "pass")
    cookies = {"cookie1": "value2"}
    timeout = 20

    header_str = '"header1": "value1"'
    cookies_str = '"cookie1": "value2"'

    filename = tmp_folder / "api_cfg_with_defaults.ini"
    filename.write_text('[API_NAME]\n\n'
                        'url = http://some.com/\n'
                        'endpoint = /api\n'
                        'client = utils.api_client.basic_api_client.BasicApiClient\n'
                        f'headers = {header_str}\n'
                        f'auth = {auth}\n'
                        f'cookies = {cookies_str}\n'
                        f'timeout = {timeout}\n',
                        encoding='utf-8')
    configs = ApiConfigurationReader(filename).read_configurations()
    api_client = setup_api_client("API_NAME", configs)

    assert api_client.request_defaults['headers'] == headers
    assert api_client.request_defaults['cookies'] == cookies
    assert api_client.request_defaults['auth'] == auth
    assert api_client.request_defaults['timeout'] == timeout

def test_setup_api_client_with_request_catalog(tmp_folder: pathlib.Path):
    """Initialize ApiClient with request catalog"""
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

    filename = tmp_folder / "api_cfg_with_request_catalog.ini"
    request_catalog_filename = tmp_folder / "requests.json"
    filename.write_text('[API_NAME]\n\n'
                        'url = http://some.com/\n'
                        'endpoint = /api\n'
                        'client = utils.api_client.basic_api_client.BasicApiClient\n'
                        f'requests = {request_catalog_filename}\n',
                        encoding='utf-8')
    request_catalog_filename.write_text(json.dumps(req_catalog))

    configs = ApiConfigurationReader(filename).read_configurations()
    api_client = setup_api_client("API_NAME", configs)

    assert api_client.request_catalog != {}
    assert api_client.get_from_catalog("GetImage")
    assert api_client.get_from_catalog("GetImage").request.method == \
        req_catalog['GetImage']['request']['method']
    assert api_client.get_from_catalog("GetImage").request.path == \
        req_catalog['GetImage']['request']['path']
    assert api_client.get_from_catalog("GetImage").response.status_code == \
        req_catalog['GetImage']['response']['status_code']

# --- Negative tests
def test_setup_api_client_no_config_fails(tmp_folder: pathlib.Path):
    """ApiClient setup fails if API name can't be retrieved from config"""
    filename = tmp_folder / "api_cfg.ini"
    filename.write_text('[API_NAME]\n'
                        'url = http://some.com/\n'
                        'endpoint = /api\n'
                        'client = utils.api_client.basic_api_client.BasicApiClient\n',
                        encoding='utf-8')

    configs = ApiConfigurationReader(filename).read_configurations()
    with pytest.raises(ValueError, match="There is no config for API .* in .*"):
        setup_api_client("NON_EXISTENT", configs)

def test_setup_api_client_invalid_client_module_fails(tmp_folder: pathlib.Path):
    """ApiClient setup fails if API config contains invalid client class"""
    api_name = "API_NAME"
    filename = tmp_folder / "api_cfg.ini"
    filename.write_text(f'[{api_name}]\n'
                        'url = http://some.com/\n'
                        'endpoint = /api\n'
                        'client = utils.api_client.unknwon.ApiClient\n',
                        encoding='utf-8')

    configs = ApiConfigurationReader(filename).read_configurations()
    with pytest.raises(ModuleNotFoundError,
                       match=f'Failed to find API client module named .* for "{api_name}".*'):
        setup_api_client(api_name, configs)

def test_setup_api_client_invalid_client_class_fails(tmp_folder: pathlib.Path):
    """ApiClient setup fails if API config contains invalid client class"""
    api_name = "API_NAME"
    filename = tmp_folder / "api_cfg.ini"
    filename.write_text(f'[{api_name}]\n'
                        'url = http://some.com/\n'
                        'endpoint = /api\n'
                        'client = utils.api_client.basic_api_client.BasicApiClient3\n',
                        encoding='utf-8')

    configs = ApiConfigurationReader(filename).read_configurations()
    with pytest.raises(ModuleNotFoundError,
                       match='Failed to find API client class "BasicApiClient3" in '
                              "module 'utils.api_client.basic_api_client'.*"):
        setup_api_client(api_name, configs)
