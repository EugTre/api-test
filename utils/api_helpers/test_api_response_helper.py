"""Unit tests for Api Response Helper

pytest -s -vv ./utils/api_helpers/test_api_response_helper.py
"""
import datetime
import json

import pytest
import jsonschema.exceptions

from requests.models import Response
from utils.api_helpers.api_response_helper import ApiResponseHelper
from utils.json_content.json_content import JsonContent

# --- Constants
PAYLOAD_SIMPLE = payload = {
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
    "Accept-Charset": "iso-8859-5, Unicode-1-1; q = 0,8"
}

HEADERS_DETAILED = {
    "Accept": "text/plain, text/html, text/x-dvi",
    "Accept-Charset": "iso-8859-5, Unicode-1-1; q = 0,8",
    "Accept-Encoding": "gzip",
    "Cookie": "name1=value1; name2=value2; name3=value3",
    "From": "webmaster@example.com",
    "Referer": "http://www.example.com",
}

# --- Fixtures and functions
def mock_response(status_code: int,
                content: str = None,  json_content: dict|list = None,
                headers: dict = None, cookies: dict = None,
                latency: int = None) -> ApiResponseHelper:
    """Creates mocked `requests.models.Response` object

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

@pytest.fixture(name='api_response_simple')
def get_api_respnse_simple() -> ApiResponseHelper:
    return mock_response(200, json_content=PAYLOAD_SIMPLE,
                         headers=HEADERS_SIMPLE)

@pytest.fixture(name='api_response_detailed')
def get_api_respnse_detailed() -> ApiResponseHelper:
    return mock_response(200, json_content=PAYLOAD_DETAILED,
                         headers=HEADERS_DETAILED)


# Tests
# --- Positive tests

class TestApiResponseHelperBasic:
    """Basic tests of ApiResponseHelper"""

    def test_get_json(self):
        """.get_json() retuns Json Content object"""
        api_resp = mock_response(200, json_content=PAYLOAD_SIMPLE)

        resp_json_content = api_resp.get_json()
        assert isinstance(resp_json_content, JsonContent)
        assert resp_json_content == PAYLOAD_SIMPLE

    def test_get_json_as_dict(self):
        """.get_json() with as_dict=True option retuns dict object"""
        api_resp = mock_response(200, json_content=PAYLOAD_SIMPLE)

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
        api_resp = mock_response(200, json_content=PAYLOAD_DETAILED)
        assert api_resp.get_value(pointer) == expected


class TestApiResponseHelperGeneral:
    """Response general validation methods tests"""

    # status_code_equals(code)
    def test_status_code_equals(self):
        mock_response(200).status_code_equals(200)

    def test_set_expected_and_status_code_equals(self, api_response_simple: ApiResponseHelper):
        api_response_simple.set_expected(status_code=200).status_code_equals()

    def test_status_code_equals_asserts(self):
        with pytest.raises(AssertionError, match='Response status code.*doesn\'t match.*'):
            mock_response(404).status_code_equals(200)

    # validate_against_schema(schema)
    def test_valudate_against_schema(self, api_response_simple: ApiResponseHelper):
        api_response_simple.validate_against_schema(JSONSCHEMA_SIMPLE)

    def test_set_expected_and_valudate_against_schema(self, api_response_simple: ApiResponseHelper):
        api_response_simple.set_expected(schema=JSONSCHEMA_SIMPLE).validate_against_schema()

    def test_valudate_against_schema_asserts(self, api_response_simple: ApiResponseHelper):
        with pytest.raises(jsonschema.exceptions.ValidationError):
            api_response_simple.validate_against_schema(JSONSCHEMA_DETAILED)

    # is_empty
    def test_is_empty(self):
        mock_response(200).is_empty()

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
            mock_response(200).is_not_empty()

    # json_equals(json)
    def test_json_equals(self, api_response_simple: ApiResponseHelper):
        api_response_simple.json_equals(PAYLOAD_SIMPLE)

    def test_set_expected_and_json_equals(self, api_response_simple: ApiResponseHelper):
        api_response_simple.set_expected(json=PAYLOAD_SIMPLE).json_equals()

    def test_json_equals_asserts(self, api_response_simple: ApiResponseHelper):
        with pytest.raises(AssertionError,
                           match='Response\'s JSON is not equal to given one.*'):
            api_response_simple.json_equals({"status": "success"})

    # json_equals(json, ignoring)
    def test_json_equals_ignoring(self, api_response_detailed: ApiResponseHelper):
        api_response_detailed.json_equals(PAYLOAD_SIMPLE, ignore=("/info/id", "/info"))

    def test_set_expected_and_json_equals_ignoring(self, api_response_detailed: ApiResponseHelper):
        api_response_detailed.set_expected(json=PAYLOAD_SIMPLE) \
            .json_equals(ignore=("/info",))

    # latency_is_lower_than
    def test_latency_is_lower_than(self):
        mock_response(200, latency=250).latency_is_lower_than(500)

    def test_latency_is_lower_than_asserts(self):
        with pytest.raises(AssertionError,
                           match='Response latency of .* is higher than.*'):
            mock_response(200, latency=500).latency_is_lower_than(250)


class TestApiResponseHelperHeaders:
    """Response Headers validation methods tests"""
    # headers_present
    @pytest.mark.parametrize("headers", [
        ('Accept', 'Accept-Charset'),
        ('accept', 'accept-charset'),
        ('accepT', 'accept-Charset')
    ])
    def test_headers_present(self, api_response_simple: ApiResponseHelper, headers):
        """.headers_present() method test, including case insensitive checks"""
        api_response_simple.headers_present(*headers)

    def test_set_expected_and_headers_present(self, api_response_simple: ApiResponseHelper):
        api_response_simple.set_expected(headers=HEADERS_SIMPLE).headers_present()

    def test_headers_present_asserts(self, api_response_simple: ApiResponseHelper):
        headers = ["From", "Cookie", "Accept-encoding"]
        with pytest.raises(AssertionError,
                           match='Some headers are not present, but expected to be. '\
                                f'Missing headers: {", ".join(headers)}'):
            api_response_simple.headers_present(*headers)

    # headers_not_present
    def test_headers_not_present(self, api_response_simple: ApiResponseHelper):
        api_response_simple.headers_not_present("From", "Cookie", "Accept-Encoding")

    def test_headers_not_present_asserts(self, api_response_simple: ApiResponseHelper):
        with pytest.raises(AssertionError,
                           match='Some headers are present, but expected not to be.*'):
            api_response_simple.headers_not_present("Accept")

    # header_contains
    @pytest.mark.parametrize("header, expected, case_sensitive", [
        ("Accept", "text/html", True),
        ("ACCEPT", "Text/HTML", False),
        ("From", "example.com", True),
        ("accept-charset", "UNICODE", False)
    ])
    def test_header_contains(self, api_response_detailed: ApiResponseHelper,
                             header, expected, case_sensitive):
        api_response_detailed.header_contains(header, expected, case_sensitive)

    @pytest.mark.parametrize("header, expected, case_sensitive, exc_msg", [
        ("Foo", "Bar", True, 'Header ".*" is missing in response headers.'),
        ("From", "something.net", False, 'Value of header .* doesn\'t contain substring.*'),
        ("Accept-Charset", "UNICODE", True, 'Value of header .* doesn\'t contain substring.*')
    ])
    def test_header_contains_asserts(self, api_response_detailed: ApiResponseHelper,
                             header, expected, case_sensitive, exc_msg):
        with pytest.raises(AssertionError, match=exc_msg):
            api_response_detailed.header_contains(header, expected, case_sensitive)

    # header_equals
    @pytest.mark.parametrize("header, expected, case_sensitive", [
        ("Accept", "text/plain, text/html, text/x-dvi", True),
        ("ACCEPT", "TEXT/plain, TEXT/html, TEXT/x-dvi", False),
        ("From", "webmaster@example.com", True),
        ("accept-encoding", "GZIP", False)
    ])
    def test_header_equals(self, api_response_detailed: ApiResponseHelper,
                             header, expected, case_sensitive):
        api_response_detailed.header_equals(header, expected, case_sensitive)

    # headers_like
    @pytest.mark.parametrize("headers_like, case_sensitive", [
        ({
            "accept": "TEXT/HTML",
            "accept-charset": "unicode"
        }, False),
        ({
            "Accept": "text/html",
            "Accept-Charset": "Unicode"
        }, True)
    ])
    def test_headers_like(self, api_response_simple: ApiResponseHelper, headers_like, case_sensitive):
        api_response_simple.headers_like(headers_like, case_sensitive)

    def test_set_expected_and_headers_like(self, api_response_detailed: ApiResponseHelper):
        api_response_detailed.set_expected(headers=HEADERS_SIMPLE).headers_like()

    @pytest.mark.parametrize("headers_like, case_sensitive, exc_msg", [
        ({
            "origin": "something",
            "redirects": "allowedd"
        }, False, 'Headers are not like given:.*header ".*" not found.*'),
        ({
            "accept": "image/png",
            "accept-charset": "xcode"
        }, False, 'Headers are not like given:.*header ".*" doesn\'t contain value.*'),
        ({
            "accept": "image/png",
            "origin": "somewhere"
        }, False, 'Headers are not like given:.*header ".*" doesn\'t contain value.*header ".*" not found.*'),
        ({
            "Accept": "Text/HTML",
            "Accept-Charset": "UNICODE"
        }, True, 'Headers are not like given:.*header ".*" doesn\'t contain value.*')
    ])
    def test_headers_like_asserts(self, api_response_simple: ApiResponseHelper, headers_like, case_sensitive, exc_msg):
        with pytest.raises(AssertionError, match=exc_msg):
            api_response_simple.headers_like(headers_like, case_sensitive)

    # headers_match

    # set_expected:
    # + headers_present
    # + headers_not_present
    # + header_contains
    # + header_equals
    # + headers_like
    # + headers_match



class TestApiResponseHelperBody:
    """Response body validation methods tests"""
    # param_presents
    # param_not_presents
    # value_is_empty
    # value_equals
    # value_contains
    # verify_value
    #
    # each_object_values_are
    # each_object_values_like
    # verify_each_object
    #
    # elements_count_is
    # verify_each
