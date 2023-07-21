"""Response helper and test wrapper"""

from typing import Self, Any, Callable
from requests import Response

import allure
from jsonschema import validate


class ApiResponseHelper:
    """Class that wraps isntance of `requests.Response` class
    with various helper and test functons.
    """
    def __init__(self):
        self.expected_status_code = 200
        self.schema = None
        self.response_object = None
        self.json = None

    def set_expected(self, status_code: int, schema: dict = None) -> Self:
        '''Sets expected response data'''
        self.expected_status_code = status_code
        self.schema = schema
        return self

    def set_and_verify_response(self, response: Response) -> Self:
        """_summary_

        Args:
            response (Response): _description_

        Returns:
            Self: _description_
        """
        self.response_object = response

        with allure.step(f'Check response status code is {self.expected_status_code}'):
            assert self.expected_status_code == self.response_object.status_code, \
                   f'Response status code {self.response_object.status_code} doesn\'t '\
                   f'match to expected code {self.expected_status_code}.'

        return self

    # Public methods
    # General functions
    def get_json(self) -> dict:
        '''Returns response's JSON value

        Return:
            dict: deserialized JSON data.

        Raises:
            RuntimeError: if response wan't acquired yet.
        '''
        self.__except_on_response_missing()
        return self.__get_json()

    def get_response(self) -> Response|None:
        """Returns instance of `requests.Response` class
        if present. Otherwise returns None.

        Returns:
            Response: instance of `requests.Response` class or None,
            if no response was assigned earlier.
        """
        return self.response_object

    def get_value(self, keylist: str|tuple)-> Any:
        """Returns value at given key or tuple of nested keys.

        Args:
            keylist (str | tuple): key or tuple of successively nested keys.

        Returns:
            Any: found value

        Raises:
            RuntimeError: if response wan't acquired yet.
            KeyError: when keylist is invalid.
        """
        return self.__get_value(keylist)

    # Response overall verification
    @allure.step('Validate response against JSON schema')
    def validate(self, schema: dict = None) -> Self:
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
        self.__except_on_response_missing()

        if schema is None and self.schema is None:
            raise ValueError('JSONSchema is not defined nor in request config, '
                             'nor in method! Validation is not possible.')

        if schema is None:
            schema = self.schema

        validate(self.__get_json(), schema)

        return self

    @allure.step('Check response is empty')
    def is_empty(self) -> Self:
        """Checks that response content is empty.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        self.__except_on_response_missing()

        assert not self.__get_json(), 'Response has JSON content, but expected to be empty.'

        return self

    @allure.step('Check response is not empty')
    def is_not_empty(self) -> Self:
        """Checks that response content is not empty.

        Raises:
            RuntimeError: if response wan't acquired yet.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        self.__except_on_response_missing()

        assert self.__get_json(), 'Response has no JSON content, but expected to be not empty.'

        return self

    @allure.step('Check response latency is lower than {latency} ms')
    def latency_is_lower_than(self, latency: int):
        """Checks that request lasted no longer than given latency.

        Args:
            latency (float | int): _description_

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        self.__except_on_response_missing()
        response_latency = int(self.response_object.elapsed.microseconds / 1000)
        assert response_latency <= latency, \
            f'Response latency of {response_latency} ms is higher '\
            f'than expected {latency} ms'

        return self

    # Response's param verification
    # Single param
    @allure.step('Check response has param {keylist}')
    def param_presents(self, keylist: str|tuple) -> Self:
        """Checks that param is present in response'

        Args:
            keylist (str | tuple):  key or tuple of successively nested keys.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        self.__except_on_response_missing()
        is_present = True

        try:
            self.__get_value(keylist)
        except KeyError:
            is_present = False

        assert is_present, f'Param [{self.__keylist_to_str(keylist)}] is not present, ' \
            'but expected to be.'

        return self

    @allure.step('Check response has no param {keylist}')
    def param_not_presents(self, keylist: str|tuple) -> Self:
        """Checks that param is not present in response.

        Args:
            keylist (str | tuple):  key or tuple of successively nested keys.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        self.__except_on_response_missing()
        is_present = True

        try:
            self.__get_value(keylist)
        except KeyError:
            is_present = False

        assert not is_present, f'Param [{self.__keylist_to_str(keylist)}] is present, '\
            'but not expected to be.'

        return self

    @allure.step('Check response has non-empty param {keylist}')
    def value_is_not_empty(self, keylist: str|tuple) -> Self:
        """Checks that value at given keylist is not empty.

        Args:
            keylist (str | tuple):  key or tuple of successively nested keys.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        self.__except_on_response_missing()
        actual_value = self.__get_value(keylist)
        assert actual_value, \
               f'Value of param [{self.__keylist_to_str(keylist)}] is empty, '\
                   'but expected to be not empty.'

        return self

    @allure.step('Check response has empty param {keylist}')
    def value_is_empty(self, keylist: str|tuple) -> Self:
        """Checks that value at given keylist is empty.

        Args:
            keylist (str | tuple):  key or tuple of successively nested keys.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        self.__except_on_response_missing()
        actual_value = self.__get_value(keylist)
        assert not actual_value, \
               f'Value of param [{self.__keylist_to_str(keylist)}] is not empty '\
                'and equals to [{actual_value}], but expected to be empty.'

        return self

    @allure.step('Check response has param {keylist} = {value}')
    def value_equals(self, keylist: str|tuple, value: Any) -> Self:
        """Checks that given key contains given value.

        Args:
            keylist (str | tuple): key or tuple of successively nested keys.
            value (Any): value to compare with.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        self.__except_on_response_missing()

        try:
            actual_value = self.__get_value(keylist)
        except KeyError as exc:
            raise KeyError(f'Failed to find "{self.__keylist_to_str(keylist)}" '  \
                           'key in response body.') from exc

        assert value == actual_value, \
               f'Value of param [{self.__keylist_to_str(keylist)}] is equal to [{actual_value}], '\
               f'but expected to be [{value}]'

        return self

    @allure.step('Verify value of param {keylist} by custom function')
    def verify_value(self, keylist: str|tuple, verification_func: Callable) -> Self:
        """Execute given callable on response's param.

        Args:
            verification_func (Callable): callable that asserts some specific condition.
            keylist (str | tuple): key or tuple of successively nested keys that selects
            value which will be passed to verification_func.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        self.__except_on_response_missing()

        target = self.__get_value(keylist)

        verification_func(target)

        return self

    # Params of objects in array
    @allure.step('Check values of each object in array at {keylist}')
    def each_object_values_are(self, list_at: str|tuple = None, **params) -> Self:
        """Checks that:
        - given keylist contains an array
        - each element of array is an object
        - each element has given key and value

        Args:
            list_at (str | tuple): key or tuple of successively nested keys that leads to array.
            **params: key-value pairs to check against each array element.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        self.__except_on_response_missing()

        list_content = self.__get_array(list_at)

        with allure.step(f'Check {len(list_content)} object(s) has {params}'):
            for idx, item in enumerate(list_content):
                for param_name, param_value in params.items():
                    assert param_value == self.__get_value(param_name, item), \
                           f'Item {idx}: key \'{param_name}\' value doesn\'t match.'

        return self

    @allure.step('Verify each object in array at {keylist} by custom function')
    def verify_each_object(self, verification_func: Callable, list_at: str|tuple,
                           keylist: str|tuple) -> Self:
        """Execute given callable on response's param.
        - given `list_at` contains an array
        - each element of array is an object
        - each element has given `keylist`

        Args:
            verification_func (Callable): callable that asserts some specific condition.
            list_at (str | tuple): key or tuple of successively nested keys that leads to array.
            keylist (str | tuple): key or tuple of successively nested keys that selects
            value which will be passed to verification_func.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        self.__except_on_response_missing()

        list_content = self.__get_array(list_at)

        with allure.step(f'Check {len(list_content)} element(s) against custom function'):
            for item in list_content:
                target = self.__get_value(keylist, item)
                verification_func(target)

        return self

    # Elements of array
    @allure.step('Verify amount of array elements at {list_at}')
    def elements_count_is(self, list_at: str|tuple, value: int) -> Self:
        """Counts elements at given list_at and compare to given value.

        Args:
            list_at (str | tuple): key or tuple of successively nested keys
            that leads to array.
            value (int): value to compare with.

        Raises:
            RuntimeError: if response wan't acquired yet.

        Returns:
            Self: instance of class `ApiResponseHelper`
        """
        self.__except_on_response_missing()

        list_content = self.__get_array(list_at)
        list_size = len(list_content)
        assert list_size == value,\
            f'List at \'{list_at}\' contains {list_size} element(s), '\
            f'but expected to be {value} element(s) long.'

        return self

    @allure.step('Verify each array element at {list_at} by custom function')
    def verify_each(self, list_at: str|tuple, verification_func: Callable) -> Self:
        """Execute given verification_func on each element of array in list_at response param.

        Args:
            verification_func (Callable): callable that asserts some specific condition.
            list_at (str | tuple): key or tuple of successively nested keys that leads to array.

        Returns:
            Self: instance of class `ApiResponseHelper`

        Raises:
            RuntimeError: if response wan't acquired yet.
        """
        self.__except_on_response_missing()

        list_content = self.__get_array(list_at)

        with allure.step(f'Check {len(list_content)} element(s) against custom function'):
            for element in list_content:
                verification_func(element)

        return self

    # Protected/private functions
    def __get_json(self) -> dict:
        '''Caches and return cached deserialized JSON data from response.

        Return:
            dict: deserialized JSON data.
        '''
        if self.json is None:
            self.json = self.response_object.json()
        return self.json

    def __get_value(self, keylist: str|tuple, target: dict = None) -> Any:
        """Returns value at given key or tuple of nested keys.

        Args:
            keylist (str | tuple): key or tuple of successively nested keys.
            target (dict, optional): dictionary to search in. Defaults to response.json().

        Returns:
            Any: found value

        Raises:
            KeyError: when keylist is invalid.
        """
        if isinstance(keylist, str):
            keylist = (keylist, )

        if target is None:
            target = self.__get_json()

        value = target
        for key in keylist:
            value = value[key]

        return value

    def __get_array(self, keylist: str|tuple, target: dict = None) -> list|None:
        """Returns list at given key or tuple of nested keys.

        Args:
            keylist (str | tuple): key or tuple of successively nested keys.
            target (dict, optional): dictionary to search in. Defaults to response.json().

        Returns:
            Any: found value

        Raises:
            KeyError: when keylist is invalid.
        """
        list_content = (self.__get_json()
                        if keylist is None else
                        self.__get_value(keylist, target))

        assert isinstance(list_content, list), \
               f'Response\'s property at {self.__keylist_to_str(keylist)} is not an array.'
        return list_content

    def __except_on_response_missing(self) -> None:
        """Checks that request was made and response object exists.

        Raises:
            RuntimeError: Response object is not defined yet.
        """
        if self.response_object is None:
            raise RuntimeError('Response object is not defined yet. '
                                'Make sure to use .perform() first!')

    def __keylist_to_str(self, keylist: tuple|str) -> str:
        """Transform keylist tuple into a string of dot notaions.

        Args:
            keylist (tuple | str): key name or list of key names

        Returns:
            str: key list in dot notation.

        Example:
            > self.__keylist_to_str(('key1', 'key2', 'key3'))
             # 'key1.key2.key3'
        """
        if isinstance(keylist, str):
            return keylist

        return '.'.join(keylist)