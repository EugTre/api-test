"""Helper for api request creation and execution."""
import re
import copy
from typing import Self
from dataclasses import asdict

import allure
from utils.api_client.basic_api_client import BasicApiClient, HTTPMethod
from utils.api_client.models import RequestEntity, ResponseEntity
from utils.json_content.json_content import JsonContent
from utils.api_helpers.api_response_helper import ApiResponseHelper


class ApiRequestHelper:
    """Helper class that wraps API Client with additional function for testing response.
    """
    count = 1
    PATH_PATTERN = re.compile(r'{([a-zA-Z0-9_]*)}')

    def __init__(self, api_client: BasicApiClient):
        """Creates instance of `ApiRequestHelper` class.

        Args:
            api_client (BasicApiClient): API client instance.
        """
        self.api_client = api_client
        self.name = ''
        self.request: RequestEntity|None = None
        self.expected: ResponseEntity|None = None

    def _reset(self):
        """Resets all properties to defaults.
        """
        self.name = ''
        self.request = None
        self.expected = None

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
        req_cfg = self.api_client.get_from_catalog(name)
        if not req_cfg:
            raise ValueError(f'Unknown request name "{name}" for API '
                             f'"{self.api_client.name}"')

        # Collect use by default path and query params
        path_params = {}
        if req_cfg.request.path_params is not None and req_cfg.request.path_params.get('@use'):
            for default_param_name in req_cfg.request.path_params['@use']:
                path_params[default_param_name] = req_cfg.request.path_params[default_param_name]

        query_params = {}
        if req_cfg.request.query_params is not None and req_cfg.request.query_params.get('@use'):
            for default_param_name in req_cfg.request.query_params['@use']:
                query_params[default_param_name] = req_cfg.request.query_params[default_param_name]

        self.request = copy.deepcopy(req_cfg.request)
        self.request.path_params = path_params
        self.request.query_params = query_params

        self.expected = copy.deepcopy(req_cfg.response)

        return self

    def by_path(self, path: str|None = None, method: HTTPMethod = HTTPMethod.GET) -> Self:
        """Sets custom path and method for request, and initialize expected response
        with default status code 200.
        Invocation of the method resets instance's properties.

        Args:
            path (str): path of API request;
            method (str or HTTPMethod, optional): method to use for request.
            Defaults to `utils.base_api_client.HTTPMethod.GET`.

        Returns:
            Self: instance of class `ApiRequestHelper`
        """
        self._reset()

        self.request = RequestEntity(
            method=method,
            path=path if path is not None else ''
        )
        self.expected = ResponseEntity(status_code=200)

        return self

    def with_path_params(self, **path_params) -> Self:
        """Adds params which should be inserted into path's placeholders.
        Appends/overwrites defaults params if defined for request.

        Args:
            **path_params - param's placeholder names and values.

        Returns:
            Self: instance of class `ApiRequestHelper`

        Raises:
            RuntimeError: request path is not defined yet.

        Example:

        > req.by_path('random/images/{amount}').with_path_params(amount=10)
         # Path: 'random/images/10'
        """
        self.__check_request_initialized()

        if self.request.path_params is None:
            self.request.path_params = {}

        for par, value in path_params.items():
            if value is None:
                del self.request.path_params[par]
            else:
                self.request.path_params[par] = value

        return self

    def with_query_params(self, **query_params) -> Self:
        """Adds params which should be added as URL query params.
        Appends/overwrites defaults params if defined for request.

        Args:
            **query_params - params names and values.

        Returns:
            Self: instance of class `ApiRequestHelper`

        Example:

        > req.by_path('random/images').with_params(amount=10)
         # Path: 'random/images?amount=10'
        """
        self.__check_request_initialized()

        print(query_params)
        if self.request.query_params is None:
            self.request.query_params = {}

        for par, value in query_params.items():
            if value is None:
                del self.request.query_params[par]
            else:
                self.request.query_params[par] = value

        return self

    def with_headers(self, headers: dict, overwrite: bool = False) -> Self:
        """Adds headers to request.
        If headers already defined (e.g. pre-configured request or set via method)
        new headers will be added to existing list. Use 'overwrite' = True to
        replace headers completely.

        Args:
            headers (dict): headers key-value pairs.
            overwrite (bool, optional): If flag is set to False - adds given headers
            to current request's headers, otherwise - overwrites headers. Defaults to False.

        Returns:
            Self: instance of class `ApiRequestHelper`
        """
        self.__check_request_initialized()

        if self.request.headers is None or overwrite:
            self.request.headers = headers
        else:
            self.request.headers.update(headers)

        return self

    def with_cookies(self, cookies: dict, overwrite: bool = False) -> Self:
        """Adds cookies to request.
        If cookies already defined (e.g. pre-configured request or set via method)
        new cookies will be added to existing list. Use 'overwrite' = True to
        replace cookies completely.

        Args:
            cookies (dict): cookies key-value pairs.
            overwrite (bool, optional): If flag is set to False - adds given cookies
            to current request's cookies, otherwise - overwrites cookies. Defaults to False.

        Returns:
            Self: instance of class `ApiRequestHelper`
        """
        self.__check_request_initialized()

        if overwrite or self.request.cookies is None:
            self.request.cookies = cookies
        else:
            self.request.cookies.update(cookies)

        return self

    def with_json_payload(self, payload: JsonContent|list|dict) -> Self:
        """Adds JSON payload to request.

        Args:
            payload (JsonContent | list | dict): JSON content.

        Returns:
            Self: instance of `ApiRequestHelper` class
        """
        self.request.json = payload.get() if isinstance(payload, JsonContent) else payload
        return self

    def with_expected(self, status_code: int = None,
                    schema: dict = None,
                    headers: JsonContent|dict = None,
                    json: JsonContent|dict|list = None) -> Self:
        """Sets expected response data.

        Args:
            status_code (int, optional): expected status code. Defaults to None.
            schema (dict, optional): expected JSON schema. Defaults to None.
            headers (JsonContent | dict, optional): expected headers. Defaults to None.
            json (JsonContent | dict | list, optional): expected JSON content. Defaults to None.

        Returns:
            Self: instance of `ApiRequestHelper` class
        """
        if status_code:
            self.expected.status_code = status_code
        if headers:
            self.expected.headers = headers
        if json:
            self.expected.json = json
        if schema:
            self.expected.schema = schema

        return self

    def check_for_missing_path_params(self) -> bool:
        """Checks that given params fullfill all placeholders in given path.
        Missing or extra parameters will raise an exception.

        Raises:
            KeyError: Missing path parameter.
            ValueError: Extra path parameters given.
        """

        expected_path_params = set(self.PATH_PATTERN.findall(self.request.path))
        params_set = set(self.request.path_params) if self.request.path_params else set()
        error_note = 'Error occured on attempting to perpare ' \
                        f'request {self.request} to "{self.api_client.name}" API.'
        missing = expected_path_params - params_set
        if missing:
            err = KeyError(f'Missing path parameter(s): {", ".join(missing)}.')
            err.add_note(error_note)
            raise err

        extra = params_set - expected_path_params
        if extra:
            err = ValueError(
                f'Extra path parameter(s) provided, but never used: {", ".join(extra)}.'
            )
            err.add_note(error_note)
            raise err

        return True

    def prepare_request_params(self, request_args: dict|None) -> dict:
        """Prepares parameters for actual API requests and return it as dict
        of param-value pairs.

        Args:
            **request_args: key-values pairs for `requests.request` method
            (headers, cookies, json, etc.)

        Raises:
            RuntimeError: Path is not defined for request.
            KeyError: Missing path parameter.
            ValueError: Extra path parameters given.

        Returns:
            Self: dict
        """
        self.__check_request_initialized()

        self.check_for_missing_path_params()

        request_args['path'] = self.request.path.format(**self.request.path_params) \
                                if self.request.path_params else \
                                self.request.path

        request_args['method'] = self.request.method
        request_args['params'] = self.request.query_params
        request_args['json'] = self.request.json

        # Ensure that given args will be appended to current requests settings
        request_args['headers'] = self.request.headers | request_args.get('headers', {}) \
                                    if self.request.headers else \
                                    request_args.get('headers')

        request_args['cookies'] = self.request.cookies | request_args.get('cookies', {}) \
                                    if self.request.cookies else \
                                    request_args.get('cookies')

        request_args['auth'] = (request_args['auth']
                                if request_args.get('auth') else
                                self.request.auth)

        return request_args

    def perform(self, override_defaults: bool = False, **request_args) -> ApiResponseHelper:
        """Performs HTTP request with given request parameters (headers, cookies, auth, etc.),
        creates and retuns `api_helpers.response_helper.ResponseHelper` with response (also
        verifies response status code).

        Request will be made composing 4 sources of parameter values by priority:
        1. parameters defined as kwargs of .perform() method
        2. parameters defined by .with_X() methods
        3. parameters defined in request catalog (e.g. requests.json)
        4. parameters defined in API Client configuration (e.g. api_config.ini)

        Composing is made on per-value basis, meaning that if some header "a" from request catalog
        is not overwritten by .with_headers() or .perform(..., headers={...}) methods - it will be
        passed to the actual request.

        In order to overwrite:
        - request catalog values use .with_headers/cookies(..., overwrite=True) - this will replace
        headers/cookies on request level completely;
        - API Client's default values use 'override_defaults=True' args of .perform(). However not
        specified parameters will be set to client's defaults anyway (so one need to manually set
        parameters to overwrite - e.g. .perform(..., override_defaults=True, headers={}) will ignore
        API Client's default headers, but add auth/cookies params)!

        Args:
            override_defaults (bool, optional): Flag to override API Client's default parameters
            for response - 'headers', 'cookies', 'timeout', 'auth'. Defaults to False.
            **request_args: key-values pairs of `requests.request` method
            (headers, cookies, json, etc.)

        Raises:
            RuntimeError: Path is not defined for request.
            KeyError: Missing path parameter.
            ValueError: Extra path parameters given.

        Returns:
            Self: instance of class `ApiRequestHelper`
        """
        args = self.prepare_request_params(request_args)
        self.__allure_save_request_params(args)

        request_step_info = f' "{self.name}"' if self.name else ''
        with allure.step(f'Request {self.count}{request_step_info} '
                         f'[method: {self.request.method}, url: {self.request.path}]'):

            response = self.api_client.request(
                override_defaults=override_defaults,
                **args
            )

            allure.dynamic.parameter(f'Request {self.count} completed', response.url)
            self.count += 1

        return ApiResponseHelper(response).set_expected(**asdict(self.expected))\
                                          .status_code_equals()

    # Private methods
    def __check_request_initialized(self) -> None:
        """Checks that request path was already initialized.

        Raises:
            RuntimeError: Request is not initialized.
        """
        if self.request and self.request.path is not None:
            return

        raise RuntimeError('Request is not initialized. '
            'Make sure to use .by_path() or .by_name() method first!')

    def __allure_save_request_params(self, request_args: dict) -> None:
        """Saves request data as Allure parameters.

        Args:
            path (str): request URI.
            request_args (dict): request parameters.
        """
        request_name = f'(pre-configured, "{self.name}")'if self.name else ''
        param_name = f'Request {self.count}{request_name}'
        param_value = {
            'method': request_args['method'],
            'path': request_args['path'],
            'query': request_args.get('query_params', ''),
            'params': {k:v for k,v in request_args.items()
                       if v is not None and k not in ('method', 'path', 'query_params')}
        }

        allure.dynamic.parameter(param_name, param_value)

        if self.request.json is not None:
            allure.dynamic.parameter(f'Request {self.count} - JSON payload', self.request.json)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(Client: {self.api_client.name})'
