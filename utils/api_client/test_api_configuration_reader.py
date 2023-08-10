"""Tests 'setup_api_client' function:

pytest -s -vv ./utils/api_client/test_api_configuration_reader.py
"""
import shutil
import uuid
import json
from pathlib import Path

import pytest
from utils.api_client.api_configuration_reader import ApiConfigurationReader

TEST_API_NAME = 'TEST_API'

# Helper class
class AppendableFilePath(type(Path())):
    """Extension to Path class"""
    def append_text(self, text):
        """Append to file"""
        with self.open('a', encoding='utf-8') as file:
            file.write(text)

    def write_as_json(self, value):
        """Overwrite file, converting given data to JSON"""
        self.write_text(json.dumps(value), encoding='utf-8')

    def append_as_json(self, value):
        """Append to file, converting given data to JSON"""
        self.append_text(json.dumps(value))


# --- Fixtures
@pytest.fixture(name='tmp_folder', scope='session')
def handle_tmp_path(tmp_path_factory):
    """Creates temporary directory and deletes on session end"""
    tmpdir = tmp_path_factory.mktemp('api_config', numbered=False)
    yield tmpdir
    shutil.rmtree(tmpdir)

@pytest.fixture(name='api_cfg_file')
def get_api_cfg_file(tmp_folder):
    filename = tmp_folder / f'api_cfg_file_{uuid.uuid4()}.json'
    filename.write_text(f'[{TEST_API_NAME}]\nurl=http://foo.bar\n', encoding='utf-8')
    return AppendableFilePath(filename)

@pytest.fixture(name='req_catalog_file')
def get_req_catalog(tmp_folder):
    return AppendableFilePath(tmp_folder / f'api_request_catalog_{uuid.uuid4()}.json')

@pytest.fixture(name='request_defaults')
def get_request_defaults():
    return {
        "timeout": None,
        "headers": {},
        "cookies": {},
        "auth": ()
    }



# --- Positive tests
def test_api_config_reader_empty_file(tmp_folder):
    """Api Config Reader reads empty file successfuly"""
    filename = tmp_folder / "api_cfg_file.ini"
    filename_str = str(filename)
    filename.write_text('', encoding='utf-8')

    api_specs = ApiConfigurationReader(filename_str).read_configurations()
    assert api_specs.source_file == str(filename_str)
    assert isinstance(api_specs.configs, dict) and not api_specs.configs

def test_api_config_reader_required_fields_only(tmp_folder, request_defaults):
    """Reads section with mandatory fields only (url)"""
    filename = tmp_folder / "api_cfg_file_required_only.ini"
    filename.write_text('[TEST_API]\nurl=http://foo.bar\n', encoding='utf-8')

    api_specs = ApiConfigurationReader(filename).read_configurations()
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
def test_api_config_reader_properties_as_file(tmp_folder: Path,
                                           api_cfg_file: AppendableFilePath,
                                           request_defaults: dict,
                                           cfg_prop: str, value):
    """Reads section with Headers as single key-value pair"""
    file = AppendableFilePath(tmp_folder / f'api_{cfg_prop}_{uuid.uuid4()}.json')
    file.append_as_json(value)
    api_cfg_file.append_text(f'{cfg_prop} = {file}')

    api_specs = ApiConfigurationReader(str(api_cfg_file)).read_configurations()
    request_defaults[cfg_prop] = value if isinstance(value, dict) else tuple(value)

    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME].request_defaults == request_defaults

def test_api_config_reader_request_catalog_required_only_no_references(
    tmp_folder, api_cfg_file: AppendableFilePath):
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
    req_cat = AppendableFilePath(tmp_folder / f'api_request_catalog_{uuid.uuid4()}.json')
    req_cat.write_as_json(req_cat_data)
    api_cfg_file.append_text(f'requests = {req_cat}')

    api_specs = ApiConfigurationReader(api_cfg_file).read_configurations()

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

def test_api_config_reader_request_catalog_full_no_references(req_catalog_file: AppendableFilePath,
                                                              api_cfg_file: AppendableFilePath):
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
    req_catalog_file.write_as_json(req_cat_data)
    api_cfg_file.append_text(f'requests = {req_catalog_file}')

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
    api_cfg_file: AppendableFilePath, req_catalog_file: AppendableFilePath):
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
    req_catalog_file.write_as_json(req_cat_data)
    api_cfg_file.append_text(f'requests = {req_catalog_file}')

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
    tmp_folder: Path,
    api_cfg_file: AppendableFilePath, req_catalog_file: AppendableFilePath):
    """Parsing of request catalog with file references"""
    data_file = tmp_folder / "api_file_ref.json"

    req_cat_data = {
        "Get": {
            "request": {
                "method": "GET",
                "path": "count",
                "headers": f"!file {data_file}",
                "cookies": f"!file {data_file}",
                "json": f"!file {data_file}"
            },
            "response": {
                "status_code": 200,
                "headers": f"!file {data_file}"
            }
        }
    }
    expected = {"key1": "value1", "key2": "value2"}

    AppendableFilePath(data_file).write_as_json(expected)
    req_catalog_file.write_as_json(req_cat_data)
    api_cfg_file.append_text(f'requests = {req_catalog_file}')

    api_specs = ApiConfigurationReader(api_cfg_file).read_configurations()

    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME].request_catalog['Get']

    compiled_req = api_specs.configs[TEST_API_NAME].request_catalog['Get']
    assert compiled_req.request.headers == expected
    assert compiled_req.request.cookies == expected
    assert compiled_req.request.json == expected
    assert compiled_req.response.headers == expected

# --- Negative tests
def test_api_config_reader_empty_section(tmp_folder):
    """Api Config Reader reads empty file successfuly"""
    filename = tmp_folder / "api_cfg_file.ini"
    filename_str = str(filename)
    filename.write_text('[API_NAME]\n', encoding='utf-8')

    with pytest.raises(ValueError, match='There is no "url" defined for.*'):
        ApiConfigurationReader(filename_str).read_configurations()

def test_api_config_reader_request_catalog_on_empty_fails(
    api_cfg_file: AppendableFilePath, req_catalog_file: AppendableFilePath):
    """Parsing of request catalog with file references"""
    req_catalog_file.write_text(' ', encoding='utf-8')
    api_cfg_file.append_text(f'requests = {req_catalog_file}')

    with pytest.raises(ValueError, match='Error on composing Request Catalog .*'):
        ApiConfigurationReader(api_cfg_file).read_configurations()








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