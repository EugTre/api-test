"""Tests 'SimpleApiClient' class.

pytest -s -vv ./utils/api_client/test_simple_api_client.py
"""

import pytest
from utils.conftest import LOCAL_SERVER_URL
from .simple_api_client import SimpleApiClient, DEFAULT_TIMEOUT
from .models import ApiClientIdentificator, ApiRequestLogEventType


ENDPOINT = "v1"
CLIENT_DEFAULTS = {
    "headers": {"default-header": "FooBar"},
    "cookies": {"default-cookie": "FooBarBaz"},
    "auth": ('default-auth-a', 'default-auth-b'),
    "timeout": 33
}

# --- Fixtures
@pytest.fixture(name='client_localhost', scope='session')
def get_local_api_client() -> SimpleApiClient:
    return SimpleApiClient({
        'base_url': LOCAL_SERVER_URL,
        'endpoint': ENDPOINT,
        'name': 'LocalAPI',
        'request_defaults': {
            'timeout': 5
        }
    })

@pytest.fixture(name='client_no_defaults', scope='session')
def get_api_client() -> SimpleApiClient:
    return SimpleApiClient({
        'base_url': LOCAL_SERVER_URL,
        'endpoint': ENDPOINT,
        'name': 'TestAPI'
    })

@pytest.fixture(name='client_all_defaults', scope='session')
def get_api_client_with_all_defaults() -> SimpleApiClient:
    return SimpleApiClient({
        'base_url': LOCAL_SERVER_URL, 'endpoint': ENDPOINT,
        'name': 'TestAPI',
        'request_defaults': CLIENT_DEFAULTS
    })

@pytest.fixture(name='client_default_headers', scope='session')
def get_api_client_with_default_headers() -> SimpleApiClient:
    return SimpleApiClient({
        'base_url': LOCAL_SERVER_URL, 'endpoint': ENDPOINT,
        'name': 'TestAPI',
        'request_defaults': {
            'headers': CLIENT_DEFAULTS['headers'],
            'cookies': None
        }
    })

@pytest.fixture(name='client_default_auth', scope='session')
def get_api_client_with_default_auth() -> SimpleApiClient:
    return SimpleApiClient({
        'base_url': LOCAL_SERVER_URL, 'endpoint': ENDPOINT,
        'name': 'TestAPI',
        'request_defaults': {
            'auth': CLIENT_DEFAULTS['auth'],
            'cookies': None
        }
    })


# --- Tests
class TestSimpleApiClient:
    """Tests for SimpleApiClient"""

    @pytest.mark.parametrize("input_data", [
        (LOCAL_SERVER_URL, 'v1'),
        (f'{LOCAL_SERVER_URL}/', 'v1'),
        (LOCAL_SERVER_URL, '/v1'),
        (f'{LOCAL_SERVER_URL}/', '/v1'),
        (f'{LOCAL_SERVER_URL}/', 'v1/'),
        (f'{LOCAL_SERVER_URL}/', '/v1/'),
    ])
    def test_get_api_url(self, input_data):
        """Should return base url + endpoint"""
        client = SimpleApiClient({
            'base_url': input_data[0],
            'endpoint': input_data[1]
        })
        assert client.get_api_url() == f'{LOCAL_SERVER_URL}/v1'

    @pytest.mark.parametrize("input_data, expected", [
        ('getPosts', f'{LOCAL_SERVER_URL}/{ENDPOINT}/getPosts'),
        ('/getPosts', f'{LOCAL_SERVER_URL}/{ENDPOINT}/getPosts'),
        ('/getPosts/', f'{LOCAL_SERVER_URL}/{ENDPOINT}/getPosts'),
        ('/getPosts/1/2', f'{LOCAL_SERVER_URL}/{ENDPOINT}/getPosts/1/2'),
        ('', f'{LOCAL_SERVER_URL}/{ENDPOINT}')
    ])
    def test_compose_url(self, input_data, expected,
                         client_no_defaults: SimpleApiClient):
        """Compose given URL with base url + endpoint test"""
        assert client_no_defaults.compose_url(input_data) == expected

    @pytest.mark.xdist_group("localhost_server")
    def test_request(self, client_localhost, localhost_server):
        """Basic request test"""
        response = client_localhost.request('GET', '')
        assert response.status_code == 501

    @pytest.mark.xdist_group("localhost_server")
    def test_request_with_params(self, client_localhost: SimpleApiClient,
                                 localhost_server):
        """Request with params"""
        user_agent = 'Mozilla/5.0 (Android; Mobile; rv:27.0) Gecko/27.0 Firefox/27.0'
        response = client_localhost.request(
            method='get',
            path='posts',
            params={'q': 1, 'size': 2},
            headers={'test-header': 'FooBar',
                     'User-Agent': user_agent},
            cookies={'cookie': 'FooBaz'}
        )

        assert response.request.method.lower() == 'get'
        assert 'test-header' in response.request.headers
        assert response.request.headers['test-header'] == 'FooBar'
        assert 'User-Agent' in response.request.headers
        assert response.request.headers['User-Agent'] == user_agent
        assert 'Cookie' in response.request.headers
        assert response.request.headers['Cookie'] == 'cookie=FooBaz'
        assert response.request.url == f'{LOCAL_SERVER_URL}/{ENDPOINT}/posts?q=1&size=2'

    @pytest.mark.parametrize("request_data, expected", [
        [   # No params given, no override defaults -> apply all defaults
            {
                "method": "GET",
                "path": "test",
                "override_defaults": False
            },
            {
                "method": "get",
                "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                'headers': None,
                'cookies': None,
                'auth': None,
                'timeout': DEFAULT_TIMEOUT
            }
        ],
        [   # All params given, no override defaults -> merge with defaults
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": False,
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                }
            ],
        [   # Some params given, no override defaults -> merge and use defaults
                # for not given values
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": False,
                    "headers": {"a": "1"},
                    "timeout": 10
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1"},
                    "cookies": None,
                    "auth": None,
                    "timeout": 10
                }
            ],
        [   # All params given + override defaults -> use given only
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": True,
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                }
            ],
        [   # Few params given + override defaults -> use given or defaults
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": True,
                    "headers": {"a": "1"},
                    "timeout": 10
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1"},
                    "cookies": None,
                    "auth": None,
                    "timeout": 10
                }
            ]
    ])
    def test_prepare_request_param_no_defaults(self,
            client_no_defaults: SimpleApiClient, request_data, expected):
        """Prepare on no defaults configured"""
        prepared = client_no_defaults.prepare_request_params(**request_data)

        assert prepared == expected

    @pytest.mark.parametrize("request_data, expected", [
            [   # No params given, no override defaults -> apply all defaults
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": False
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    'headers': CLIENT_DEFAULTS['headers'],
                    'cookies': CLIENT_DEFAULTS['cookies'],
                    'auth': CLIENT_DEFAULTS['auth'],
                    'timeout': CLIENT_DEFAULTS['timeout']
                }
            ],
            [   # All params given, no override defaults -> merge with defaults
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": False,
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1", **CLIENT_DEFAULTS['headers']},
                    "cookies": {"b": "2", **CLIENT_DEFAULTS['cookies']},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                }
            ],
            [   # Some params given, no override defaults -> merge and use defaults
                # for not given values
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": False,
                    "headers": {"a": "1"},
                    "auth": ('auth-a', 'auth-b'),
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1", **CLIENT_DEFAULTS['headers']},
                    "cookies": CLIENT_DEFAULTS['cookies'],
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": CLIENT_DEFAULTS['timeout']
                }
            ],
            [   # All params given + override defaults -> use given only
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": True,
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                }
            ],
            [   # Few params given + override defaults -> use given or defaults
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": True,
                    "headers": {"a": "1"},
                    "auth": ('auth-a', 'auth-b')
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1"},
                    "cookies": CLIENT_DEFAULTS['cookies'],
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": CLIENT_DEFAULTS['timeout']
                }
            ]
        ])
    def test_prepare_request_param_all_defaults(self,
            client_all_defaults: SimpleApiClient, request_data, expected):
        """Prepare on all defaults configured"""
        prepared = client_all_defaults.prepare_request_params(**request_data)

        assert prepared == expected

    @pytest.mark.parametrize("request_data, expected", [
            [   # No params given, no override defaults -> apply all defaults
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": False
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    'headers': CLIENT_DEFAULTS['headers'],
                    'cookies': None,
                    'auth': None,
                    'timeout': DEFAULT_TIMEOUT
                }
            ],
            [   # All params given, no override defaults -> merge with defaults
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": False,
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1", **CLIENT_DEFAULTS['headers']},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                }
            ],
            [   # Some params given, no override defaults -> merge and use defaults
                # for not given values
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": False,
                    "headers": {"a": "1"},
                    "auth": ('auth-a', 'auth-b'),
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1", **CLIENT_DEFAULTS['headers']},
                    "cookies": None,
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": DEFAULT_TIMEOUT
                }

            ],
            [   # All params given + override defaults -> use given only
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": True,
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                }
            ],
            [   # Few params given + override defaults -> use given or defaults
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": True,
                    "headers": {"a": "1"},
                    "auth": ('auth-a', 'auth-b'),
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1"},
                    "cookies": None,
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": DEFAULT_TIMEOUT
                }
            ]
        ])
    def test_prepare_request_param_default_headers(self,
            client_default_headers: SimpleApiClient, request_data, expected):
        """Prepare on specific defaults configured (headers)"""
        prepared = client_default_headers.prepare_request_params(**request_data)

        assert prepared == expected

    @pytest.mark.parametrize("request_data, expected", [
        [   # No params given, no override defaults -> apply all defaults
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": False
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    'headers': None,
                    'cookies': None,
                    'auth': CLIENT_DEFAULTS['auth'],
                    'timeout': DEFAULT_TIMEOUT
                }
            ],
        [   # All params given, no override defaults -> merge with defaults
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": False,
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                }
            ],
        [   # Some params given, no override defaults -> merge and use defaults
                # for not given values
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": False,
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": CLIENT_DEFAULTS['auth'],
                    "timeout": DEFAULT_TIMEOUT
                }

            ],
        [   # All params given + override defaults -> use given only
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": True,
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1"},
                    "cookies": {"b": "2"},
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": 10
                }
            ],
        [   # Few params given + override defaults -> use given or defaults
                {
                    "method": "GET",
                    "path": "test",
                    "override_defaults": True,
                    "headers": {"a": "1"},
                    "auth": ('auth-a', 'auth-b'),
                },
                {
                    "method": "get",
                    "url": fr'{LOCAL_SERVER_URL}/{ENDPOINT}/test',
                    "headers": {"a": "1"},
                    "cookies": None,
                    "auth": ('auth-a', 'auth-b'),
                    "timeout": DEFAULT_TIMEOUT
                }
            ]
    ])
    def test_prepare_request_param_default_auth(self,
            client_default_auth: SimpleApiClient, request_data, expected):
        """Prepare on specific defaults configured (auth)"""
        prepared = client_default_auth.prepare_request_params(**request_data)

        assert prepared == expected


import logging

@pytest.fixture(name='client_with_logger')
def get_api_client_with_logger(monkeypatch) -> SimpleApiClient:
    """Returns configured logger object"""
    log_storage = []

    handler = logging.Handler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(fmt='%(message)s'))

    def monkey_emit(*args, **kwargs):
        log_storage.append(args)
        return True
    monkeypatch.setattr(handler, 'emit', monkey_emit)

    logger = logging.getLogger('CustomLogger')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    client = SimpleApiClient({
        'base_url': LOCAL_SERVER_URL, 'endpoint': ENDPOINT,
        'name': 'TestAPI',
        'request_defaults': CLIENT_DEFAULTS,
        'logger_name': logger.name
    })
    client.log_storage = log_storage

    return client

class TestSimpleApiClientLogging:
    """Tests logging of SimpleApiClient"""
    @pytest.mark.xdist_group("localhost_server")
    def test_log_request(self, client_with_logger: SimpleApiClient, localhost_server):
        """Logging called for request with params"""
        req_params = {
            'override_defaults': True,
            'method': 'get',
            'path': 'posts',
            'params': {'q': 1, 'size': 2},
            'headers': {'test-header': 'FooBar'},
            'cookies': {'cookie': 'FooBaz'}
        }
        prepared_params = client_with_logger.prepare_request_params(**req_params)

        response = client_with_logger.request(**req_params)
        request_id = client_with_logger.request_count - 1

        # Read catched logs and assert values
        prepared_request_log_record = client_with_logger.log_storage[0][0]
        succes_request_log_recored = client_with_logger.log_storage[1][0]

        assert prepared_request_log_record.event_type == ApiRequestLogEventType.PREPARED
        assert prepared_request_log_record.request_id == request_id
        assert prepared_request_log_record.client_id == client_with_logger.client_id
        assert prepared_request_log_record.request_params == prepared_params

        assert succes_request_log_recored.event_type == ApiRequestLogEventType.SUCCESS
        assert succes_request_log_recored.request_id == request_id
        assert succes_request_log_recored.client_id == client_with_logger.client_id
        assert succes_request_log_recored.request == \
            client_with_logger.request_object_to_str(response.request)
        assert succes_request_log_recored.response == \
            client_with_logger.response_object_to_str(response)
