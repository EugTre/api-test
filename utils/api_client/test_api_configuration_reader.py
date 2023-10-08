"""Tests 'setup_api_client' function:

pytest -s -vv ./utils/api_client/test_api_configuration_reader.py
"""
import json
from dataclasses import asdict

import pytest
from utils.conftest import AppendableFilePath
from .api_configuration_reader import ApiConfigurationReader

TEST_API_NAME = 'TEST_API'

# --- Positive tests
def test_api_config_reader_required_fields_only(json_file: AppendableFilePath):
    """Reads section with mandatory fields only (url)"""

    json_file.write_as_json({
        TEST_API_NAME: {
            'url': 'http://foo.bar'
        }
    })

    api_specs = ApiConfigurationReader(str(json_file)).read_configurations()
    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME]
    assert api_specs.configs[TEST_API_NAME].name == TEST_API_NAME
    assert api_specs.configs[TEST_API_NAME].base_url == 'http://foo.bar'
    assert api_specs.configs[TEST_API_NAME].endpoint == ''
    assert api_specs.configs[TEST_API_NAME].client_class == \
        'utils.api_client.simple_api_client.SimpleApiClient'
    assert api_specs.configs[TEST_API_NAME].logger_name == None

    assert api_specs.configs[TEST_API_NAME].request_defaults == {
        "timeout": None,
        "headers": None,
        "cookies": None,
        "auth": None
    }
    assert api_specs.configs[TEST_API_NAME].request_catalog is None

def test_api_config_reader_request_catalog_required_only_no_references(get_file):
    """Parsing of simple request catalog without references"""
    cfg_file = get_file(ext='json')
    req_cat_file = get_file(ext='json')

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

    cfg_file.write_as_json({
        TEST_API_NAME: {
            "url": "http://example.com",
            "requests": {"!include": str(req_cat_file)}
        }
    })
    req_cat_file.write_as_json(req_cat_data)

    api_specs = ApiConfigurationReader(str(cfg_file)).read_configurations()

    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME].request_catalog['Get']

    req_entity = api_specs.configs[TEST_API_NAME].request_catalog['Get']
    assert asdict(req_entity.request) == {
                "method": "GET",
                "path": "",
                "query_params": None,
                "path_params": None,
                "headers": None,
                "cookies": None,
                "auth": None,
                "json": None,
                "text": None,
                "timeout": None
            }
    assert asdict(req_entity.response) == {
                "status_code": 200,
                "schema": None,
                "json": None,
                "headers": None,
                "text": None
            }

def test_api_config_reader_request_catalog_full_no_references(get_file):
    """Parsing of fully qualified request catalog without references"""
    api_cfg_file = get_file(ext='json')
    req_cat_file = get_file(ext='json')

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
                "text": None,
                "timeout": 5
            },
            "response": {
                "status_code": 200,
                "schema": {"a": "b"},
                "json": {"item2": 2},
                "headers": {"key3": "value3"},
                "text": None
            }
        }
    }
    req_cat_file.write_as_json(req_cat_data)
    api_cfg_file.write_as_json({
        TEST_API_NAME: {
            "url": "http://example.com",
            "requests": {"!include": str(req_cat_file)}
        }
    })

    api_specs = ApiConfigurationReader(api_cfg_file).read_configurations()

    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME].request_catalog['Get']

    req_entity = api_specs.configs[TEST_API_NAME].request_catalog['Get']
    assert asdict(req_entity.request) == req_cat_data['Get']['request']
    assert asdict(req_entity.response) == req_cat_data['Get']['response']

def test_api_config_reader_request_catalog_with_references(get_file):
    """Parsing of request catalog with references"""
    api_cfg_file = get_file(ext='json')
    req_cat_file = get_file(ext='json')

    req_cat_data = {
        "$defs": {
            "ref_string": "GET",
            "ref_dict": {"key1": "value1"}
        },
        "Get": {
            "request": {
                "method": {"!ref": "/$defs/ref_string"},
                "path": "count",
                "headers": {"!ref": "/$defs/ref_dict"},
                "cookies": {"!ref": "/$defs/ref_dict"},
            },
            "response": {
                "status_code": 200,
                "headers": {"!ref": "/$defs/ref_dict"},
            }
        }
    }

    req_cat_file.write_as_json(req_cat_data)
    api_cfg_file.write_as_json({
        TEST_API_NAME: {
            "url": "http://example.com",
            "requests": {
                "!include": str(req_cat_file),
                "$compose": True
            }
        }
    })

    api_specs = ApiConfigurationReader(api_cfg_file).read_configurations()

    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME].request_catalog['Get']

    compiled_req = api_specs.configs[TEST_API_NAME].request_catalog['Get']
    assert compiled_req.request.method == req_cat_data['$defs']['ref_string']
    assert compiled_req.request.path == req_cat_data['Get']['request']['path']
    assert compiled_req.request.headers == req_cat_data['$defs']['ref_dict']
    assert compiled_req.request.cookies == req_cat_data['$defs']['ref_dict']
    assert compiled_req.response.headers == req_cat_data['$defs']['ref_dict']

def test_api_config_reader_request_catalog_with_file_references(get_file):
    """Parsing of request catalog with file references"""

    api_cfg_file = get_file(ext='json')
    req_cat_file = get_file("req_cat", "json")
    ref_file = get_file("ref", "json")

    req_cat_data = {
        "Get": {
            "request": {
                "method": "GET",
                "path": "count",
                "headers": {"!file": str(ref_file)},
                "cookies": {"!file": str(ref_file)},
                "json": {"!file": str(ref_file)}
            },
            "response": {
                "status_code": 200,
                "headers": {"!file": str(ref_file)},
            }
        }
    }
    ref_file_data = {"key1": "value1", "key2": "value2"}

    req_cat_file.write_as_json(req_cat_data)
    ref_file.write_as_json(ref_file_data)
    api_cfg_file.write_as_json({
        TEST_API_NAME: {
            "url": "http://example.com",
            "requests": {
                "!include": str(req_cat_file),
                "$compose": True
            }
        }
    })

    api_specs = ApiConfigurationReader(str(api_cfg_file)).read_configurations()

    assert api_specs.configs
    assert api_specs.configs[TEST_API_NAME].request_catalog['Get']

    compiled_req = api_specs.configs[TEST_API_NAME].request_catalog['Get']
    assert compiled_req.request.headers == ref_file_data
    assert compiled_req.request.cookies == ref_file_data
    assert compiled_req.request.json == ref_file_data
    assert compiled_req.response.headers == ref_file_data

# --- Negative tests
def test_api_config_reader_empty_file_fails(json_file):
    """Api Config Reader reads empty file successfuly"""
    json_file.write_text('', encoding='utf-8')

    with pytest.raises(Exception):
        ApiConfigurationReader(str(json_file)).read_configurations()

def test_api_config_reader_empty_section(json_file):
    """Api Config Reader reads empty file successfuly"""
    json_file.write_as_json({
        TEST_API_NAME: {}
    })

    with pytest.raises(ValueError, match='There is no "url" defined for.*'):
        ApiConfigurationReader(str(json_file)).read_configurations()

def test_api_config_reader_request_catalog_on_empty_fails(get_file):
    """Parsing of request catalog with file references"""
    api_cfg_file = get_file(ext='json')
    req_cat_file = get_file(ext='json')

    req_cat_file.write_text(' ', encoding='utf-8')
    api_cfg_file.write_as_json({
        TEST_API_NAME: {
            "url": "http://example.com",
            "requests": {"!include": str(req_cat_file)}
        }
    })

    with pytest.raises(json.decoder.JSONDecodeError):
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
