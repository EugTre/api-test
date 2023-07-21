"""Helper for api request creation and execution."""
import re
from typing import Self

import allure
from utils.api_client.basic_api_client import BasicApiClient, HTTPMethod
from utils.api_client.models import RequestEntity
from utils.api_helpers.api_response_helper import ApiResponseHelper

class ApiRequestHelper:
    """Helper class that wraps API Client with additional function for testing response.
    """
    count = 1
    PATH_PATTERN = re.compile(r'{([a-zA-Z0-9]*)}')

    def __init__(self, api_client: BasicApiClient):
        """Creates instance of `ApiRequestHelper` class.

        Args:
            api_client (BasicApiClient): API client instance.
        """
        self.api_client = api_client
        self.name = ''
        self.request = None
        self.response = None

    def _reset(self):
        """Resets all properties to defaults.
        """
        self.name = ''
        self.request = None
        self.response = None

    # Request setup
    def by_name(self, name: str) -> Self:
        """Selects request from API Client's catalogue by request name.
        Invocation of the method resets instance's properties.

        Args:
            name (str): name of the request (defined in configuration file)

        Raises:
            ValueError: Unknown request name is given

        Returns:
            Self: instance of class `ApiRequestHelper`
        """
        self._reset()
        self.name = name
        req_cfg = self.api_client.request_catalog.get(name)
        if not req_cfg:
            raise ValueError(f'Unknown request name "{name}" for API '
                             f'"{self.api_client.name}"')
        self.request = req_cfg.request
        self.response = ApiResponseHelper().set_expected(
                            status_code=req_cfg.response.status_code,
                            schema=req_cfg.response.schema
                        )
        return self

    def by_path(self, path: str, method: HTTPMethod = HTTPMethod.GET,
                status_code: int = 200) -> Self:
        """Sets custom path for request.
        Invocation of the method resets instance's properties.

        Args:
            path (str): path of API request;
            method (str or HTTPMethod, optional): method to use for request.
            Defaults to `utils.base_api_client.HTTPMethod.GET`.
            status_code (int, optional): expected status code of the response. Defaults to 200.

        Returns:
            Self: instance of class `ApiRequestHelper`
        """
        self._reset()

        self.request = RequestEntity(
            method=method,
            path=path
        )
        self.response =  ApiResponseHelper().set_expected(status_code)

        return self

    def with_path_params(self, **path_params) -> Self:
        """Adds params which should be inserted into path's placeholders.
        Appends defaults params if defined for request.

        Args:
            **path_params - param's placeholder names and values.

        Returns:
            Self: instance of class `ApiRequestHelper`

        Raises:
            RuntimeError: request path is not defined yet.
            KeyError: Missing path parameter.
            ValueError: Extra path parameters given.

        Example:

        > req.by_path('random/images/{amount}').with_path_params(amount=10)
         # Path: 'random/images/10'
        """
        self.__check_request_initialized()

        if self.request.path_params.get('@use'):
            for default_param_name in self.request.path_params['@use']:
                path_params.setdefault(
                    default_param_name,
                    self.request.path_params[default_param_name]
                )

        self.request.path_params = path_params

        return self

    def with_query_params(self, **query_params) -> Self:
        """Adds params which should be added as URL query params.
        Appends defaults params if defined for request.

        Args:
            **query_params - params names and values.

        Returns:
            Self: instance of class `ApiRequestHelper`

        Example:

        > req.by_path('random/images').with_params(amount=10)
         # Path: 'random/images?amount=10'
        """
        self.__check_request_initialized()

        if self.request.query_params.get('@use'):
            for default_param_name in self.request.query_params['@use']:
                query_params.setdefault(
                    default_param_name,
                    self.request.query_params[default_param_name]
                )

        self.request.query_params = query_params

        return self

    def get_schema(self, name: str, fail_on_missing: bool = True) -> dict|None:
        """Returns schema from API Client's defaults

        Args:
            name (str): name of the schema.
            fail_on_missing (bool, optional): flag to raise an exception if
            schema not found. Defaults to True.

        Raises:
            ValueError: if schema not found and 'fail_on_missing' flag
            is set to True.

        Returns:
            dict|None: schema dictionary or None, if schema not found.
        """
        schema = self.api_client.request_defaults['schemas'].get(name)
        if fail_on_missing and not schema:
            raise ValueError(f'Failed to find "{name}" schema in '
                             f'"{self.api_client.name}" API Client.')

        return schema

    def perform(self, override_defaults: bool = False, **request_args) -> ApiResponseHelper:
        """Performs HTTP request with given request parameters (headers, cookies, json, etc.),
        creates and retuns `api_helpers.response_helper.ResponseHelper` with response (also
        verifies response status code).

        By default parameters will be appended with API's default request parameters. To use
        only given parameters set 'override_defaults' to True. However not specified parameters
        will be set to client's defaults!

        Args:
            override_defaults (bool, optional): Flag to override API Client's default parameters
            for response - 'headers', 'cookies', 'timeout', 'auth'. Defaults to False.
            **request_args: key-values pairs of `requests.request` method
            (headers, cookies, json, etc.)

        Raises:
            RuntimeError: Path is not defined for request.

        Returns:
            Self: instance of class `ApiRequestHelper`
        """
        self.__check_request_initialized()
        if self.request.path is None:
            raise RuntimeError('Path is not defined for request. '
                               'Make sure to use .by_path() or .by_name() method first!')

        self.__check_for_missing_path_params(self.request.path, self.request.path_params)

        path = (self.request.path.format(**self.request.path_params)
                if self.request.path_params else
                self.request.path)

        request_args['headers'] = self.request.headers | request_args.get('headers', {})
        request_args['cookies'] = self.request.cookies | request_args.get('cookies', {})
        request_args['auth'] = (request_args['auth']
                                if request_args.get('auth')
                                else tuple(self.request.auth) if self.request.auth else ())

        allure.dynamic.parameter(
            f'Request {self.count} (pre-configured, "{self.name}")'
            if self.name else
            f'Request {self.count}',
            {
                'path': path,
                'query': self.request.query_params if self.request.query_params else None,
                'params': request_args if request_args else None
            })

        request_step_info = f' "{self.name}"' if self.name else ''
        with allure.step(f'Request {self.count}{request_step_info} '
                         f'[method: {self.request.method}, url: {self.request.path}]'):
            response = self.api_client.request(method = self.request.method,
                                               path = path,
                                               params = self.request.query_params,
                                               override_defaults = override_defaults,
                                               **request_args)

            allure.dynamic.parameter(f'Request {self.count} completed', response.url)
            self.count += 1

        return self.response.set_and_verify_response(response)

    # Private methods
    def __check_request_initialized(self) -> None:
        """Checks that request path was already initialized.

        Raises:
            RuntimeError: Request is not initialized.
        """
        if self.request:
            return

        raise RuntimeError('Request is not initialized. '
                          'Use .by_name() or .by_path() methods first!')

    def __check_for_missing_path_params(self, path: str, params: dict) -> None:
        """Checks that given params fullfill all placeholders in given path.
        Missing or extra parameters will raise an exception.

        Args:
            path (str): path to check.
            params (dict): dictionary of parameters for path.

        Raises:
            KeyError: Missing path parameter.
            ValueError: Extra path parameters given.
        """
        expected_path_params = set(self.PATH_PATTERN.findall(path))
        params_set = set(params) if params else set()

        missing = expected_path_params - params_set
        if missing:
            raise KeyError(f'Missing path parameter(s): {", ".join(missing)}.')

        extra = params_set - expected_path_params
        if extra:
            raise ValueError(f'Extra path parameter(s) provided, '
                             f'but never used: {", ".join(extra)}')
