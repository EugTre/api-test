"""Response helper and test wrapper"""
import json as json_encoder
from typing import Self, Any
from requests import Response, exceptions as requests_exceptions
from requests.models import CaseInsensitiveDict

import allure
from jsonschema import validate
from utils.api_client.models import ResponseEntity
from utils.json_content.json_content import JsonContent, JsonContentBuilder
from utils.json_content.pointer import ROOT_POINTER
from utils.matchers.matcher import BaseMatcher


class ExtendedJSONEncoder(json_encoder.JSONEncoder):
    """Adds correct encoding of matchers"""
    def default(self, o):
        if isinstance(o, BaseMatcher):
            return str(o)


def attach_as_text(name, body) -> None:
    """Wrapper for allure.attach function that
    converts data to JSON-formatted string"""
    allure.attach(
        name=name,
        body=json_encoder.dumps(body, indent=2, cls=ExtendedJSONEncoder),
        attachment_type=allure.attachment_type.TEXT
    )


class ResponseHeadersValidator:
    """Provide methods to validate reponse's headers"""
    def __init__(self, api_response_helper: 'ApiResponseHelper',
                 headers: dict):
        self.response_helper = api_response_helper
        self.headers = headers
        self.headers_lowercase = {
            header.lower(): value.lower()
            for header, value in headers.items()
        }
        self.expected: dict | None = None

    def set_expected(self, headers: dict) -> 'ApiResponseHelper':
        """Sets expected headers to compare against by other methods.

        Args:
            headers (dict): headers expected in the response.

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        self.expected = headers

        return self.response_helper

    @allure.step('Response headers are like expected')
    def are_like(self, headers: dict[str, str | BaseMatcher] | None = None
                 ) -> 'ApiResponseHelper':
        """Check that response headers are like given.
        If 'headers' not passed as parameter - headers
        from response section of Request Catalog entity will be used.

        Asserts that:
        - all passed headers are present
        - values of headers matches

        Use `utils.matchers.AnyText`, `utils.matchers.AnyTextLike` or
        `utils.matchers.AnyTextWith` to match by regex/substring matches.

        Args:
            expected_headers (dict[str,str], optional): dictionary of headers
            and it's values. Defaults to None (Request Catalog will be used
            or value set by .set_expected()).

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        desc = " (pre-defined)" if headers is None else ''
        expected_headers = self.__get_default_if_none(headers)

        failed = []
        for header, value in expected_headers.items():
            header = header.lower()
            if header not in self.headers:
                failed.append(f'header "{header}" not found')
                continue

            actual_value = self.headers[header]
            if value != actual_value:
                failed.append(
                    f'header\'s value "{header}" = "{actual_value}" '
                    f'doesn\'t match to expected value "{value}"'
                )

        attach_as_text(
            name=f"Expected headers{desc}",
            body=expected_headers
        )
        assert not failed, 'Response headers are not like expected: '\
            f'{", ".join(failed)}'

        return self.response_helper

    @allure.step('Response headers match to expected')
    def equals(self, headers: dict[str, str] = None, ignore: tuple = None
               ) -> 'ApiResponseHelper':
        """Check of response headers to be equal to given.
        If 'expected_headers' not passed as parameter - headers from response
        section of Request Catalog entity will be used.

        Asserts that:
        - all headers present in response, except headers listed in 'ignore'
        - there is no extra headers in response, except headers listed in
        'ignore'
        - values are exactly the same for checked headers

        Args:
            expected_headers (dict[str,str], optional): dictionary of headers
            and it's values. Defaults to None (Request Catalog will be used or
            value set by .set_expected()).
            ignore (optional, tuple): names of the headers that should be
            excluded from comparison (e.g. ('Accept', 'From')).
            Defaults to None.

        Returns:
            instance of class `ApiResponseHelper`
        """
        desc = " (pre-defined)" if headers is None else ''
        headers = self.__get_default_if_none(headers)

        # Make all header names lower case
        ignore = tuple(k.lower() for k in ignore) if ignore else tuple()
        expected_headers = {k.lower(): v
                            for k, v in headers.items()
                            if k.lower() not in ignore}
        response_headers = {k.lower(): v
                            for k, v in self.headers.items()
                            if k.lower() not in ignore}

        attach_as_text(
            name=f"Expected headers{desc}",
            body=expected_headers
        )
        assert response_headers == expected_headers, \
            'Headers are not equal to expected.'

        return self.response_helper

    @allure.step('Response headers are present')
    def present(self, *headers_to_check: str) -> 'ApiResponseHelper':
        """Checks that response contains all given headers.
        If headers not passed as parameter - headers from
        response section of Request Catalog entity
        or headers set via .set_expected() will be used.

        Assertion is case insensitive.

        Args:
            *headers (str): one or more header names to check.

        Returns:
            Instance of `ApiResponseHelper` class
        """
        desc = " (pre-defined)" if headers_to_check is None else ''
        headers_to_check = self.__get_default_if_none(headers_to_check)
        if isinstance(headers_to_check, dict):
            headers_to_check = headers_to_check.keys()

        missing_headers = [header for header in headers_to_check
                           if header not in self.headers]

        attach_as_text(
            name=f"Expected headers{desc}",
            body=headers_to_check
        )
        assert not missing_headers, \
            'Some headers are not present, but expected to be. '\
            f'Missing headers: {", ".join(missing_headers)}'

        return self.response_helper

    @allure.step('Response headers aren\'t present in response')
    def not_present(self, *headers_to_check: str) -> 'ApiResponseHelper':
        """Checks that response doesn't contain any of given headers.
        Assertion is case insensitive.

        Args:
            *headers (list | tuple): list of header names (str) to check.

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        present = [header for header in headers_to_check
                   if header in self.headers]

        assert not present, 'Some headers are present, but expected ' \
            f'not to be. Headers: {", ".join(present)}'

        return self.response_helper

    @allure.step('Response header "{header}" contains substring "{value}"')
    def header_contains(self, header: str, value: str,
                        case_sensitive: bool = False) -> 'ApiResponseHelper':
        """Checks that given header is present and it's value contains given
        substring 'value'.

        Args:
            header (str): name of the header.
            value (str): substring to find in header's value.
            case_sensitive (optiona, bool): flag to make assertion case
            sensetive. Defaults to False.

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        response_headers = self.__get(case_sensitive)
        header = header.lower()
        if not case_sensitive:
            value = value.lower()

        assert header in response_headers, \
            f'Header "{header}" is missing in response headers.'

        assert value in response_headers[header], \
            f'Value of header "{header}" = "{response_headers[header]} '\
            f'doesn\'t contain substring "{value}"'

        return self.response_helper

    @allure.step('Response header "{header}" equals to "{value}"')
    def header_equals(self, header: str, value: str,
                      case_sensitive: bool = False) -> 'ApiResponseHelper':
        """Checks that given header is present and it's value equals
        to given 'value'.

        Args:
            header (str): name of the header.
            value (str): value to compare.
            case_sensitive (optiona, bool): flag to make assertion case
            sensetive. Defaults to False.

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        response_headers = self.__get(case_sensitive)
        header = header.lower()
        if not case_sensitive:
            value = value.lower()

        assert header in response_headers, \
            f'Header "{header}" is missing in response headers.'

        assert response_headers[header] == value, \
            f'Value of header "{header}" is not equal to "{value}", '\
            'but expected to be.'

        return self.response_helper

    def __get(self, case_sensitive: bool = False) -> dict:
        """Returns response's headers. If flag 'case_sensitive' is
        set to False - returns all lowercase version of the headers
        (both keys and values).

        Args:
            case_sensitive (bool, optional): flag to return headers as
            all lowercase variant (False) or as is (True). Defaults to False.

        Returns:
            dict: headers
        """
        if case_sensitive:
            return self.headers

        return self.headers_lowercase

    def __get_default_if_none(self, headers: dict) -> dict:
        """Returns given value back or returns default expected headers if set.
        Otherwise - raises ValueError"""
        if headers is not None:
            return headers

        if not self.expected:
            raise ValueError(
                "There is no headers to compare - "
                "headers must be passed as argument, "
                "via .set_exepcted() method or defined in Request Catalog."
            )

        return self.expected


class ResponseBodyJsonValidatior:
    """Provide methods to validate JSON body of the repsonse"""
    def __init__(self, api_response_helper: 'ApiResponseHelper',
                 response_json: dict | None) -> None:
        self.response_helper: 'ApiResponseHelper' = api_response_helper
        self.content: JsonContent | None = None
        self.expected: JsonContent | None = None

        if response_json is not None:
            self.content = JsonContentBuilder() \
                            .from_data(response_json) \
                            .build()

    def set_expected(self, json_content: dict | JsonContent
                     ) -> 'ApiResponseHelper':
        """Sets expected JSON content to test against in various methods.

        Args:
            json_content (dict): response's body JSON parsed to dict

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        self.expected = json_content \
            if isinstance(json_content, JsonContent) else \
            JsonContentBuilder().from_data(json_content).build()

        return self.response_helper

    # -------
    # Overall JSON validation
    # -------
    @allure.step('Response JSON content equals to expected')
    def equals(self, json: JsonContent | dict | list = None,
               ignore: tuple = None) -> 'ApiResponseHelper':
        """"Compare JSON of response with given one or expected.

        Asserts that:
        - all keys from passed 'json' are present in response, except params
        listed in 'ignore'
        - there is no extra keys in response, except params listed in 'ignore'
        - values are excatly the same for all checked params

        Wrapped with Allure.Step.

        Args:
            json (JsonContent | dict | list, optional): JSON content to
            compare with. Defaults to None and content set via .set_expected()
            will be used.
            ignore (tuple, optional): JSON pointers to fields that should be
            excluded from comparison (e.g. ('/status', '/message/0')).
            Defaults to None.

        Raises:
            ValueError: If given JSON Pointers have invalid syntax.

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        desc = ' (pre-defined)' if json is None else ''
        self.response_helper.is_not_empty()

        # Make both dicts|lists
        json = self.__get_default_if_none(json)
        if isinstance(json, JsonContent):
            json = json.get()
        response_json = self.content.get()

        if ignore:
            # Make a copy and delete unwanted nodes
            builder = JsonContentBuilder()
            response_json = builder.from_data(response_json, True)\
                .build().delete(*ignore).get()
            json = builder.from_data(json, True)\
                .build().delete(*ignore).get()

        attach_as_text(name=f"Expected JSON{desc}", body=json)
        with allure.step('Response equals to expected'):
            assert response_json == json, \
                "Response's JSON is not equal to expected."

        return self.response_helper

    @allure.step('Response JSON content is like expected')
    def is_like(self, json: JsonContent | dict | list = None
                ) -> 'ApiResponseHelper':
        """Weak comparison of given JSON with response's JSON.
        Use `utils.matchers.AbstactMatcher` as values to check only
        datatypes/approximate values.

        Asserts that:
        - all keys from passed 'json' are present in response
        - given values are equal

        Args:
            json (JsonContent | dict | list, optional): JSON content to
            compare with.
            Defaults to None and content set via .set_expected() will be used.

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        desc = ' (pre-defined)' if json is None else ''
        self.response_helper.is_not_empty()

        json = self.__get_default_if_none(json)
        if not isinstance(json, JsonContent):
            json = JsonContentBuilder().from_data(json).build()

        failed = []
        on_key_missing = 'pointer "{ptr}" is missing'
        on_value_mismatch = 'value at pointer "{ptr}" = {value} ' \
                            '(of type: {value_type}) ' \
                            'doesn\'t match to expected value '\
                            '{expected_value} (of type: {expected_value_type})'
        for ptr, value in json:
            if ptr not in self.content:
                failed.append(on_key_missing.format(ptr=ptr.rfc_pointer))
                continue

            actual_value = self.content.get(ptr)

            if actual_value != value:
                failed.append(
                    on_value_mismatch.format(
                        ptr=ptr,
                        value=actual_value,
                        value_type=type(actual_value),
                        expected_value=value,
                        expected_value_type=type(value)
                    )
                )

        attach_as_text(name=f"Expected JSON{desc}", body=json.get())
        failed_explanation = "\n- ".join(failed) if failed else None
        with allure.step('JSON is like expected'):
            assert not failed, \
                f'JSON content is not like expected: \n- {failed_explanation}'

        return self.response_helper

    # -------
    # Params validation
    # -------
    def params_present(self, *pointers: str) -> 'ApiResponseHelper':
        """Checks that param is present in response

        Args:
            pointer (str): JSON pointers to params.

        Raises:
            AssertionError: when param is not present.
            ValueError: if JSON Pointer has invalid syntax.

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        with allure.step(f'Response has params "{pointers}"'):
            self.response_helper.is_not_empty()

            failed = [ptr for ptr in pointers if ptr not in self.content]
            with allure.step("Params are present"):
                assert not failed, 'Params are not present, ' \
                    f'but expected to be: {", ".join(failed)}'

        return self.response_helper

    def params_not_present(self, *pointers: str) -> 'ApiResponseHelper':
        """Checks that param is not present in response.

        Args:
            pointer (str): JSON pointer to param.

        Raises:
            AssertionError: when params is present.
            ValueError: if JSON Pointer has invalid syntax.

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        with allure.step('Response doesn\t has params "{pointers}"'):
            self.response_helper.is_not_empty()

            failed = [ptr for ptr in pointers if ptr in self.content]
            with allure.step('Params are not present'):
                assert not failed, 'Params are present, ' \
                    f'but not expected to be: {", ".join(failed)}'

        return self.response_helper

    def params_are_not_empty(self, *pointers: str) -> 'ApiResponseHelper':
        """Checks that value at given keylist is not empty or null.

        Args:
            pointer (str): JSON pointer to param.

        Raises:
            ValueError: if JSON Pointer has invalid syntax or
            refers to non-existent node.

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        with allure.step('Response has non-empty params "{pointers}"'):
            self.response_helper.is_not_empty()

            failed = []
            for ptr in pointers:
                if ptr not in self.content:
                    failed.append(f'param "{ptr}" is missing')
                    continue

                value = self.content.get(ptr)
                # Empty is None or empty str/dict/list
                if any((
                    value is None,
                    isinstance(value, (str, dict, list)) and not value
                )):
                    value_msg = f'"{value}"' \
                                if isinstance(value, str) else \
                                str(value)
                    failed.append(f'param "{ptr}" is empty '
                                  f'(value={value_msg})')

            failed_explanation = "\n- ".join(failed) if failed else None
            with allure.step("Params are not empty"):
                assert not failed, \
                    'Params are empty or missing, ' \
                    'but expected to present and ' \
                    'be not empty:\n' \
                    f'- {failed_explanation}'

        return self.response_helper

    def params_are_empty(self, *pointers: str) -> 'ApiResponseHelper':
        """Checks that value at given keylist is empty.

        Args:
            pointer (str): JSON pointer to param.

        Raises:
            AssertionError: when value is not empty.
            ValueError: if JSON Pointer has invalid syntax.
            KeyError/IndexError: if pointer refers to non-existsend
            key/out of range index.

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        with allure.step('Response has empty params "{pointers}"'):
            self.response_helper.is_not_empty()

            failed = []
            for ptr in pointers:
                if ptr not in self.content:
                    failed.append(f'param "{ptr}" is missing')
                    continue

                value = self.content.get(ptr)
                # Non empty is:
                #   any bool/number
                #   itarbale with non-zero length
                if any((
                    isinstance(value, (bool, int, float)),
                    isinstance(value, (str, dict, list)) and value
                )):
                    value_msg = f'"{value}"' \
                                if isinstance(value, str) else \
                                str(value)
                    failed.append(
                        f'param "{ptr}" is not empty (value={value_msg})'
                    )

            failed_explanation = "\n- ".join(failed) if failed else None

            with allure.step("Params are empty"):
                assert not failed, \
                    'Params are not empty or missing, ' \
                    'but expected to present and ' \
                    'be empty:\n' \
                    f'- {failed_explanation}'

        return self.response_helper

    def param_equals(self, pointer: str, value: Any) -> 'ApiResponseHelper':
        """Checks that given key has value equal to given.
        Use `utils.matchers` for inaccurate comparison.

        Args:
            pointer (str): JSON pointer to param.
            value (Any): value to compare with.

        Raises:
            AssertionError: when value is not equals to given.
            ValueError: if JSON Pointer has invalid syntax.
            KeyError/IndexError: if pointer refers to non-existsend key/out of
            range index.

        Returns:
            Instance of `ApiResponseHelper` class.
        """
        with allure.step(f'Response param "{pointer}" = {value}'):
            self.response_helper.is_not_empty()

            assert pointer in self.content, \
                f'Param "{pointer}" is missing in the response JSON.'

            actual_value = self.content.get(pointer)

            with allure.step("Response param equals to expected"):
                assert value == actual_value, \
                    f'Value of param "{pointer}" ' \
                    f'is equal to [{actual_value}], ' \
                    f'but expected to be [{value}]'

        return self

    # Private functions
    def __get_default_if_none(self, json: JsonContent | dict | None = None
                              ) -> JsonContent | dict:
        """Checks that given 'json' value and:
        - returns given value is it's not None
        - returns default expected JSON is it's None and expected is set
        - raises ValueError if bot given value and default expected value are
        None

        Args:
            json (JsonContent | dict | None, optional): JSON value to check.
            Defaults to None.

        Raises:
            ValueError: if both given and default values are
            not defined (None).

        Returns:
            JsonContent|dict: given value or default expected value.
        """
        if json is not None:
            return json

        if self.expected is None:
            raise ValueError(
                'There is no JSON to compare - expected JSON'
                'must be passed as argument, '
                'via .set_exepcted() method or defined in Request Catalog.'
            )
        return self.expected


class ApiResponseHelper:
    """Class that wraps isntance of `requests.Response` class
    with various helper and test functons.
    """
    def __init__(self, response: Response):
        self.response_object = response

        self.expected_status_code = 200
        self.expected_text = None
        self.schema = None

        try:
            json_of_response = self.response_object.json()
        except requests_exceptions.JSONDecodeError:
            json_of_response = None

        self.headers = ResponseHeadersValidator(self,
                                                self.response_object.headers)
        self.json = ResponseBodyJsonValidatior(self, json_of_response)

    # Setup functions
    def set_expected(self,
                     status_code: int | None = None,
                     schema: dict | None = None,
                     headers: dict | None = None,
                     json: JsonContent | dict | list | None = None,
                     text: str | None = None,
                     expected_response: ResponseEntity | None = None) -> Self:
        """Sets expected response data for futher use as defaults
        in validation methods.

        Args:
            status_code (int, optional): expected status code.
            Defaults to None.
            schema (dict, optional): expected JSON schema. Defaults to None.
            headers (JsonContent | dict, optional): expected headers.
            Defaults to None.
            json (JsonContent | dict | list, optional): expected JSON content.
            Defaults to None.
            text (str | None, optional): expected text body. Defaults to None.
            expected_response (utils.api_client.models.ResponseEntity):
            expected response params.
            Defaults to None.

        Returns:
            Self: instance of `ApiResponseHelper` class
        """

        # Apply data from response entity if passed.
        # (e.g. from pre-configured expected response)
        if expected_response:
            # Note: asdict() method parses Matchers into an dicts,
            # as they are dataclasses. So manually map fields
            self.set_expected(
                status_code=expected_response.status_code,
                schema=expected_response.schema,
                headers=expected_response.headers,
                json=expected_response.json,
                text=expected_response.text
            )

        # Then apply specific values
        if status_code is not None:
            self.expected_status_code = status_code
        if schema is not None:
            self.schema = schema
        if json is not None:
            self.json.set_expected(json)
        if headers is not None:
            self.headers.set_expected(headers)
        if text is not None:
            self.expected_text = text

        return self

    # General functions
    def get_response(self) -> Response | None:
        """Returns instance of `requests.Response` class
        if present. Otherwise returns None.

        Returns:
            Response: instance of `requests.Response` class or None,
            if no response was assigned earlier.
        """
        return self.response_object

    def get_headers(self) -> CaseInsensitiveDict:
        """Returns response's headers.

        Returns:
            CaseInsensitiveDict: response's headers.
        """
        return self.response_object.headers

    def get_json(self, as_dict: bool = False) -> JsonContent | dict:
        '''Returns response's JSON value

        Args:
            as_dict (optional, bool) - if True - returns dictionary,
            otherwise return JsonContent object.

        Raises:
            ValueError: if there is no JSON in resonse body.

        Return:
            dict: deserialized JSON data.
        '''
        if self.json.content is None:
            return None
            # raise ValueError('JSON is missing in response body.')

        return self.json.content.get() if as_dict else self.json.content

    def get_json_value(self, pointer: str) -> Any:
        """Returns value at given pointer.

        Args:
            pointer (str): JSON pointer to param.

        Raises:
            ValueError: if there is no JSON in resonse body.
            ValueError: if JSON Pointer has invalid syntax or
            refers to non-existent node.

        Returns:
            Any: found value
        """
        if self.json.content is None:
            raise ValueError('JSON is missing in response body.')

        return self.json.content.get(pointer)

    # -------
    # Response overall verification
    # -------
    def status_code_equals(self, status_code: int = None) -> Self:
        """Cheks that response's status code is equal to given one or
        to code set via .set_expected(status_code=???)

        Args:
            status_code (int, optional): expected status code. If not
            given self.expected_status_code will be used.

        Returns:
            Self: instance of `ApiResponseHelper` class
        """
        status_code = status_code if status_code else self.expected_status_code

        with allure.step(f'Response status code is {status_code}'):
            assert status_code == self.response_object.status_code, \
                f'Response status code {self.response_object.status_code} ' \
                f'doesn\'t match to expected code {status_code}.'

        return self

    @allure.step("Response is validated against JSON schema")
    def validates_against_schema(self, schema: dict = None) -> Self:
        """Validates response against given JSONSchema or schema
        from request config, if pre-configured request was made.
        Wrapped with Allure.Step.

        Args:
            schema (dict, optional): JSON schema. Defaults to None and
            looks for value from request configuration.

        Raises:
            ValueError: JSONSchema is not defined nor in request config,
            nor in method! Validation is not possible.
            RuntimeError: if response wasn't acquired yet.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        desc = " (pre-defined)" if schema is None else ''

        if schema is None:
            if self.schema is None:
                raise ValueError(
                    'JSONSchema is not defined nor in request config, '
                    'nor in method! Validation is not possible.'
                )
            schema = self.schema

        attach_as_text(
            name=f'Expected Schema{desc}',
            body=schema.get("title", "<untitled>")
        )
        validate(self.__get_value(ROOT_POINTER), schema)

        return self

    @allure.step('Response is empty')
    def is_empty(self) -> Self:
        """Checks that response content is empty.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        assert not self.response_object.text, \
            'Response has content, but expected to be empty.'

        return self

    @allure.step('Response is not empty')
    def is_not_empty(self) -> Self:
        """Checks that response content is not empty.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        assert self.response_object.text, \
            'Response has no content, but expected to be not empty.'

        return self

    @allure.step('Response equals to given')
    def equals(self, text: str | BaseMatcher | None = None) -> Self:
        """Checks that response content equals to given.

        Args:
            text (str | BaseMatcher): text to compare with or
            text matcher.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        self.is_not_empty()

        desc = "(pre-defined)" if text is None else ""
        if text is None:
            if self.expected_text is None:
                raise ValueError(
                    "There is no text to compare - "
                    "text must be passed as argument, "
                    "via .set_exepcted() method or defined in Request Catalog."
                )

            text = self.expected_text

        attach_as_text(name=f"Expected body text{desc}", body=text)
        with allure.step("Response content matches to expected"):
            assert self.response_object.text == text, \
                'Response content doesn\'t match to expected'

        return self

    @allure.step('Response latency is lower than {latency} ms')
    def latency_is_lower_than(self, latency: int) -> Self:
        """Checks that request lasted no longer than given latency.

        Args:
            latency (float | int): _description_

        Returns:
            Self: instance of class `ApiResponseHelper`
        """

        latensy_micro = self.response_object.elapsed.microseconds
        response_latency = int(latensy_micro // 1000)
        assert response_latency <= latency, \
            f'Response latency of {response_latency} ms is higher '\
            f'than expected {latency} ms'

        return self

    # Protected/private functions
    def __get_value(self, pointer: str) -> Any:
        """Returns value from response's JSON by given pointer.

        Args:
            pointer (str): JSON pointer to param.

        Raises:
            IndexError: on attempt to get element of list by out of
            bound index.
            KeyError: when pointer uses non-existent node.

        Returns:
            Any: found value
        """
        return self.json.content.get(pointer)

    def __repr__(self) -> str:
        method = self.response_object.request.method \
            if self.response_object.request else \
            ""

        return f'ApiResponseHelper(' \
            f'{method} ' \
            f'status_code={self.response_object.status_code}, ' \
            f'url={self.response_object.url})'
