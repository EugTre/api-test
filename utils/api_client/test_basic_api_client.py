"""Tests 'BasicApiClient' class.

pytest -s -vv ./utils/api_client/test_basic_api_client.py
"""

import pytest
from utils.conftest import LOCAL_SERVER_URL
from .basic_api_client import BasicApiClient, DEFAULT_TIMEOUT


ENDPOINT = "v1"
CLIENT_DEFAULTS = {
    "headers": {"default-header": "FooBar"},
    "cookies": {"default-cookie": "FooBarBaz"},
    "auth": ('default-auth-a', 'default-auth-b'),
    "timeout": 33
}

# --- Fixtures
@pytest.fixture(name='client_localhost', scope='session')
def get_local_api_client() -> BasicApiClient:
    return BasicApiClient({
        'base_url': LOCAL_SERVER_URL,
        'endpoint': ENDPOINT,
        'name': 'LocalAPI',
        'request_defaults': {
            'timeout': 5
        }
    })

@pytest.fixture(name='client_no_defaults', scope='session')
def get_api_client() -> BasicApiClient:
    return BasicApiClient({
        'base_url': LOCAL_SERVER_URL, 'endpoint': ENDPOINT,
        'name': 'TestAPI'
    })

@pytest.fixture(name='client_all_defaults', scope='session')
def get_api_client_with_all_defaults() -> BasicApiClient:
    return BasicApiClient({
        'base_url': LOCAL_SERVER_URL, 'endpoint': ENDPOINT,
        'name': 'TestAPI',
        'request_defaults': CLIENT_DEFAULTS
    })

@pytest.fixture(name='client_default_headers', scope='session')
def get_api_client_with_default_headers() -> BasicApiClient:
    return BasicApiClient({
        'base_url': LOCAL_SERVER_URL, 'endpoint': ENDPOINT,
        'name': 'TestAPI',
        'request_defaults': {
            'headers': CLIENT_DEFAULTS['headers'],
            'cookies': None
        }
    })

@pytest.fixture(name='client_default_auth', scope='session')
def get_api_client_with_default_auth() -> BasicApiClient:
    return BasicApiClient({
        'base_url': LOCAL_SERVER_URL, 'endpoint': ENDPOINT,
        'name': 'TestAPI',
        'request_defaults': {
            'auth': CLIENT_DEFAULTS['auth'],
            'cookies': None
        }
    })


# --- Tests
class TestBasicApiClient:
    """Tests for BasicApiClient"""

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
        client = BasicApiClient({
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
                         client_no_defaults: BasicApiClient):
        """Compose given URL with base url + endpoint test"""
        assert client_no_defaults.compose_url(input_data) == expected

    @pytest.mark.xdist_group("localhost_server")
    def test_request(self, client_localhost, localhost_server):
        """Basic request test"""
        response = client_localhost.request('GET', '')
        assert response.status_code == 501

    @pytest.mark.xdist_group("localhost_server")
    def test_request_with_params(self, client_localhost: BasicApiClient,
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
            client_no_defaults: BasicApiClient, request_data, expected):
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
            client_all_defaults: BasicApiClient, request_data, expected):
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
            client_default_headers: BasicApiClient, request_data, expected):
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
            client_default_auth: BasicApiClient, request_data, expected):
        """Prepare on specific defaults configured (auth)"""
        prepared = client_default_auth.prepare_request_params(**request_data)

        assert prepared == expected
