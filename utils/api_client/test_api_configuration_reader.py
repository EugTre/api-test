"""Tests 'setup_api_client' function:

pytest -s -vv ./utils/api_client/test_api_configuration_reader.py
"""
import pytest
from utils.api_client.api_configuration_reader import ApiConfigurationReader
from utils.conftest import AppendableFilePath

TEST_API_NAME = 'TEST_API'

# Helper class

# --- Fixtures
@pytest.fixture(name='api_cfg_file')
def get_api_cfg_file(ini_file):
    """Provides unqiue path to api config file with minimal required data"""
    ini_file.write_text(f'[{TEST_API_NAME}]\n'
                        'url=http://foo.bar\n',
                        encoding='utf-8')
    return ini_file

@pytest.fixture(name='request_defaults')
def get_request_defaults():
    """Returns defaults for API Client requsts"""
    return {
        "timeout": None,
        "headers": {},
        "cookies": {},
        "auth": ()
    }

# --- Positive tests
def test_api_config_reader_empty_file(ini_file):
    """Api Config Reader reads empty file successfuly"""
    ini_file.write_text('', encoding='utf-8')

    api_specs = ApiConfigurationReader(str(ini_file)).read_configurations()
    assert api_specs.source_file == str(ini_file)
    assert isinstance(api_specs.configs, dict) and not api_specs.configs

def test_api_config_reader_required_fields_only(api_cfg_file, request_defaults):
    """Reads section with mandatory fields only (url)"""
    api_specs = ApiConfigurationReader(str(api_cfg_file)).read_configurations()
    assert api_specs.configs
    assert api_specs.configs['TEST_API']
    assert api_specs.configs['TEST_API'].name == 'TEST_API'
    assert api_specs.configs['TEST_API'].base_url == 'http://foo.bar'
    assert api_specs.configs['TEST_API'].endpoint == ''
    assert api_specs.configs['TEST_API'].client == \
        'utils.api_client.basic_api_client.BasicApiClient'
    assert api_specs.configs['TEST_API'].logger_name == ''

    assert api_specs.configs['TEST_API'].request_defaults == request_defaults
    assert isinstance(api_specs.configs['TEST_API'].request_catalog, dict) and \
        not api_specs.configs['TEST_API'].request_catalog

@pytest.mark.parametrize("cfg_prop, value, expected", [
    ('headers', '"key": "value"', {"key": "value"}),
    ('headers',
     '\n'
     '    "key1": "value1",\n'
     '    "key2": "value2"'
     , {
        "key1": "value1",
        "key2": "value2"
     }),
    ('cookies', '"key": "value"', {"key": "value"}),
    ('cookies',
     '\n'
     '    "key1": "value1",\n'
     '    "key2": "value2"'
     , {
        "key1": "value1",
        "key2": "value2"
     }),
    ('auth', '("user", "pass")', ("user", "pass"))
])
def test_api_config_reader_properties_as_key_value_pairs(api_cfg_file: AppendableFilePath,
                                                      request_defaults,
                                                      cfg_prop, value, expected):
    """Reads section with Headers as single key-value pair"""
    api_cfg_file.append_text(f'{cfg_prop} = {value}')
    request_defaults[cfg_prop] = expected

    api_specs = ApiConfigurationReader(str(api_cfg_file)).read_configurations()
    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME].request_defaults == request_defaults

@pytest.mark.parametrize("cfg_prop, value", [
    ('headers', {"key1": "value1", "key2": "value2"}),
    ('cookies', {"key1": "value1", "key2": "value2"}),
    ('auth', ['user', 'pass'])
])
def test_api_config_reader_properties_as_file(api_cfg_file: AppendableFilePath,
                                           json_file: AppendableFilePath,
                                           request_defaults: dict,
                                           cfg_prop: str, value):
    """Reads section with Headers as single key-value pair"""
    json_file.append_as_json(value)
    api_cfg_file.append_text(f'{cfg_prop} = {json_file}')

    api_specs = ApiConfigurationReader(str(api_cfg_file)).read_configurations()
    request_defaults[cfg_prop] = value if isinstance(value, dict) else tuple(value)

    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME].request_defaults == request_defaults

def test_api_config_reader_request_catalog_required_only_no_references(
    api_cfg_file: AppendableFilePath, json_file: AppendableFilePath, ):
    """Parsing of simple request catalog without references"""
    req_cat_data = {
        "Get": {
            "request": {
                "method": "GET",
                "path": ""
            },
            "response": {
                "status_code": 200
            }
        }
    }
    json_file.write_as_json(req_cat_data)
    api_cfg_file.append_text(f'requests = {json_file}')

    api_specs = ApiConfigurationReader(str(api_cfg_file)).read_configurations()

    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME].request_catalog['Get']

    req_entity = api_specs.configs[TEST_API_NAME].request_catalog['Get']
    assert req_entity.request.method == req_cat_data['Get']['request']['method']
    assert req_entity.request.path == req_cat_data['Get']['request']['path']
    assert req_entity.request.query_params == {}
    assert req_entity.request.path_params == {}
    assert req_entity.request.headers == {}
    assert req_entity.request.cookies == {}
    assert req_entity.request.auth is None
    assert req_entity.request.json is None
    assert req_entity.request.timeout is None

    assert req_entity.response.status_code == req_cat_data['Get']['response']['status_code']
    assert req_entity.response.schema is None
    assert req_entity.response.headers is None
    assert req_entity.response.json is None

def test_api_config_reader_request_catalog_full_no_references(
    api_cfg_file: AppendableFilePath, json_file: AppendableFilePath):
    """Parsing of fully qualified request catalog without references"""
    req_cat_data = {
        "Get": {
            "request": {
                "method": "GET",
                "path": "count",
                "query_params": {
                    "q": 1234
                },
                "path_params": {
                    "amount": 3
                },
                "headers": {"key1": "value1"},
                "cookies": {"key2": "value2"},
                "auth": ["user", "pass"],
                "json": {"item1": 1},
                "timeout": 5
            },
            "response": {
                "status_code": 200,
                "schema": {"a": "b"},
                "json": {"item2": 2},
                "headers": {"key3": "value3"}
            }
        }
    }
    json_file.write_as_json(req_cat_data)
    api_cfg_file.append_text(f'requests = {json_file}')

    api_specs = ApiConfigurationReader(api_cfg_file).read_configurations()

    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME].request_catalog['Get']

    req_entity = api_specs.configs[TEST_API_NAME].request_catalog['Get']
    assert req_entity.request.method == req_cat_data['Get']['request']['method']
    assert req_entity.request.path == req_cat_data['Get']['request']['path']
    assert req_entity.request.query_params == req_cat_data['Get']['request']['query_params']
    assert req_entity.request.path_params == req_cat_data['Get']['request']['path_params']
    assert req_entity.request.headers == req_cat_data['Get']['request']['headers']
    assert req_entity.request.cookies == req_cat_data['Get']['request']['cookies']
    assert req_entity.request.auth == req_cat_data['Get']['request']['auth']
    assert req_entity.request.json == req_cat_data['Get']['request']['json']
    assert req_entity.request.timeout == req_cat_data['Get']['request']['timeout']

    assert req_entity.response.status_code == req_cat_data['Get']['response']['status_code']
    assert req_entity.response.schema == req_cat_data['Get']['response']['schema']
    assert req_entity.response.headers == req_cat_data['Get']['response']['headers']
    assert req_entity.response.json == req_cat_data['Get']['response']['json']

def test_api_config_reader_request_catalog_with_references(
    api_cfg_file: AppendableFilePath, json_file: AppendableFilePath):
    """Parsing of request catalog with references"""
    req_cat_data = {
        "$defs": {
            "ref_string": "GET",
            "ref_dict": {"key1": "value1"}
        },
        "Get": {
            "request": {
                "method": "!ref /$defs/ref_string",
                "path": "count",
                "headers": "!ref /$defs/ref_dict",
                "cookies": "!ref /$defs/ref_dict",
            },
            "response": {
                "status_code": 200,
                "headers": "!ref /$defs/ref_dict",
            }
        }
    }
    json_file.write_as_json(req_cat_data)
    api_cfg_file.append_text(f'requests = {json_file}')

    api_specs = ApiConfigurationReader(api_cfg_file).read_configurations()

    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME].request_catalog['Get']

    compiled_req = api_specs.configs[TEST_API_NAME].request_catalog['Get']
    assert compiled_req.request.method == req_cat_data['$defs']['ref_string']
    assert compiled_req.request.path == req_cat_data['Get']['request']['path']
    assert compiled_req.request.headers == req_cat_data['$defs']['ref_dict']
    assert compiled_req.request.cookies == req_cat_data['$defs']['ref_dict']
    assert compiled_req.response.headers == req_cat_data['$defs']['ref_dict']

def test_api_config_reader_request_catalog_with_file_references(
    api_cfg_file: AppendableFilePath, get_file: AppendableFilePath):
    """Parsing of request catalog with file references"""

    req_catalog_file = get_file("req_cat", "json")
    ref_file = get_file("ref", "json")

    req_cat_data = {
        "Get": {
            "request": {
                "method": "GET",
                "path": "count",
                "headers": f"!file {ref_file}",
                "cookies": f"!file {ref_file}",
                "json": f"!file {ref_file}"
            },
            "response": {
                "status_code": 200,
                "headers": f"!file {ref_file}"
            }
        }
    }
    req_catalog_file.write_as_json(req_cat_data)

    expected = {"key1": "value1", "key2": "value2"}
    ref_file.write_as_json(expected)

    api_cfg_file.append_text(f'requests = {req_catalog_file}')
    api_specs = ApiConfigurationReader(str(api_cfg_file)).read_configurations()

    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME].request_catalog['Get']

    compiled_req = api_specs.configs[TEST_API_NAME].request_catalog['Get']
    assert compiled_req.request.headers == expected
    assert compiled_req.request.cookies == expected
    assert compiled_req.request.json == expected
    assert compiled_req.response.headers == expected

# --- Negative tests
def test_api_config_reader_empty_section(ini_file):
    """Api Config Reader reads empty file successfuly"""
    ini_file.write_text('[API_NAME]\n', encoding='utf-8')

    with pytest.raises(ValueError, match='There is no "url" defined for.*'):
        ApiConfigurationReader(str(ini_file)).read_configurations()

def test_api_config_reader_request_catalog_on_empty_fails(
    api_cfg_file: AppendableFilePath, json_file: AppendableFilePath):
    """Parsing of request catalog with file references"""
    json_file.write_text(' ', encoding='utf-8')
    api_cfg_file.append_text(f'requests = {json_file}')

    with pytest.raises(ValueError, match='Error on composing Request Catalog .*'):
        ApiConfigurationReader(api_cfg_file).read_configurations()

# TODO:
# Error on reading malformed config file

# Api Section have defaults cookies as malformed key-value
# Api Section have defaults headers as malformed key-value
# Api Section have defaults auth as malformed key-value

# Api Section have defaults headers as malformed file
# Api Section have defaults cookies as malformed file
# Api Section have defaults auth as malformed file

# Api Section have defaults headers as non exists file
# Api Section have defaults cookies as non exists file
# Api Section have defaults auth as non exists file

# Request Catalog - no required params
# Request Catalog - has non-exist refs
# Request Catalog - has malformed refs
# Request Catalog - has non-exists file ref
# Request Catalog - has malformed JSON file ref
