"""Unit tests for Api Response Helper

pytest -s -vv ./utils/api_helpers/test_api_response_helper.py
"""
import datetime
import json

import pytest
import jsonschema.exceptions
from requests.models import Response

import utils.matchers.matcher as match
from utils.json_content.json_content import JsonContent, JsonContentBuilder
from .api_response_helper import ApiResponseHelper


# --- Constants
PAYLOAD_SIMPLE = {
    "status": "success",
    "message": "Successfully executed"
}

PAYLOAD_DETAILED = {
    "status": "success",
    "message": "Successfully executed",
    "info": {
        "id": 344,
        "timestamp": "2023-08-11T20:43:55.534Z",
        "items": [44, 492, 2410]
    }
}

PAYLOAD_WITH_EMPTY = {
    "index": 0,
    "extraInfo": "",
    "hasFlag": False,
    "comments": [],
    "child": {},
    "parentId": None
}

JSONSCHEMA_SIMPLE = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "message": {
            "type": "string",
        },
        "status": {
            "type": "string",
            "enum": ["success","error"]
        }
    },
    "required": [
        "message",
        "status"
    ]
}

JSONSCHEMA_DETAILED = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success","error"]
        },
        "message": {
            "type": "string",
        },
        "info": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "number"
                },
                "timestamp": {
                    "type": "string"
                },
                "items": {
                    "type": "array"
                }
            }
        }
    },
    "required": [
        "message",
        "status",
        "info"
    ]
}

HEADERS_SIMPLE = {
    "Accept": "text/plain, text/html, text/x-dvi",
    "Accept-Charset": "iso-8859-5, Unicode-1-1"
}

HEADERS_DETAILED = {
    "Accept": "text/plain, text/html, text/x-dvi",
    "Accept-Charset": "iso-8859-5, Unicode-1-1",
    "Accept-Encoding": "gzip",
    "Cookie": "name1=value1; name2=value2; name3=value3",
    "From": "webmaster@example.com",
    "Referer": "http://www.example.com",
}

# --- Fixtures and functions
def get_api_with_mocked_response(status_code: int,
                content: str = None,  json_content: dict|list = None,
                headers: dict = None, cookies: dict = None,
                latency: int = None) -> ApiResponseHelper:
    """Creates ApiResponseHelper with mocked `requests.models.Response` object

        Args:
            status_code (int): status code as int (200, 404).
            content (str, optional): plain text content. Defaults to None.
            json_content (dict | list, optional): JSON like content. Defaults to None.
            headers (dict, optional): dict of headers. Defaults to None.
            cookies (dict, optional): dict of cookies. Defaults to None.
            latency (int, optional): In miliseconds. Defaults to None.
        """
    resp = Response()
    resp.status_code = status_code
    resp.encoding = 'utf-8'

    if headers is not None:
        resp.headers.update(headers)

    if cookies is not None:
        resp.cookies.update(cookies)

    if content is not None:
        resp._content = bytes(content)

    if json_content is not None:
        resp._content = bytes(
            json.dumps(json_content),
            encoding='utf-8'
        )

    if latency is not None:
        resp.elapsed = datetime.timedelta(seconds=latency/1000)

    return ApiResponseHelper(resp)

@pytest.fixture(name='api_response_simple', scope='session')
def get_api_respnse_simple() -> ApiResponseHelper:
    '''Return ApiResponseHelper with mocked response
    with simple payload and headers'''
    return get_api_with_mocked_response(
        200,
        json_content=PAYLOAD_SIMPLE,
        headers=HEADERS_SIMPLE
    )

@pytest.fixture(name='api_response_detailed', scope='session')
def get_api_respnse_detailed() -> ApiResponseHelper:
    '''Return ApiResponseHelper with mocked response
    with detailed payload and headers'''
    return get_api_with_mocked_response(
        200,
        json_content=PAYLOAD_DETAILED,
        headers=HEADERS_DETAILED
    )

@pytest.fixture(name='api_response_with_empty', scope='session')
def get_api_response_with_empty() -> ApiResponseHelper:
    """Returns ApiResponseHelper with mocked response
    with empty JSON params"""
    return get_api_with_mocked_response(
        200,
        json_content=PAYLOAD_WITH_EMPTY
    )


# Tests
# --- Positive tests
class TestApiResponseHelperBasic:
    """Basic tests of ApiResponseHelper"""

    def test_get_json(self):
        """.get_json() retuns Json Content object"""
        api_resp = get_api_with_mocked_response(200, json_content=PAYLOAD_SIMPLE)

        resp_json_content = api_resp.get_json()
        assert isinstance(resp_json_content, JsonContent)
        assert resp_json_content == PAYLOAD_SIMPLE

    def test_get_json_as_dict(self):
        """.get_json() with as_dict=True option retuns dict object"""
        api_resp = get_api_with_mocked_response(200, json_content=PAYLOAD_SIMPLE)

        resp_json_content = api_resp.get_json(as_dict=True)
        assert isinstance(resp_json_content, dict) and \
            not isinstance(resp_json_content, JsonContent)
        assert resp_json_content == PAYLOAD_SIMPLE

    @pytest.mark.parametrize("pointer, expected", [
        ("/status", PAYLOAD_DETAILED["status"]),
        ("/info/id", PAYLOAD_DETAILED["info"]["id"]),
        ("/info/items/1", PAYLOAD_DETAILED["info"]["items"][1])
    ])
    def test_get_value(self, pointer, expected):
        """.get_value() method able to retrieve data"""
        api_resp = get_api_with_mocked_response(200, json_content=PAYLOAD_DETAILED)
        assert api_resp.get_json_value(pointer) == expected


class TestApiResponseHelperGeneral:
    """Response general validation methods tests"""

    # status_code_equals(code)
    def test_status_code_equals(self):
        get_api_with_mocked_response(200).status_code_equals(200)

    def test_set_expected_and_status_code_equals(self, api_response_simple: ApiResponseHelper):
        api_response_simple.set_expected(status_code=200).status_code_equals()

    def test_status_code_equals_asserts(self):
        with pytest.raises(AssertionError, match='Response status code.*doesn\'t match.*'):
            get_api_with_mocked_response(404).status_code_equals(200)

    # validate_against_schema(schema)
    def test_valudate_against_schema(self, api_response_simple: ApiResponseHelper):
        api_response_simple.validates_against_schema(JSONSCHEMA_SIMPLE)

    def test_set_expected_and_valudate_against_schema(self, api_response_simple: ApiResponseHelper):
        api_response_simple.set_expected(schema=JSONSCHEMA_SIMPLE).validates_against_schema()

    def test_valudate_against_schema_asserts(self, api_response_simple: ApiResponseHelper):
        with pytest.raises(jsonschema.exceptions.ValidationError):
            api_response_simple.validates_against_schema(JSONSCHEMA_DETAILED)

    # latency_is_lower_than
    def test_latency_is_lower_than(self):
        get_api_with_mocked_response(200, latency=250).latency_is_lower_than(500)

    def test_latency_is_lower_than_asserts(self):
        with pytest.raises(AssertionError,
                           match='Response latency of .* is higher than.*'):
            get_api_with_mocked_response(200, latency=500).latency_is_lower_than(250)

    # is_empty
    def test_is_empty(self):
        get_api_with_mocked_response(200).is_empty()

    def test_is_empty_asserts(self, api_response_simple: ApiResponseHelper):
        with pytest.raises(AssertionError,
                           match='Response has JSON content, but expected to be empty.'):
            api_response_simple.is_empty()

    # is_not_empty
    def test_is_not_empty(self, api_response_simple: ApiResponseHelper):
        api_response_simple.is_not_empty()

    def test_is_not_empty_asserts(self):
        with pytest.raises(AssertionError,
                           match='Response has no JSON content, but expected to be not empty.'):
            get_api_with_mocked_response(200).is_not_empty()


class TestApiResponseHelperHeaders:
    """Response Headers validation methods tests"""
    # headers_present
    @pytest.mark.parametrize("headers", [
        ('Accept', 'Accept-Charset'),
        ('accept', 'accept-charset'),
        ('accepT', 'accept-Charset')
    ])
    def test_headers_present(self, api_response_simple: ApiResponseHelper, headers):
        """.headers.present() method test, including case insensitive checks"""
        api_response_simple.headers.present(*headers)

    def test_set_expected_and_headers_present(self, api_response_simple: ApiResponseHelper):
        api_response_simple.set_expected(headers=HEADERS_SIMPLE).headers.present()

    def test_headers_present_asserts(self, api_response_simple: ApiResponseHelper):
        headers = ["From", "Cookie", "Accept-encoding"]
        with pytest.raises(AssertionError,
                           match='Some headers are not present, but expected to be. '\
                                f'Missing headers: {", ".join(headers)}'):
            api_response_simple.headers.present(*headers)

    # headers_not_present
    def test_headers_not_present(self, api_response_simple: ApiResponseHelper):
        api_response_simple.headers.not_present("From", "Cookie", "Accept-Encoding")

    def test_headers_not_present_asserts(self, api_response_simple: ApiResponseHelper):
        with pytest.raises(AssertionError,
                           match='Some headers are present, but expected not to be.*'):
            api_response_simple.headers.not_present("Accept")

    # header_contains
    @pytest.mark.parametrize("header, expected, case_sensitive", [
        ("Accept", "text/html", True),
        ("ACCEPT", "Text/HTML", False),
        ("From", "example.com", True),
        ("accept-charset", "UNICODE", False)
    ])
    def test_header_contains(self, api_response_detailed: ApiResponseHelper,
                             header, expected, case_sensitive):
        api_response_detailed.headers.header_contains(header, expected, case_sensitive)

    @pytest.mark.parametrize("header, expected, case_sensitive, exc_msg", [
        ("Foo", "Bar", True, 'Header ".*" is missing in response headers.'),
        ("From", "something.net", False, 'Value of header .* doesn\'t contain substring.*'),
        ("Accept-Charset", "UNICODE", True, 'Value of header .* doesn\'t contain substring.*')
    ])
    def test_header_contains_asserts(self, api_response_detailed: ApiResponseHelper,
                             header, expected, case_sensitive, exc_msg):
        with pytest.raises(AssertionError, match=exc_msg):
            api_response_detailed.headers.header_contains(header, expected, case_sensitive)

    # specific header_equals
    @pytest.mark.parametrize("header, expected, case_sensitive", [
        ("Accept", "text/plain, text/html, text/x-dvi", True),
        ("ACCEPT", "TEXT/plain, TEXT/html, TEXT/x-dvi", False),
        ("From", "webmaster@example.com", True),
        ("accept-encoding", "GZIP", False)
    ])
    def test_header_equals(self, api_response_detailed: ApiResponseHelper,
                             header, expected, case_sensitive):
        api_response_detailed.headers.header_equals(header, expected, case_sensitive)

    # headers like
    @pytest.mark.parametrize("headers_like", [
        {
            "accept": match.AnyTextLike(".*TEXT/HTML.*"),
            "accept-charset": match.AnyTextLike(".*unicode.*")
        },
        {
            "accept": match.AnyTextLike(r"(Text/[a-z-]*),*\s*"),
            "accept-charset": match.AnyTextLike(".*unicode.*")
        },
        {
            "Accept": match.AnyTextLike(".*text/html.*", True),
            "Accept-Charset": match.AnyTextLike(".*Unicode.*", True)
        }
    ])
    def test_headers_to_be_like(self, api_response_simple: ApiResponseHelper, headers_like):
        api_response_simple.headers.are_like(headers_like)

    def test_set_expected_and_headers_to_be_like(self, api_response_detailed: ApiResponseHelper):
        api_response_detailed.set_expected(headers=HEADERS_SIMPLE).headers.are_like()

    @pytest.mark.parametrize("headers_like, exc_msg", [
        (
            {
                "origin": match.AnyTextLike(".*something.*"),
                "redirects":  match.AnyTextLike(".*allowedd.*")
            },
            r'Response headers are not like given:.*header ".*" not found.*'
        ),
        (
            {
                "accept": match.AnyTextLike(".*image/png.*"),
                "accept-charset":  match.AnyTextLike(".*xcode.*")
            },
            r'Response headers are not like given:.*header\'s value .*'
            r'doesn\'t match to expected .*'
        ),
        (
            {
                "accept": match.AnyTextLike(".*image/png.*"),
                "origin": match.AnyTextLike(".*somewhere.*")
            },
            r'Response headers are not like given:.*header\'s value .*'
            r'doesn\'t match to expected .*header ".*" not found.*'
        ),
        (
            {
                "Accept": match.AnyTextLike(".*Text/HTML.*", case_sensitive=True),
                "Accept-Charset": match.AnyTextLike(".*UNICODE.*", case_sensitive=True)
            },
            r'Response headers are not like given:.*header\'s value .*'
            r'doesn\'t match to expected .*'
        )
    ])
    def test_headers_to_be_like_asserts(self, api_response_simple: ApiResponseHelper,
                                        headers_like, exc_msg):
        with pytest.raises(AssertionError, match=exc_msg):
            api_response_simple.headers.are_like(headers_like)

    # headers equals
    def test_headers_equals(self, api_response_detailed: ApiResponseHelper):
        api_response_detailed.headers.equals(HEADERS_DETAILED)

    def test_headers_equals_ignore(self, api_response_simple: ApiResponseHelper):
        api_response_simple.headers.equals(HEADERS_DETAILED,
                                           ignore=("Accept-Encoding", "Cookie", "From", "Referer"))

    def test_headers_equals_ignore_case_insensitive(self, api_response_simple: ApiResponseHelper):
        api_response_simple.headers.equals(HEADERS_DETAILED,
                                           ignore=("accept-Encoding", "cookie", "From", "referer"))

    def test_headers_equals_using_matchers(self, api_response_simple: ApiResponseHelper):
        api_response_simple.headers.equals(
            headers={
                "accept": match.AnyTextLike("Text/plain, Text/html, Text/x-dvi"),
                "accept-charset": match.AnyTextLike("iso-8859-5, Unicode-1-1", case_sensitive=True)
            }
        )

    def test_set_expected_and_headers_equals(self, api_response_detailed: ApiResponseHelper):
        api_response_detailed.set_expected(headers=HEADERS_DETAILED).headers.equals()

    def test_headers_equals_values_differ_asserts(self, api_response_simple: ApiResponseHelper):
        with pytest.raises(AssertionError,
                           match='Headers are not equal to expected.'):
            api_response_simple.headers.equals({
                "accept": "text/plain, text/html",
                "Accept-Charset": "iso-8859-5, Unicode-1-1, windows-1253"
            })

    def test_headers_equals_missing_headers_asserts(self, api_response_simple: ApiResponseHelper):
        expected = JsonContentBuilder().from_data(HEADERS_SIMPLE, True).build() \
                .update('/Extra-Header', "some value").get()
        with pytest.raises(AssertionError,
                           match='Headers are not equal to expected.'):
            api_response_simple.headers.equals(headers=expected)

    def test_headers_equals_extra_headers_asserts(self, api_response_simple: ApiResponseHelper):
        expected = JsonContentBuilder().from_data(HEADERS_SIMPLE, True).build() \
                .delete('/Accept').get()
        with pytest.raises(AssertionError,
                           match='Headers are not equal to expected.'):
            api_response_simple.headers.equals(headers=expected)


class TestApiResponseHelperJson:
    """Response body validation methods tests"""
    # equals
    def test_equals(self, api_response_simple: ApiResponseHelper):
        api_response_simple.json.equals(PAYLOAD_SIMPLE)

    def test_set_expected_and_equals(self, api_response_simple: ApiResponseHelper):
        api_response_simple.set_expected(json=PAYLOAD_SIMPLE).json.equals()

    def test_equals_asserts(self, api_response_simple: ApiResponseHelper):
        with pytest.raises(AssertionError,
                           match='Response\'s JSON is not equal to given one.*'):
            api_response_simple.json.equals({"status": "success"})

    def test_equals_ignoring(self, api_response_detailed: ApiResponseHelper):
        api_response_detailed.json.equals(PAYLOAD_SIMPLE, ignore=("/info/id", "/info"))

    def test_set_expected_and_equals_ignoring(self, api_response_detailed: ApiResponseHelper):
        api_response_detailed \
            .set_expected(json=PAYLOAD_SIMPLE) \
            .json.equals(ignore=("/info",))

    def test_equals_with_matchers(self, api_response_simple: ApiResponseHelper):
        api_response_simple.set_expected(json={
            "status": match.AnyText(),
            "message": match.AnyTextLike(r'success.*exec.*')
        }).json.equals()

    # is_like
    def test_is_like(self, api_response_detailed: ApiResponseHelper):
        api_response_detailed.json.is_like({
            'status': PAYLOAD_DETAILED['status'],
            'message': PAYLOAD_DETAILED['message']
        })

    def test_is_like_for_nested(self, api_response_detailed: ApiResponseHelper):
        api_response_detailed.json.is_like({
            'info': {
                'id': 344,
                'items': match.AnyListOf(item_type=1)
            }
        })

    def test_is_like_for_missing_keys_fail(self, api_response_detailed: ApiResponseHelper):
        with pytest.raises(AssertionError,
                match='JSON content is not like given:.*'):
            api_response_detailed.json.is_like({
                'info': {
                    'status': 344,
                    'message': 'Successfully executed'
                }
            })

    def test_is_like_comparison_fail(self, api_response_detailed: ApiResponseHelper):
        with pytest.raises(AssertionError,
                match='JSON content is not like given:.*'):
            api_response_detailed.json.is_like({
                'status': 34125,
                'message': "Message"
            })

    # params_present / params_not_present
    @pytest.mark.parametrize("params", (
        ['/status'],
        ['/info/items/0'],
        ('/message', '/info', '/info/timestamp', '/info/items'),
    ), ids=('single', 'single_nested', 'multiple'))
    def test_params_present(self, api_response_detailed: ApiResponseHelper, params):
        api_response_detailed.json.params_present(*params)

    @pytest.mark.parametrize("params", (
        ['/missing'],
        ('/missing1', '/missing2'),
        ('/status', '/missing'),
        ('/missing', '/status')
    ), ids=('missing', 'multiple_missing', 'existsing_and_missing', 'missing_and_existing'))
    def test_params_present_for_missing_param_fails(self,
            api_response_detailed: ApiResponseHelper, params):
        with pytest.raises(AssertionError,
                match='Params are not present, but expected to be.*'):
            api_response_detailed.json.params_present(*params)

    @pytest.mark.parametrize("params", (
        ['/info'],
        ('/info', '/info/timestamp', '/info/items', '/info/items/0'),
    ), ids=('single', 'multiple'))
    def test_params_not_present(self, api_response_simple: ApiResponseHelper, params):
        api_response_simple.json.params_not_present(*params)

    @pytest.mark.parametrize("params", (
        ('/status',),
        ('/status', '/message'),
        ('/status', '/missing'),
        ('/missing', '/status'),
    ), ids=('existing', 'multiple_existing', 'existsing_and_missing', 'missing_and_existing'))
    def test_params_not_present_for_existing_params_fails(self,
            api_response_detailed: ApiResponseHelper, params):
        with pytest.raises(AssertionError,
                match='Params are present, but not expected to be.*'):
            api_response_detailed.json.params_not_present(*params)

    # params_are_not_empty
    @pytest.mark.parametrize('params', (
        ['/index'],
        ('/hasFlag',),
        ('/index', '/hasFlag')
    ), ids=('zero', 'False', 'multiple'))
    def test_params_are_not_empty(self, api_response_with_empty: ApiResponseHelper, params):
        api_response_with_empty.json.params_are_not_empty(*params)

    @pytest.mark.parametrize('params', (
        ['/extraInfo'],
        ['/comments'],
        ['/child'],
        ['/parentId'],
        ('/comments', '/parentId'),
        ('/hasFlag', '/parentId'),
        ('/parentId', '/hasFlag'),
    ), ids=(
        'empty_string', 'empty_list', 'empty_dict', 'None', 'multiple_empty',
        'non_empty_and_empty', 'empty_and_non_empty'
    ))
    def test_params_are_not_empty_for_empty_fails(self,
            api_response_with_empty: ApiResponseHelper, params):
        with pytest.raises(AssertionError,
                match='Params are empty or missing, but expected to present and be not empty:.*'):
            api_response_with_empty.json.params_are_not_empty(*params)

    def test_params_are_not_empty_for_missing_params_fails(self,
            api_response_with_empty: ApiResponseHelper):
        with pytest.raises(AssertionError,
                match='Params are empty or missing, but expected to present and be not empty:.*'):
            api_response_with_empty.json.params_are_not_empty('/missing')

    # params_are_empty
    @pytest.mark.parametrize('params', (
        ['/extraInfo'],
        ['/comments'],
        ['/parentId'],
        ['/child'],
        ('/extraInfo', '/comments', '/parentId')
    ), ids=('empty_string', 'empty_list', 'empty_dict', 'None', 'multiple'))
    def test_params_are_empty(self, api_response_with_empty: ApiResponseHelper, params):
        api_response_with_empty.json.params_are_empty(*params)

    @pytest.mark.parametrize('params', (
        ['/index'],
        ['/hasFlag'],
        ('/index', '/hasFlag'),
        ('/extraInfo', '/hasFlag'),
        ('/hasFlag', '/extraInfo')
    ), ids=(
        'zero', 'False', 'multiple_non_empty',
        'empty_and_nonempty', 'nonempty_and_empty'
    ))
    def test_params_are_empty_for_non_empty_fails(self,
            api_response_with_empty: ApiResponseHelper, params):
        with pytest.raises(AssertionError,
                match='Params are not empty or missing, but expected to present and be empty.*'):
            api_response_with_empty.json.params_are_empty(*params)

    def test_params_are_empty_for_missing_params_fails(self,
            api_response_with_empty: ApiResponseHelper):
        with pytest.raises(AssertionError,
                match='Params are not empty or missing, but expected to present and be empty.*'):
            api_response_with_empty.json.params_are_empty('/missing')

    # param_equals
    @pytest.mark.parametrize("param, expected", (
        ('/status', PAYLOAD_DETAILED['status']),
        ('/message', PAYLOAD_DETAILED['message']),
        ('/info', PAYLOAD_DETAILED['info']),
        ('/info/id', PAYLOAD_DETAILED['info']['id']),
        ('/info/timestamp', PAYLOAD_DETAILED['info']['timestamp']),
        ('/info/items', PAYLOAD_DETAILED['info']['items']),
        ('/info/items/0', PAYLOAD_DETAILED['info']['items'][0]),
        ('/info/items/1', PAYLOAD_DETAILED['info']['items'][1]),
        ('/info/items/2', PAYLOAD_DETAILED['info']['items'][2]),
    ))
    def test_param_equals(self, api_response_detailed: ApiResponseHelper, param, expected):
        api_response_detailed.json.param_equals(param, expected)

    @pytest.mark.parametrize("param, expected", (
        ('/status', match.AnyText()),
        ('/message', match.AnyTextLike(r'.*success.*executed.*')),
        ('/info', match.AnyDict()),
        ('/info', {
            "id": match.AnyNumber(),
            "timestamp": match.AnyText(),
            "items": match.AnyListOf(item_type=1)
        }),
        ('/info/id', match.AnyNumberGreaterThan(-1)),
        # ('/info/timestamp', PAYLOAD_DETAILED['info']['timestamp']), -- to do Date Matcher
        ('/info/items', match.AnyListOfMatchersLongerThan(
            matcher=match.AnyNumberGreaterThan(0),
            size=0
        )),
        ('/info/items/0', match.AnyNumberGreaterThan(40)),
        ('/info/items/1', match.AnyNumberLessThan(4000)),
        ('/info/items/2', match.Anything()),
    ))
    def test_param_equals_using_matchers(self, api_response_detailed: ApiResponseHelper, param, expected):
        api_response_detailed.json.param_equals(param, expected)

    def test_param_equals_for_missing_param_fails(self, api_response_detailed: ApiResponseHelper):
        with pytest.raises(AssertionError,
                match='Param "/missing_param" is missing in the response JSON.*'):
            api_response_detailed.json.param_equals('/missing_param', 100500)

    def test_param_equals_comparison_fails(self, api_response_simple: ApiResponseHelper):
        with pytest.raises(AssertionError,
                match='Value of param "/status" is equal to .*, but expected to be .*'):
            api_response_simple.json.param_equals('/status', 'not match')
