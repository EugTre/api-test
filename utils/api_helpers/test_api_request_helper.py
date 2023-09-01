"""Tests for Api Request Helper class

pytest -s -vv ./utils/api_helpers/test_api_request_helper.py
"""
import re

import pytest
from utils.api_helpers.api_request_helper import ApiRequestHelper
from utils.api_client.basic_api_client import BasicApiClient
from utils.api_client.models import RequestCatalogEntity, RequestEntity, ResponseEntity
from utils.matchers import Anything

REQUEST_NAME_1 = "GetItem"
REQUEST_CONFIGURED_1 = RequestEntity(
    method="GET",
    path="items/{amount}",
    path_params={"amount": 4},
    query_params={"page": 1}
)
RESPONSE_CONFIGURED_1 = ResponseEntity(
    status_code=200,
    schema={"this": "is_schema"}
)

REQUEST_NAME_2 = "UpdateItem"
REQUEST_CONFIGURED_2 = RequestEntity(
    method="POST",
    path="items/{node}/update/{id}",
    path_params=None,
    query_params=None,
    json={
        "type": 10,
        "price": 100500
    },
    headers={"Foo": "Bar"},
    cookies={'Foo': 'Baz'}
)
RESPONSE_CONFIGURED_2 = ResponseEntity(
    status_code=200,
    schema={"this": "is_schema"},
    json={
        "id": Anything(),
        "type": 10,
        "price": 100500
    }
)

API_CLIENT_CONFIG = {
    'base_url': "http://example.com",
    'endpoint': "v1",
    'name': 'TestAPI',
    'request_catalog': {
        REQUEST_NAME_1: RequestCatalogEntity(
            REQUEST_NAME_1,
            request=RequestEntity(
                method="GET",
                path="items/{amount}",
                path_params={
                    "amount": 4,
                    "@use": ["amount"]
                },
                query_params={
                    "page": 1,
                    "@use": ["page"]
                }
            ),
            response=RESPONSE_CONFIGURED_1
        ),
        REQUEST_NAME_2: RequestCatalogEntity(
            REQUEST_NAME_2,
            request=RequestEntity(
                method=REQUEST_CONFIGURED_2.method,
                path=REQUEST_CONFIGURED_2.path,
                path_params={"id": 10},
                query_params=None,
                headers=REQUEST_CONFIGURED_2.headers,
                cookies=REQUEST_CONFIGURED_2.cookies,
                json=REQUEST_CONFIGURED_2.json
            ),
            response=RESPONSE_CONFIGURED_2
        )
    }
}

@pytest.fixture(name='client', scope='session')
def get_api_client() -> BasicApiClient:
    return BasicApiClient(API_CLIENT_CONFIG)


@pytest.fixture(name='client_requestless', scope='session')
def get_api_client_no_requests() -> BasicApiClient:
    return BasicApiClient({
        'base_url': "http://example.com",
        'endpoint': "v1",
        'name': 'TestAPI',
        'request_catalog': None
    })

class TestApiRequestHelper:
    # --- Positive test
    def test_prepare_request_by_name(self, client):
        """Request may be selected and pre-configured by name"""
        api = ApiRequestHelper(client).by_name(REQUEST_NAME_1)

        print('Api.Request:')
        print(api.request)
        print('Api.Expected:')
        print(api.expected)

        assert api.request == REQUEST_CONFIGURED_1
        assert api.expected == RESPONSE_CONFIGURED_1

    def test_prepare_custom_request(self, client):
        """Prepare custom request with custom params"""
        header = {"Foo": "Bar"}
        query_param = {"id": 100500}
        expected_request = RequestEntity(
            method='POST',
            path='user',
            headers=header,
            query_params=query_param
        )
        expected_response_code = 200

        api = ApiRequestHelper(client).by_path(
            path=expected_request.path,
            method=expected_request.method,
            status_code=expected_response_code
        ).with_query_params(id=query_param['id']) \
            .with_headers(header)

        assert api.request == expected_request
        assert api.expected == ResponseEntity(
            status_code=expected_response_code
        )

    def test_prepare_customized_request(self, client):
        """Request may be overwritten with various methods"""
        path_params = {'amount': 44}
        query_params = {'page': 55}
        headers = {'Foo': 'Bar'}
        cookies = {'foo': 'bar'}
        json_data = {'a': 100}

        api = ApiRequestHelper(client).by_name(REQUEST_NAME_1) \
                .with_path_params(**path_params) \
                .with_query_params(**query_params) \
                .with_headers(headers) \
                .with_cookies(cookies) \
                .with_json_payload(json_data)

        print(api.request)

        assert api.request == RequestEntity(
            method=REQUEST_CONFIGURED_1.method,
            path=REQUEST_CONFIGURED_1.path,
            headers=headers,
            cookies=cookies,
            path_params=path_params,
            query_params=query_params,
            json=json_data
        )
        assert api.expected == RESPONSE_CONFIGURED_1

    def test_append_params(self, client):
        """Params append already defined params"""

        api = ApiRequestHelper(client) \
            .by_path(method="GET", path="") \
            .with_path_params(id1=100500) \
            .with_path_params(id2=201000) \
            .with_query_params(p1=100) \
            .with_query_params(p2=200) \
            .with_headers({'Test': 'New'}) \
            .with_headers({'Test2': 'New'}) \
            .with_cookies({'TestCookie': 'New'}) \
            .with_cookies({'TestCookie2': 'New'}) \

        assert api.request == RequestEntity(
            method="GET",
            path="",
            path_params={"id1": 100500, "id2": 201000},
            query_params={"p1": 100, "p2": 200},
            headers={"Test": "New", "Test2": "New"},
            cookies={"TestCookie": "New", "TestCookie2": "New"}
        )

    def test_overwrite_params(self, client):
        """Params may be overwritten"""
        api = ApiRequestHelper(client) \
            .by_path(method="GET", path="") \
            .with_path_params(id1=100500) \
            .with_query_params(p1=100) \
            .with_headers({'Test': 'New'}) \
            .with_cookies({'TestCookie': 'New'})

        api.with_headers({'Test2': 'New'}, True) \
            .with_cookies({'TestCookie2': 'New'}, True) \

        assert api.request == RequestEntity(
            method="GET",
            path="",
            path_params={"id1": 100500},
            query_params={"p1": 100},
            headers={"Test2": "New"},
            cookies={"TestCookie2": "New"}
        )







class TestApiRequestHelperNegative:
    # --- Negative tests
    def test_get_request_by_unknown_name_fails(self, client_requestless):
        with pytest.raises(ValueError, match='Unknown request name.*'):
            ApiRequestHelper(client_requestless).by_name('Set')

    def test_check_for_missing_params_fails(self, client):
        api = ApiRequestHelper(client) \
            .by_name(REQUEST_NAME_2)

        with pytest.raises(KeyError, match=r'Missing path parameter.*') as err:
            api.check_for_missing_path_params()

        assert ' node' in err.exconly()
        assert ' id' in err.exconly()
