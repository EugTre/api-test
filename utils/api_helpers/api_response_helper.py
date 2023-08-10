"""Response helper and test wrapper"""

from typing import Self, Any, Callable
from requests import Response

import allure
from jsonschema import validate
from utils.json_content.json_content import JsonContent, JsonContentBuilder
from utils.json_content.pointer import Pointer, POINTER_PREFIX

class ApiResponseHelper:
    """Class that wraps isntance of `requests.Response` class
    with various helper and test functons.
    """
    def __init__(self, response: Response):
        self.response_object = response

        self.expected_status_code = 200
        self.expected_json = None
        self.expected_headers = None
        self.schema = None

        self.__json_content = None
        self.__headers_lowercase = None

    def set_expected(self, status_code: int = None,
                     schema: dict = None,
                     headers: JsonContent|dict = None,
                     json: JsonContent|dict|list = None) -> Self:
        """Sets expected response data for futher use as defaults in validation methods.

        Args:
            status_code (int, optional): expected status code. Defaults to None.
            schema (dict, optional): expected JSON schema. Defaults to None.
            headers (JsonContent | dict, optional): expected headers. Defaults to None.
            json (JsonContent | dict | list, optional): expected JSON content. Defaults to None.

        Returns:
            Self: instance of `ApiResponseHelper` class
        """
        if status_code is not None:
            self.expected_status_code = status_code
        if schema is not None:
            self.schema = schema
        if json is not None:
            self.expected_json = json.get() if isinstance(json, JsonContent) else json
        if headers is not None:
            self.expected_headers = headers.get() if isinstance(headers, JsonContent) else headers

        return self

    # Public methods
    # General functions
    def get_json(self, as_dict: bool = False) -> dict:
        '''Returns response's JSON value

        Args:
            as_dict (optional, bool) - if True - returns dictionary,
            otherwise return JsonContent object.

        Return:
            dict: deserialized JSON data.

        Raises:
            RuntimeError: if response wan't acquired yet.
        '''
        content = self.__get_json()

        return content.get() if as_dict else content

    def get_response(self) -> Response|None:
        """Returns instance of `requests.Response` class
        if present. Otherwise returns None.

        Returns:
            Response: instance of `requests.Response` class or None,
            if no response was assigned earlier.
        """
        return self.response_object

    def get_value(self, pointer: str|Pointer)-> Any:
        """Returns value at given key or tuple of nested keys.

        Args:
            pointer (str | Pointer): JSON pointer.

        Returns:
            Any: found value

        Raises:
            RuntimeError: if response wan't acquired yet.
            KeyError: when keylist is invalid.
        """

        return self.__get_json().get(pointer)

    # Response overall verification
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

        with allure.step(f'Check response status code is {status_code}'):
            assert status_code == self.response_object.status_code, \
                   f'Response status code {self.response_object.status_code} doesn\'t '\
                   f'match to expected code {status_code}.'

        return self

    @allure.step('Validate response against JSON schema')
    def validate_against_schema(self, schema: dict = None) -> Self:
        """Validates response against given JSONSchema or schema from request config,
        if pre-configured request was made.
        Wrapped with Allure.Step.

        Args:
            schema (dict, optional): JSON schema. Defaults to None and
            looks for value from request configuration.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            ValueError: JSONSchema is not defined nor in request config,
            nor in method! Validation is not possible.
            RuntimeError: if response wan't acquired yet.
        """
        if schema is None and self.schema is None:
            raise ValueError('JSONSchema is not defined nor in request config, '
                             'nor in method! Validation is not possible.')

        if schema is None:
            schema = self.schema

        validate(self.__get_json().get(), schema)

        return self

    @allure.step('Validate response JSON content')
    def json_equals(self, json: JsonContent|dict|list = None, ignore: tuple = None):
        """Compare JSON of response with given one"""
        if json is None:
            json = self.expected_json

        response_json = self.__get_json()
        if isinstance(response_json, dict):
            if ignore:
                # Delete values to ignore - so it won't be compared
                response_json = JsonContentBuilder() \
                                .from_data(self.response_object.json, True) \
                                .build() \
                                .delete(ignore) \
                                .get()
            if isinstance(json, JsonContent):
                json = json.get()

        assert response_json == json, "Response's JSON is not equal to given one.\n"\
                f'Expected: {json}\n'\
                f'Actual:   {response_json}'

        return self

    @allure.step('Check response is empty')
    def is_empty(self) -> Self:
        """Checks that response content is empty.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        assert not self.__get_json().get(), \
            'Response has JSON content, but expected to be empty.'

        return self

    @allure.step('Check response is not empty')
    def is_not_empty(self) -> Self:
        """Checks that response content is not empty.

        Raises:
            RuntimeError: if response wan't acquired yet.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        assert self.__get_json().get(), \
            'Response has no JSON content, but expected to be not empty.'

        return self

    @allure.step('Check response latency is lower than {latency} ms')
    def latency_is_lower_than(self, latency: int) -> Self:
        """Checks that request lasted no longer than given latency.

        Args:
            latency (float | int): _description_

        Returns:
            Self: instance of class `ApiResponseHelper`
        """

        response_latency = int(self.response_object.elapsed.microseconds / 1000)
        assert response_latency <= latency, \
            f'Response latency of {response_latency} ms is higher '\
            f'than expected {latency} ms'

        return self

    # Headers
    @allure.step('Check all headers are present in response.')
    def headers_present(self, *headers: str) -> Self:
        """Checks that response contains all given headers.
        If headers not passed as parameter - headers from
        response section of Request Catalog entity will be used.

        Assertion is case insensitive.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        if headers is None:
            if self.expected_headers:
                headers = self.expected_headers.keys()
            else:
                raise ValueError("There is no headers to compare - headers must "
                    "be passed as argument or defined in Request Catalog.")

        response_headers = self.__get_headers()
        not_present = [header
                       for header in headers
                       if header.lower() not in response_headers]

        assert not not_present, 'Some headers are not present, but expected to be. '\
                                f'Missing headers: {", ".join(not_present)}'

        return self

    @allure.step('Check that headers aren\'t present in response.')
    def headers_not_present(self, *headers: str) -> Self:
        """Checks that response doesn't contain any of given headers.
        If headers not passed as parameter - headers from
        response section of Request Catalog entity will be used.

        Assertion is case insensitive.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        if headers is None:
            if self.expected_headers:
                headers = self.expected_headers.keys()
            else:
                raise ValueError("There is no headers to compare - headers must "
                    "be passed as argument or defined in Request Catalog.")

        response_headers = self.__get_headers()
        present = [header
                   for header in headers
                   if header.lower() in response_headers]

        assert not present, 'Some headers are present, but expected not to be. '\
                                f'Headers: {", ".join(present)}'

        return self

    @allure.step('Check that header "{header}" contains substring "{value}"')
    def header_contains(self, header: str, value: str,
                        case_insensetive: bool = True) -> Self:
        """Checks that given header is present and it's value contains given
        substring 'value'.

        Args:
            header (str): name of the header.
            value (str): substring to find in header's value.
            case_insensetive (optiona, bool): flag to make assertion case
            insensetive. Defaults to True.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        response_headers = self.__get_headers(case_insensetive)
        if case_insensetive:
            header = header.lower()
            value = value.lower()

        assert header in response_headers, \
            f'Header "{header}" is missing in response headers.'

        assert value in response_headers[header], \
            f'Value of header "{header}" = "{response_headers[header]} '\
            f'doesn\'t contain substring "{value}"'

        return self

    @allure.step('Check that header "{header}" equals to "{value}"')
    def header_equals(self, header: str, value: str,
                      case_insensetive: bool = True) -> Self:
        """Checks that given header is present and it's value equals
        to given 'value'.

        Args:
            header (str): name of the header.
            value (str): value to compare.
            case_insensetive (optiona, bool): flag to make assertion case
            insensetive. Defaults to True.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        response_headers = self.__get_headers(case_insensetive)
        if case_insensetive:
            header = header.lower()
            value = value.lower()

        assert header in response_headers, \
            f'Header "{header}" is missing in response headers.'

        assert value == response_headers[header], \
            f'Value of header "{header}" is not equal to "{value}", '\
            'but expected to be.'

        return self

    @allure.step('Check that headers are like given')
    def headers_like(self, expected_headers: dict = None,
                     case_insensetive: bool = True) -> Self:
        """Check of response headers to be like given.
        If 'expected_headers' not passed as parameter - headers
        from response section of Request Catalog entity will be used.

        Args:
            expected_headers (dict, optional): dictionary of headers and it's values.
            Defaults to None (Request Catalog will be used).
            case_insensetive (optiona, bool): flag to make assertion case
            insensetive. Defaults to True.

        Returns:
            Self: _description_
        """
        if expected_headers is None:
            if self.expected_headers:
                expected_headers = self.expected_headers
            else:
                raise ValueError("There is no headers to compare - headers must "
                    "be passed as argument or defined in Request Catalog.")

        response_headers = self.__get_headers(case_insensetive)

        failed = []
        for header, value in expected_headers.items():
            if case_insensetive:
                header = header.lower()
                value = value.lower()

            if header in response_headers and value not in response_headers[header]:
                failed.append(f'header "{header}" doesn\'t contain value "{value}"')
            else:
                failed.append(f'header "{header}" not found')

        assert not failed, f'Headers are not like given: {", ".join(failed)}'

        return self

    @allure.step('Check that headers are match to given')
    def headers_match(self, expected_headers: dict = None,
                     case_insensetive: bool = True) -> Self:
        """Check of response headers to be equal to given.
        If 'expected_headers' not passed as parameter - headers from response
        section of Request Catalog entity will be used.

        Args:
            expected_headers (dict, optional): dictionary of headers and it's values.
            Defaults to None (Request Catalog will be used).
            case_insensetive (optiona, bool): flag to make assertion case
            insensetive. Defaults to True.

        Returns:
            Self: _description_
        """
        if expected_headers is None:
            if self.expected_headers:
                expected_headers = self.expected_headers
            else:
                raise ValueError("There is no headers to compare - headers must "
                    "be passed as argument or defined in Request Catalog.")

        response_headers = self.__get_headers(case_insensetive)

        failed = []
        for header, value in expected_headers.items():
            if case_insensetive:
                header = header.lower()
                value = value.lower()

            if header in response_headers and value != response_headers[header]:
                failed.append(f'header "{header}" doesn\'t equals to "{value}"')
            else:
                failed.append(f'header "{header}" not found')

        assert not failed, f'Headers doesn\'t match to given: {", ".join(failed)}'

        return self

    # Response's param verification
    # Single param
    @allure.step('Check response has param "{pointer}"')
    def param_presents(self, pointer: str|Pointer) -> Self:
        """Checks that param is present in response'

        Args:
            pointer (str | Pointer):  key or tuple of successively nested keys.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """

        is_present = True

        try:
            self.__get_value(pointer)
        except KeyError:
            is_present = False

        assert is_present, f'Param "{pointer}" is not present, ' \
            'but expected to be.'

        return self

    @allure.step('Check response has no param "{pointer}"')
    def param_not_presents(self, pointer: str|Pointer) -> Self:
        """Checks that param is not present in response.

        Args:
            pointer (str | Pointer):  key or tuple of successively nested keys.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """

        is_present = True

        try:
            self.__get_value(pointer)
        except KeyError:
            is_present = False

        assert not is_present, f'Param "{pointer}" is present, '\
            'but not expected to be.'

        return self

    @allure.step('Check response has non-empty param "{pointer}"')
    def value_is_not_empty(self, pointer: str|Pointer) -> Self:
        """Checks that value at given keylist is not empty.

        Args:
            pointer (str | Pointer):  key or tuple of successively nested keys.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """

        actual_value = self.__get_value(pointer)
        assert actual_value, \
               f'Value of param "{pointer}" is empty, '\
                   'but expected to be not empty.'

        return self

    @allure.step('Check response has empty param "{pointer}"')
    def value_is_empty(self, pointer: str|Pointer) -> Self:
        """Checks that value at given keylist is empty.

        Args:
            pointer (str | Pointer):  key or tuple of successively nested keys.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """

        actual_value = self.__get_value(pointer)
        assert not actual_value, \
               f'Value of param "{pointer}" is not empty '\
                'and equals to [{actual_value}], but expected to be empty.'

        return self

    @allure.step('Check response has param "{pointer}" = {value}')
    def value_equals(self, pointer: str|Pointer, value: Any) -> Self:
        """Checks that given key contains given value.

        Args:
            pointer (str | Pointer): key or tuple of successively nested keys.
            value (Any): value to compare with.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        try:
            actual_value = self.__get_value(pointer)
        except KeyError as exc:
            raise KeyError(f'Failed to find "{pointer}" '  \
                           'key in response body.') from exc

        assert value == actual_value, \
               f'Value of param "{pointer}" is equal to [{actual_value}], '\
               f'but expected to be [{value}]'

        return self

    def verify_value(self, pointer: str|Pointer, verification_func: Callable,
                     value_to_compare: Any = None) -> Self:
        """Execute given callable on response's param.

        Args:
            verification_func (Callable): callable that asserts some specific condition.
            pointer (str | Pointer): key or tuple of successively nested keys that selects
            value which will be passed to verification_func.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        target_value = self.__get_value(pointer)
        if value_to_compare is None:
            with allure.step(f'Verify value of param "{pointer}" '
                            f'by {verification_func.__name__}'):
                verification_func(target_value)
        else:
            with allure.step(f'Verify that value of param "{pointer}" '
                            f'{verification_func.__name__} {value_to_compare}'):
                verification_func(target_value, value_to_compare)

        return self

    # Params of objects in array
    @allure.step('Check values of each object in array at "{list_at}"')
    def each_object_values_are(self, list_at: str|Pointer, **params) -> Self:
        """Checks that:
        - given keylist contains an array
        - each element of array is an object
        - each element has given key and value

        Args:
            list_at (str | Pointer): key or tuple of successively nested keys that leads to array.
            **params: key-value pairs to check against each array element.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        list_content = self.__get_array(list_at)

        with allure.step(f'Check {len(list_content)} object(s) has {params}'):
            for idx, _ in enumerate(list_content):
                for param_name, param_value in params.items():
                    pointer = f'{list_at}/{idx}/{param_name}'
                    assert param_value == self.__get_value(pointer), \
                           f'Item {idx}: key "{pointer}" value doesn\'t match.'

        return self

    @allure.step('Verify each object in array at "{list_at}" by custom function')
    def verify_each_object(self, verification_func: Callable, list_at: str|Pointer,
                           pointer: str) -> Self:
        """Execute given callable on response's param. Considerations:
        - `list_at` points on an array
        - each element of array is an object
        - each element has given `keylist`

        Args:
            verification_func (Callable): callable that asserts some specific condition.
            list_at (str | Pointer): pointer that leads to array.
            pointer (str): pointer that selects value inside each object which
            will be passed to verification_func.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        list_content = self.__get_array(list_at)
        pointer = (pointer
                   if pointer.startswith(POINTER_PREFIX) else
                   f'{POINTER_PREFIX}{pointer}')

        with allure.step(f'Check {len(list_content)} element(s) against custom function'):
            for idx, _ in enumerate(list_content):
                object_pointer = f'{list_at}/{idx}/{pointer}'
                verification_func(self.__get_value(object_pointer))

        return self

    # Elements of array
    @allure.step('Verify amount of array elements at "{list_at}"')
    def elements_count_is(self, list_at: str|Pointer, value: int) -> Self:
        """Counts elements at given list_at and compare to given value.

        Args:
            list_at (str | Pointer): pointer that leads to array.
            value (int): value to compare with.

        Raises:
            RuntimeError: if response wan't acquired yet.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        list_content = self.__get_array(list_at)
        list_size = len(list_content)
        assert list_size == value,\
            f'List at \'{list_at}\' contains {list_size} element(s), '\
            f'but expected to be {value} element(s) long.'

        return self

    @allure.step('Verify each array element at "{list_at}" by custom function')
    def verify_each(self, list_at: str|Pointer, verification_func: Callable) -> Self:
        """Execute given verification_func on each element of array in list_at response param.

        Args:
            verification_func (Callable): callable that asserts some specific condition.
            list_at (str | Pointer): pointer that leads to array.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """


        list_content = self.__get_array(list_at)

        with allure.step(f'Check {len(list_content)} element(s) against custom function'):
            for element in list_content:
                verification_func(element)

        return self


    # Protected/private functions
    def __get_json(self) -> JsonContent:
        '''Caches and return cached deserialized JSON data from response.

        Return:
            dict: deserialized JSON data.
        '''
        if self.__json_content is None:
            self.__json_content = JsonContentBuilder().from_data(self.response_object.json())\
                .allow_reference_resolution(False, False).build()
        return self.__json_content

    def __get_value(self, pointer: str|Pointer) -> Any:
        return self.__get_json().get(pointer)

    def __get_array(self, pointer: str|Pointer) -> list|None:
        """Returns list at given key or tuple of nested keys.

        Args:
            keylist (str | tuple): key or tuple of successively nested keys.
            target (dict, optional): dictionary to search in. Defaults to response.json().

        Returns:
            Any: found value

        Raises:
            KeyError: when keylist is invalid.
        """
        list_content = self.__get_value(pointer)

        assert isinstance(list_content, list), \
               f'Response\'s property at "{pointer}" is not an array.'
        return list_content

    def __get_headers(self, case_insensitive: bool = True) -> dict:
        """Returns response's headers. If flag 'case_insensitive' is set to True -
        returns all lowercase version of the headers (both keys and values).

        Args:
            case_insensitive (bool, optional): flag to return headers as
            all lowercase variant (True) or as is (False). Defaults to True.

        Returns:
            dict: _description_
        """
        if not case_insensitive:
            return self.response_object.headers

        if not self.__headers_lowercase:
            self.__headers_lowercase = {}
            for k, v in self.response_object.headers.items():
                self.__headers_lowercase[k.lower()] = v.lower()

        return self.__headers_lowercase
