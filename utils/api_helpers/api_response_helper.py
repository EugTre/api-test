"""Response helper and test wrapper"""

import re
from typing import Self, Any, Callable
from requests import Response, exceptions as requests_exceptions

import allure
from jsonschema import validate
from utils.json_content.json_content import JsonContent, JsonContentBuilder
from utils.json_content.json_wrapper import FlatJsonWrapper
from utils.json_content.pointer import Pointer, POINTER_PREFIX, ROOT_POINTER

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

        self.__headers_lowercase = {}
        for key, value in self.response_object.headers.items():
            self.__headers_lowercase[key.lower()] = value.lower()

        try:
            json_of_response = self.response_object.json()
        except requests_exceptions.JSONDecodeError:
            json_of_response = None

        self.__json_content = None
        if json_of_response is not None:
            self.__json_content = JsonContentBuilder() \
                                .from_data(json_of_response) \
                                .set_wrapper(FlatJsonWrapper) \
                                .build()

    # Public methods
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

    # General functions
    def get_json(self, as_dict: bool = False) -> dict:
        '''Returns response's JSON value

        Args:
            as_dict (optional, bool) - if True - returns dictionary,
            otherwise return JsonContent object.

        Return:
            dict: deserialized JSON data.

        Raises:
        '''
        if self.__json_content is None:
            return None

        return self.__json_content.get() if as_dict else self.__json_content

    def get_response(self) -> Response|None:
        """Returns instance of `requests.Response` class
        if present. Otherwise returns None.

        Returns:
            Response: instance of `requests.Response` class or None,
            if no response was assigned earlier.
        """
        return self.response_object

    def get_value(self, pointer: str)-> Any:
        """Returns value at given pointer.

        Args:
            pointer (str): JSON pointer to param.

        Raises:
            ValueError: if JSON Pointer has invalid syntax or
            refers to non-existent node.

        Returns:
            Any: found value
        """

        return self.__get_value(pointer)

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

    def validate_against_schema(self, schema: dict = None) -> Self:
        """Validates response against given JSONSchema or schema from request config,
        if pre-configured request was made.
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
        desc = "given JSON Schema"

        if schema is None:
            if self.schema is None:
                raise ValueError('JSONSchema is not defined nor in request config, '
                             'nor in method! Validation is not possible.')

            desc = "expected JSON Schema"
            schema = self.schema

        with allure.step(f'Validate response against {desc}'):
            validate(self.__get_value(ROOT_POINTER), schema)

        return self

    @allure.step('Check response is empty')
    def is_empty(self) -> Self:
        """Checks that response content is empty.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        assert not self.response_object.text, \
            'Response has JSON content, but expected to be empty.'

        return self

    @allure.step('Check response is not empty')
    def is_not_empty(self) -> Self:
        """Checks that response content is not empty.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        assert self.response_object.text, \
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
    @allure.step('Check headers are present in response.')
    def headers_present(self, *headers: str) -> Self:
        """Checks that response contains all given headers.
        If headers not passed as parameter - headers from
        response section of Request Catalog entity
        or headers set via .set_expected() will be used.

        Assertion is case insensitive.

        Args:
            *headers (str): one or more header names to check.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        if headers is None:
            if not self.expected_headers:
                raise ValueError("There is no headers to compare - "\
                    "headers must be passed as argument, "\
                    "via .set_exepcted() method or defined in Request Catalog.")

            headers = self.expected_headers.keys()

        missing_headers = [header for header in headers
                            if header not in self.response_object.headers]

        assert not missing_headers, 'Some headers are not present, but expected to be. '\
                                f'Missing headers: {", ".join(missing_headers)}'

        return self

    @allure.step('Check that headers aren\'t present in response.')
    def headers_not_present(self, *headers: str) -> Self:
        """Checks that response doesn't contain any of given headers.
        Assertion is case insensitive.

        Args:
            *headers (list | tuple): list of header names (str) to check.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        present = [header for header in headers
                    if header in self.response_object.headers]

        assert not present, 'Some headers are present, but expected not to be. '\
                                f'Headers: {", ".join(present)}'

        return self

    @allure.step('Check that header "{header}" contains substring "{value}"')
    def header_contains(self, header: str, value: str,
                        case_sensitive: bool = False) -> Self:
        """Checks that given header is present and it's value contains given
        substring 'value'.

        Args:
            header (str): name of the header.
            value (str): substring to find in header's value.
            case_sensitive (optiona, bool): flag to make assertion case
            sensetive. Defaults to False.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        response_headers = self.__get_headers(case_sensitive)
        header = header.lower()
        if not case_sensitive:
            value = value.lower()

        assert header in response_headers, \
            f'Header "{header}" is missing in response headers.'

        assert value in response_headers[header], \
            f'Value of header "{header}" = "{response_headers[header]} '\
            f'doesn\'t contain substring "{value}"'

        return self

    @allure.step('Check that header "{header}" equals to "{value}"')
    def header_equals(self, header: str, value: str,
                      case_sensitive: bool = False) -> Self:
        """Checks that given header is present and it's value equals
        to given 'value'.

        Args:
            header (str): name of the header.
            value (str): value to compare.
            case_sensitive (optiona, bool): flag to make assertion case
            sensetive. Defaults to False.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        response_headers = self.__get_headers(case_sensitive)
        header = header.lower()
        if not case_sensitive:
            value = value.lower()

        assert header in response_headers, \
            f'Header "{header}" is missing in response headers.'

        assert value == response_headers[header], \
            f'Value of header "{header}" is not equal to "{value}", '\
            'but expected to be.'

        return self

    @allure.step('Check that headers are like given')
    def headers_to_be_like(self, headers: dict[str, str] = None,
                     case_sensitive: bool = False) -> Self:
        """Check that response headers are like given.
        If 'expected_headers' not passed as parameter - headers
        from response section of Request Catalog entity will be used.

        Asserts that:
        - all passed headers are present
        - values of headers match to expected regex

        Args:
            expected_headers (dict[str,str], optional): dictionary of headers and
            it's values. Defaults to None (Request Catalog will be used or value
            set by .set_expected()).
            case_sensitive (optiona, bool): flag to make assertion case
            sensetive. Defaults to False.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        if headers is None:
            if not self.expected_headers:
                raise ValueError("There is no headers to compare - "\
                    "headers must be passed as argument, "\
                    "via .set_exepcted() method or defined in Request Catalog.")

            headers = self.expected_headers

        response_headers = self.__get_headers(case_sensitive)

        failed = []
        for header, value in headers.items():
            header = header.lower()
            if not case_sensitive:
                value = value.lower()

            if header not in response_headers:
                failed.append(f'header "{header}" not found')
            elif not re.match(value, response_headers[header]):
                failed.append(f'header\'s value "{header}" = "{response_headers[header]}" '
                              f'doesn\'t match to expected value "{value}"')

        assert not failed, f'Response headers are not like given: {", ".join(failed)}'

        return self

    @allure.step('Check that headers are match to given')
    def headers_equals(self, headers: dict[str, str] = None,
                     case_sensitive: bool = False, ignore: tuple = None) -> Self:
        """Check of response headers to be equal to given.
        If 'expected_headers' not passed as parameter - headers from response
        section of Request Catalog entity will be used.

        Asserts that:
        - all headers present in response, except headers listed in 'ignore'
        - there is no extra headers in response, except headers listed in 'ignore'
        - values are exactly the same for checked headers

        Args:
            expected_headers (dict[str,str], optional): dictionary of headers and
            it's values. Defaults to None (Request Catalog will be used or value
            set by .set_expected()).
            case_sensitive (optiona, bool): flag to make assertion case
            sensetive. Defaults to False.
            ignore (optional, tuple): names of the headers that should be excluded
            from comparison (e.g. ('Accept', 'From')). Defaults to None.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        if headers is None:
            if not self.expected_headers:
                raise ValueError("There is no headers to compare - "\
                    "headers must be passed as argument, "\
                    "via .set_exepcted() method or defined in Request Catalog.")

            headers = self.expected_headers

        response_headers = None
        expected_headers = None
        if case_sensitive:
            expected_headers = dict( (k.lower(), v) for k,v in headers.items() )
            response_headers = dict(
                (k.lower(), v)
                for k,v in self.__get_headers(case_sensitive=True).items()
            )
        else:
            expected_headers = dict( ((k.lower(), v.lower())
                                      for k, v in headers.items()) )
            response_headers = self.__get_headers()

        if ignore:
            ignore = tuple(
                (f'{POINTER_PREFIX}{k.lower()}'
                for k in ignore)
            )
            print(f'Ignoring: {ignore}')

            response_headers = JsonContentBuilder().from_data(
                response_headers, True).build().delete(*ignore).get()
            expected_headers = JsonContentBuilder().from_data(
                expected_headers, True).build().delete(*ignore).get()


        assert response_headers == expected_headers, \
            f'Headers are not equal to expected.\n' \
            f'Expected: {expected_headers}\n'\
            f'Actual:   {response_headers}'

        return self

    # Response's JSON body param verification
    @allure.step('Validate response JSON content')
    def json_equals(self, json: JsonContent|dict|list = None, ignore: tuple = None):
        """"Compare JSON of response with given one or JSON from request config,
        if pre-configured request was made.
        Wrapped with Allure.Step.

        Asserts that:
        - all keys from passed 'json' are present in response, except params listed in 'ignore'
        - there is no extra keys in response, except params listed in 'ignore'
        - values are excatly the same for all checked params

        Args:
            json (JsonContent | dict | list, optional): JSON content to compare with.
            Defaults to None.
            ignore (tuple, optional): JSON pointers to fields that should be excluded
            from comparison (e.g. ('/status', '/message/0')). Defaults to None.

        Raises:
            ValueError: If given JSON Pointers have invalid syntax.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        if json is None:
            if self.expected_json is  None:
                raise ValueError("There is no JSON to compare - "\
                    "expected JSON must be passed as argument, "\
                    "via .set_exepcted() method or defined in Request Catalog.")
            json = self.expected_json

        if not isinstance(json, JsonContent):
            json = JsonContentBuilder().from_data(json, True).build()

        response_json = self.response_object.json()
        if ignore:
            # Delete values to ignore - so it won't be compared
            response_json = JsonContentBuilder() \
                           .from_data(response_json, True) \
                           .build() \
                           .delete(*ignore)
            json.delete(*ignore)

        assert response_json == json, "Response's JSON is not equal to given one.\n"\
                f'Expected: {json}\n'\
                f'Actual:   {response_json}'

        return self

    def json_to_be_like(self, json: dict|list = None, case_sensitive: bool = False):
        """Weak comparison of given JSON with response's JSON.

        Asserts that:
        - all keys from passed 'json' are present in response
        - values are same type
        - string values match to given regexp
        - non-string values are equal

        Limitations:
        - values of list/dict type will be ignored!

        Args:
            json (dict | list, optional): _description_. Defaults to None.
            case_sensitive (bool, optional): _description_. Defaults to False.
        """
        if json is None:
            if self.expected_json is  None:
                raise ValueError("There is no JSON to compare - "\
                    "expected JSON must be passed as argument, "\
                    "via .set_exepcted() method or defined in Request Catalog.")
            json = self.expected_json

        expected_json = FlatJsonWrapper(json)
        actual_json = self.__json_content

        for ptr, expected_value in expected_json:
            assert actual_json.has(ptr), f'Param "{ptr}" is missing in response JSON'

            actual_value = actual_json.get(ptr)
            assert type(actual_value) is type(expected_value), \
                f'Actual value type "{type(actual_value)} is not the same as '\
                f'expected "{expected_value}" (of type: {type(expected_value)})'


            if isinstance(expected_value, str):
                # Consider expected string as regex
                assert re.match(expected_value, actual_value,
                                re.NOFLAG if case_sensitive else re.IGNORECASE)

            elif not isinstance(expected_value, (dict|list)):
                # Other expected values compare as is (excluding dicts and lists),
                # which may contain nestsed objects
                assert actual_value == expected_value

    # Single param
    @allure.step('Check response has param "{pointer}"')
    def param_presents(self, pointer: str) -> Self:
        """Checks that param is present in response

        Args:
            pointer (str): JSON pointer to param.

        Raises:
            AssertionError: when param is not present.
            ValueError: if JSON Pointer has invalid syntax.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """

        is_present = self.__has_param(pointer)
        assert is_present, f'Param "{pointer}" is not present, ' \
            'but expected to be.'

        return self

    @allure.step('Check response has no param "{pointer}"')
    def param_not_presents(self, pointer: str) -> Self:
        """Checks that param is not present in response.

        Args:
            pointer (str): JSON pointer to param.

        Raises:
            AssertionError: when params is present.
            ValueError: if JSON Pointer has invalid syntax.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """

        is_present = self.__has_param(pointer)
        assert not is_present, f'Param "{pointer}" is present, '\
            'but not expected to be.'

        return self

    @allure.step('Check response has non-empty param "{pointer}"')
    def value_is_not_empty(self, pointer: str) -> Self:
        """Checks that value at given keylist is not empty.

        Args:
            pointer (str): JSON pointer to param.

        Raises:
            ValueError: if JSON Pointer has invalid syntax or
            refers to non-existent node.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        actual_value = self.__get_value(pointer)
        assert actual_value, \
               f'Value of param "{pointer}" is empty, '\
                   'but expected to be not empty.'

        return self

    @allure.step('Check response has empty param "{pointer}"')
    def value_is_empty(self, pointer: str) -> Self:
        """Checks that value at given keylist is empty.

        Args:
            pointer (str): JSON pointer to param.

        Raises:
            AssertionError: when value is not empty.
            ValueError: if JSON Pointer has invalid syntax.
            KeyError/IndexError: if pointer refers to non-existsend
            key/out of range index.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        actual_value = self.__get_value(pointer)
        assert not actual_value, \
               f'Value of param "{pointer}" is not empty '\
                'and equals to [{actual_value}], but expected to be empty.'

        return self

    @allure.step('Check response has param "{pointer}" = {value}')
    def value_equals(self, pointer: str, value: Any) -> Self:
        """Checks that given key has value equal to given.

        Args:
            pointer (str): JSON pointer to param.
            value (Any): value to compare with.

        Raises:
            AssertionError: when value is not equals to given.
            ValueError: if JSON Pointer has invalid syntax.
            KeyError/IndexError: if pointer refers to non-existsend key/out of range index.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """

        actual_value = self.__get_value(pointer)
        assert value == actual_value, \
               f'Value of param "{pointer}" is equal to [{actual_value}], '\
               f'but expected to be [{value}]'

        return self

    @allure.step('Check response has param "{pointer}" like {value}')
    def value_contains(self, pointer: str, value: str) -> Self:
        """Checks that given key has value that contains given value substring.

        Args:
            pointer (str): JSON pointer to param.
            value (str): substring to be expected.

        Raises:
            AssertionError: when value doesn't include given substring.
            ValueError: if JSON Pointer has invalid syntax.
            KeyError/IndexError: if pointer refers to non-existsend
            key/out of range index.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """

        actual_value = self.__get_value(pointer)
        assert value in actual_value, \
               f'Value [{actual_value}] of param "{pointer}" doesn\'t '\
               f'contain [{value}].'

        return self

    def verify_value(self, pointer: str, verification_func: Callable,
                     value_to_compare: Any = None) -> Self:
        """Execute given callable on response's param.

        Args:
            verification_func (Callable): callable that asserts some
            specific condition.
            pointer (str): JSON pointer to param to pick value from
            and pass to to verification_func.

        Raises:
            AssertionError: produced by 'verification_func'.
            ValueError: if JSON Pointer has invalid syntax.
            KeyError/IndexError: if pointer refers to non-existsend
            key/out of range index.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        target_value = self.__get_value(pointer)
        # There are 2 verification_function to be expected:
        # - one that checks something without explicit comparison
        # - one that compares to user given value (comparators)
        # Depending on 'value_to_compare' - proper call is selected
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
    def each_object_values_are(self, list_at: str, params: dict) -> Self:
        """Checks that:
        - given pointer contains an array
        - each element of array is an object
        - each element has given key (pointer) and value

        Args:
            list_at (str): key or tuple of successively nested keys that leads to array.
            params (dict): key-value pairs to check against each array element in format
            {'/pointer': value}.

        Raises:
            AssertionError: if there is missing key or value doesn't equals
            AssertionError: if pointer doesn't refer to a list.
            ValueError: if JSON Pointer has invalid syntax.
            KeyError/IndexError: if pointer refers to non-existsend key/out of range index.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        list_content = self.__get_array(list_at)

        with allure.step(f'Check {len(list_content)} object(s) has {params}'):
            for idx, _ in enumerate(list_content):
                for param_name, param_value in params.items():
                    assert Pointer.match(param_name), \
                        f'Given object\'s pointer "{param_name}" is not valid JSON Pointer.'\
                        f'Should start with "{POINTER_PREFIX}".'

                    pointer = f'{list_at}/{idx}{param_name}'

                    assert self.__has_param(pointer), \
                            f'Item {idx}: key "{pointer}" is missing!'

                    assert param_value == self.__get_value(pointer), \
                           f'Item {idx}: key "{pointer}" value doesn\'t match.'

        return self

    @allure.step('Check values of each object in array at "{list_at}"')
    def each_object_values_like(self, list_at: str, params: dict) -> Self:
        """Checks that:
        - given pointer contains an array
        - each element of array is an object
        - each element has given key (pointer) and it's value contains given substring.

        Args:
            list_at (str): key or tuple of successively nested keys that leads to array.
            params (dict): key-value pairs to check against each array element in format
            {'/pointer': str}.

        Raises:
            AssertionError: if there is missing key or value doesn't equals
            AssertionError: if pointer doesn't refer to a list.
            ValueError: if JSON Pointer has invalid syntax.
            KeyError/IndexError: if pointer refers to non-existsend key/out of range index.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        list_content = self.__get_array(list_at)

        with allure.step(f'Check {len(list_content)} object(s) has params like {params}'):
            for idx, _ in enumerate(list_content):
                for param_name, param_value in params.items():
                    assert Pointer.match(param_name), \
                        f'Given object\'s pointer "{param_name}" is not valid JSON Pointer.'\
                        f'Should start with "{POINTER_PREFIX}".'

                    pointer = f'{list_at}/{idx}{param_name}'

                    assert self.__has_param(pointer), \
                            f'Item {idx}: key "{pointer}" is missing!'

                    actual_value = self.__get_value(pointer)
                    assert isinstance(actual_value, str), \
                        f'Item {idx}: "{pointer}" value "{actual_value}" is not a string!'

                    assert param_value in actual_value, \
                           f'Item {idx}: "{pointer}" value "{actual_value}" doesn\'t '\
                               'contain {param_value}!'

        return self

    @allure.step('Verify each object in array at "{list_at}" by custom function')
    def verify_each_object(self, verification_func: Callable, list_at: str,
                           pointer: str) -> Self:
        """Execute given callable on response's param. Considerations:
        - `list_at` points on an array
        - each element of array is an object
        - each element has given `keylist`

        Args:
            verification_func (Callable): callable that asserts some specific condition.
            list_at (str): pointer that leads to an array.
            pointer (str): pointer that selects value inside each object which
            will be passed to verification_func (e.g. '/id').

        Raises:
            AssertionError: if pointer doesn't refer to a list.
            ValueError: if JSON Pointer has invalid syntax.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        list_content = self.__get_array(list_at)

        assert Pointer.match(pointer), \
            f'Given object\'s pointer "{pointer}" is not valid JSON Pointer.'\
            f'Should start with "{POINTER_PREFIX}".'

        with allure.step(f'Check {len(list_content)} element(s) against custom function'):
            for idx, _ in enumerate(list_content):
                fq_pointer = f'{list_at}/{idx}{pointer}'

                assert self.__has_param(fq_pointer), \
                    f'Item {idx}: key "{fq_pointer}" is missing!'

                verification_func(self.__get_value(fq_pointer))

        return self

    # Elements of array
    @allure.step('Verify amount of array elements at "{list_at}"')
    def elements_count_is(self, list_at: str, value: int) -> Self:
        """Counts elements at given list_at and compare to given value.

        Args:
            list_at (str): pointer that leads to a list.
            value (int): value to compare with.

        Raises:
            AssertionError: if number of element not equals to expected.
            AssertionError: if pointer doesn't refer to a list.
            ValueError: if JSON Pointer has invalid syntax.
            KeyError/IndexError: if pointer refers to non-existsend key/out of range index.

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
    def verify_each(self, list_at: str, verification_func: Callable) -> Self:
        """Execute given verification_func on each element of array in list_at response param.

        Args:
            verification_func (Callable): callable that asserts some specific condition.
            list_at (str): pointer that leads to array.

        Raises:
            AssertionError: if pointer doesn't refer to a list.
            ValueError: if JSON Pointer has invalid syntax.
            KeyError/IndexError: if pointer refers to non-existsend key/out of range index.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        list_content = self.__get_array(list_at)

        with allure.step(f'Check {len(list_content)} element(s) against custom function'):
            for element in list_content:
                verification_func(element)

        return self


    # Protected/private functions
    def __get_json(self) -> JsonContent:
        """Returns iterable JSON Content object or raises ValueError
        if response body is missing any JSON data."""
        if self.__json_content is None:
            raise ValueError("There is no JSON found in Response body!")
        return self.__json_content

    def __has_param(self, pointer: str) -> bool:
        """Returns True if given pointer refers to existing param of
        response's JSON.

        Args:
            pointer (str): JSON pointer to param.

        Returns:
            bool: True if param exists, False otherwise.
        """
        return pointer in self.__json_content

    def __get_value(self, pointer: str) -> Any:
        """Returns value from response's JSON by given pointer.

        Args:
            pointer (str): JSON pointer to param.

        Raises:
            IndexError: on attempt to get element of list by out of bound index.
            KeyError: when pointer uses non-existent node.

        Returns:
            Any: found value
        """
        return self.__json_content.get(pointer)

    def __get_array(self, pointer: str) -> list|None:
        """Returns list at given key or tuple of nested keys.

        Args:
            pointer (str): JSON pointer to param.
            target (dict, optional): dictionary to search in. Defaults to response.json().

        Raises:
            AssertionError: if value at given pointer is not a list
            ValueError: if JSON Pointer has invalid syntax
            KeyError/IndexError: if pointer refers to non-existsend key/out of range index.

        Returns:
            Any: found array
        """
        assert pointer in self.__json_content, \
            f'Param "{pointer}" is missing in the response.'

        list_content = self.__json_content.get(pointer)
        assert isinstance(list_content, list), \
               f'Response\'s param at "{pointer}" is not an JSON array (list).'
        return list_content

    def __get_headers(self, case_sensitive: bool = False) -> dict:
        """Returns response's headers. If flag 'case_sensitive' is set to False -
        returns all lowercase version of the headers (both keys and values).

        Args:
            case_sensitive (bool, optional): flag to return headers as
            all lowercase variant (False) or as is (True). Defaults to False.

        Returns:
            dict: headers
        """
        if case_sensitive:
            return self.response_object.headers

        return self.__headers_lowercase
