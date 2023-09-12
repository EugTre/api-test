"""Tests for Api Request Helper class

pytest -s -vv ./utils/api_helpers/test_api_request_helper.py
"""
import pytest
from utils.api_client.basic_api_client import BasicApiClient
from utils.api_client.models import RequestCatalogEntity, RequestEntity, \
    ResponseEntity, HTTPMethod
from utils.matchers import Anything
from utils.conftest import LOCAL_SERVER_URL
from .api_request_helper import ApiRequestHelper, ApiResponseHelper


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
    'base_url': LOCAL_SERVER_URL,
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
    '''Returns api client instance'''
    return BasicApiClient(API_CLIENT_CONFIG)

@pytest.fixture(name='client_requestless', scope='session')
def get_api_client_no_requests() -> BasicApiClient:
    '''Returns api client instnace without request catalog'''
    return BasicApiClient({
        'base_url': "http://example.com",
        'endpoint': "v1",
        'name': 'TestAPI',
        'request_catalog': None
    })

@pytest.fixture(name='api')
def get_api_helper(client) -> ApiRequestHelper:
    """Returns configured ApiRequestHelper"""
    return ApiRequestHelper(client)

class TestApiRequestHelper:
    """Positive tests for ApiRequestHelper"""
    def test_prepare_request_by_name(self, api: ApiRequestHelper):
        """Request may be selected and pre-configured by name"""
        api.by_name(REQUEST_NAME_1)
        assert api.request == REQUEST_CONFIGURED_1
        assert api.expected == RESPONSE_CONFIGURED_1

    def test_prepare_custom_request(self, api: ApiRequestHelper):
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

        api.by_path(
            path=expected_request.path,
            method=expected_request.method
        ).with_query_params(id=query_param['id']) \
            .with_headers(header)

        assert api.request == expected_request
        assert api.expected == ResponseEntity(
            status_code=expected_response_code
        )

    def test_prepare_customized_request(self, api: ApiRequestHelper):
        """Request may be overwritten with various methods"""
        path_params = {'amount': 44}
        query_params = {'page': 55}
        headers = {'Foo': 'Bar'}
        cookies = {'foo': 'bar'}
        json_data = {'a': 100}

        api.by_name(REQUEST_NAME_1) \
                .with_path_params(**path_params) \
                .with_query_params(**query_params) \
                .with_headers(headers) \
                .with_cookies(cookies) \
                .with_json_payload(json_data)

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

    def test_by_path_defaults(self, api: ApiRequestHelper):
        """.by_path with no args should prepare valid request"""
        api.by_path()
        assert api.request == RequestEntity(
            method=HTTPMethod.GET,
            path=""
        )
        assert api.expected == ResponseEntity(status_code=200)

    def test_append_params(self, api: ApiRequestHelper):
        """Params append already defined params"""
        api.by_path(method="GET", path="") \
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

    def test_overwrite_params(self, api: ApiRequestHelper):
        """Params may be overwritten"""
        api.by_path(method="GET", path="") \
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

    def test_unset_extra_path_param(self, api: ApiRequestHelper):
        """Extra path params may be removed by setting to null"""
        params_extra = {
            'id':100500, 'node':'FooBarr', 'amount':45
        }

        api.by_name(REQUEST_NAME_2) \
            .with_path_params(**params_extra)

        assert api.request.path_params == params_extra

        api.with_path_params(amount=None)
        assert api.request.path_params == {
            'id': params_extra['id'],
            'node': params_extra['node']
        }

    def test_unset_extra_query_param(self, api: ApiRequestHelper):
        """Extra query params may be removed by setting to null"""
        params_extra = {
            'id':100500, 'node':'FooBarr', 'amount':45
        }

        api.by_name(REQUEST_NAME_2) \
            .with_query_params(**params_extra)

        assert api.request.query_params == params_extra

        api.with_query_params(amount=None)
        assert api.request.query_params == {
            'id': params_extra['id'],
            'node': params_extra['node']
        }

    def test_with_expected(self, api: ApiRequestHelper):
        """with_expected() sets expected params"""
        status_code = 501
        schema = {'json_schema': 'foo'}
        headers = {'headers': 'bar'}
        json = {'content': 'baz'}

        api.by_path('/items').with_expected(
            status_code=status_code,
            schema=schema,
            headers=headers,
            json=json
        )

        assert api.expected == ResponseEntity(
            status_code=status_code, schema=schema, json=json, headers=headers
        )

    def test_with_expected_partial(self, api: ApiRequestHelper):
        """with_expected() sets some expected params"""
        status_code = 501
        headers = {'headers': 'bar'}

        api.by_path('/items').with_expected(
            status_code=status_code,
            headers=headers
        )

        assert api.expected == ResponseEntity(
            status_code=status_code, headers=headers
        )

    def test_with_expected_overwrites(self, api: ApiRequestHelper):
        """with_expected() overwrites already set expected params"""
        status_code = 501
        json = {'content': 'bar'}

        api.by_name(REQUEST_NAME_2).with_expected(
            status_code=status_code,
            json=json
        )

        assert api.expected == ResponseEntity(
            status_code=status_code,
            json=json,
            schema=RESPONSE_CONFIGURED_2.schema
        )

    def test_prepare_request_params_for_configured_request(self, api: ApiRequestHelper):
        """Prepare request method test for concifugrd request"""
        api.by_path(path='{node}/{id}') \
            .with_path_params(node='foobar', id=100500) \
            .with_query_params(page=2) \
            .with_headers({'Test': 'test'}) \
            .with_cookies({'Test': 'test'}) \
            .with_json_payload({"stuff": "foobar"})

        req_params = api.prepare_request_params({
            'headers': {'Test2': 'test'},
            'cookies': {'Test2': 'test'},
            'auth': ('foo', 'bar')
        })

        assert req_params == {
            'method': HTTPMethod.GET,
            'path': 'foobar/100500',
            'params': {'page': 2},
            'headers': {
                'Test': 'test',
                'Test2': 'test'
            },
            'cookies': {
                'Test': 'test',
                'Test2': 'test'
            },
            'auth': ('foo', 'bar'),
            'json': {"stuff": "foobar"}
        }

    def test_prepare_request_params_for_unconfigured_request(self, api: ApiRequestHelper):
        """Prepare request method test for unconcifugrd request"""
        params = {
            'headers': {'Foo': 'Bar'},
            'cookies': {'Foo': 'Baz'},
            'auth': ('user', 'pass')
        }
        api.by_path('')
        req_params = api.prepare_request_params(params)

        assert req_params == {
            'method': HTTPMethod.GET,
            'path': '',
            'params': None,
            'json': None,
            **params
        }


@pytest.mark.xdist_group("localhost_server")
class TestApiRequestHelperPerform:
    """Test .perform() method"""
    def test_perform_request_no_params(self, api: ApiRequestHelper, localhost_server):
        """Request may be performed without additional args"""
        response = api.by_path("/items").with_expected(status_code=501).perform()

        assert response
        assert isinstance(response, ApiResponseHelper)

    def test_perform_request_with_params(self, api: ApiRequestHelper, localhost_server):
        """Request may be performed with additional args"""
        response = api.by_path("/items").with_expected(status_code=501)\
            .perform(headers={'foo': 'bar'})

        assert response
        assert 'foo' in (response.get_response().request.headers)

    def test_perform_request_with_params_mixin(self, api: ApiRequestHelper, localhost_server):
        """Request may be performed with mixin preset params and .perform() args params"""
        response = api.by_name(REQUEST_NAME_2)\
            .with_path_params(node='node', id=2) \
            .with_expected(status_code=501) \
            .perform(
                override_defaults=True,
                headers={"Omaha": "Kilo"}
            )

        assert response
        assert 'Omaha' in response.get_response().request.headers

    def test_perform_request_with_params_override(self, api: ApiRequestHelper, localhost_server):
        """Request may be performed with overwriting preset params by .perform() args params"""
        new_header_value = "NotBar"
        response = api.by_name(REQUEST_NAME_2)\
            .with_path_params(node='node', id=100) \
            .with_expected(status_code=501) \
            .perform(
                headers={"Foo": new_header_value}
            )

        assert response
        request_headers = response.get_response().request.headers
        assert 'Foo' in request_headers
        assert request_headers['Foo'] == new_header_value

class TestApiRequestHelperNegative:
    """Negative tests for ApiRequestHelper"""
    def test_get_request_by_unknown_name_fails(self, client_requestless):
        """Error on selecting request by unknown name"""
        with pytest.raises(ValueError, match='Unknown request name.*'):
            ApiRequestHelper(client_requestless).by_name('Set')

    def test_check_for_missing_path_params_fails(self, api: ApiRequestHelper):
        """Missing path params raises error"""
        api.by_name(REQUEST_NAME_2)

        # Missing all 2 params
        with pytest.raises(KeyError, match=r'Missing path parameter.*') as err:
            api.check_for_missing_path_params()

        assert ' node' in err.exconly()
        assert ' id' in err.exconly()

        # Missing only 1 param
        api.with_path_params(id=100500)
        with pytest.raises(KeyError, match=r'Missing path parameter.*') as err:
            api.check_for_missing_path_params()

        assert ' node' in err.exconly()
        assert ' id' not in err.exconly()

        # All params present - no error
        api.with_path_params(node="FooBar")
        assert api.check_for_missing_path_params()

    def test_check_for_extra_path_params_fails(self, api: ApiRequestHelper):
        """Extra path params raises error"""
        api.by_name(REQUEST_NAME_2) \
            .with_path_params(id=100500, node='FooBar')

        # Extra params - raise error
        api.with_path_params(foo='bar')
        with pytest.raises(
            ValueError,
            match=r'Extra path parameter\(s\) provided, but never used.*'
        ) as err:
            api.check_for_missing_path_params()

        assert 'foo' in err.exconly()

        # Delete extra param and re-check
        api.with_path_params(foo=None)
        assert api.check_for_missing_path_params()

    def test_perform_on_unset_request_fails(self, api: ApiRequestHelper):
        """Error occurs if request is not set before performing request"""
        with pytest.raises(RuntimeError, match='Request is not initialized.*'):
            api.perform()
