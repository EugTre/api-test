"""Basic API Client wrapper"""
import logging
from logging import ERROR, INFO
from enum import Enum
from abc import ABC, abstractmethod

import requests
from utils.api_client.models import RequestCatalogEntity

DEFAULT_TIMEOUT = 240

class HTTPMethod(Enum):
    """Enumerations of supported HTTP methods"""
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    PATCH = 'patch'
    DELETE = 'delete'

class AbstractApiClient(ABC):
    """Abstract class for API Client"""
    @abstractmethod
    def __init__(self, base_url, endpoint, name, logger_name,
                 request_defaults, request_catalog):
        """Init required fields"""

    @abstractmethod
    def request(self, method, path, override_defaults, **kwargs):
        """Makes HTTP request, wrapping `requests.request` fucntion call"""

    @abstractmethod
    def get_api_url(self):
        """Return fully qualified API url (url + endpoint)"""

    @abstractmethod
    def get_from_catalog(self, name: str):
        """Get RequestCatalogEntity from api's client request catalog"""


class BasicApiClient(AbstractApiClient):
    """Basic API Client class and base class for inheritence.
    Wraps `requests` module with little custom logic and logging of request & response.

    Args:
        base_url (str): base URL for API;
        endpoint (str, optional): endpoint for API, default - empty;
        default_timeout (int, optional): default timeout for requests, in sceonds, default 240 sec;
        logger_name (str, optional): name of the logger to log requests and responses;
        request_catalog (dict, optional): catalogue of reference requests/response data,
        default - None.
    """
    instnace_count = 0   # TODO: Remove debug info

    def __init__(self,
                 base_url: str,
                 endpoint: str = '',
                 name: str = '',
                 logger_name: str = None,
                 request_defaults: dict = None,
                 request_catalog: dict = None,
        ):
        """Creates an instance of `BasicApiClient` class.

        Args:
            base_url (str): base URL of API.
            endpoint (str, optional): API's endpoint. Defaults to ''.
            name (str, optional): API name. Defaults to ''.
            logger_name (str, optional): logger name to use for reqeust/response
            logging. Defaults to None.
            request_defaults (dict, optional): settings to apply for each request. Defaults to None.
            request_catalog (dict, optional): catalog of API requests. Defaults to None.
        """
        self.base_url = base_url.rstrip(r'/')
        self.endpoint = endpoint.strip(r'/')
        self.request_defaults = request_defaults
        self.logger = logging.getLogger(logger_name) if logger_name else None
        self.request_catalog = request_catalog
        self.name = name
        if not self.name:
            self.name = f'Client for {self.get_api_url()} API'

        if not self.request_defaults['timeout']:
            self.request_defaults['timeout'] = DEFAULT_TIMEOUT

        # TODO: Remove debug info
        self.instance_id = BasicApiClient.instnace_count
        BasicApiClient.instnace_count += 1

        self.request_count = 0

        self._log(INFO, f'BasicApiClient {self.instance_id} was created!!!')
        self._log(INFO, self)

    def request(self, method: str|HTTPMethod,
                path: str,
                override_defaults: bool = False,
                **params) -> requests.Response:
        """Performs request with given method and paramerters to given path of API.
        Send request and response data to logger.

        Each request will be extended with defaults parameters (headers, cookies, auth, timeout)
        from config file (e.g. api_config.ini). If 'override_defaults' flag set to True - only
        missing parameters will be set to defaults (e.g. if 'override_defaults' is True,
        default headers is set and request invoked with headers - only passed headers will be used)

        Args:
            method (str or `HTTPMethod` enum): method to make a request ('get', 'post', etc.)
            path (str): path relative to API base url (e.g. 'v1/check')
            override_defaults(bool): flag to override default values of API Client. If True -
            values passed in **params will override API Client's defaults. However for params
            that not passed - defaults will still apply.
            params(): additional keyword arguments for request.

        Returns:
            `requests.Response:`: :class:`Response <Response>` object
        """
        print(method)
        print(path)
        print(override_defaults)
        print(params)

        if isinstance(method, HTTPMethod):
            method = method.value

        request_params = self._prepare_request_params(method, path,
                                                      override_defaults,
                                                      **params)
        response = None
        try:
            response = requests.request(**request_params)
        except Exception:
            self._log(ERROR, 'Exception', exc_info=True,
                      extra={'request': request_params, 'response': response})
            raise

        self.request_count += 1
        self._log(INFO, f'Request {self.request_count} by {self.instance_id} made {response.url}',
                  extra={'request': request_params, 'response': response})
        return response

    def get_api_url(self) -> str:
        '''Returns API URL - base url + endpoint'''
        return self._compose_url('')

    def get_from_catalog(self, name: str) -> RequestCatalogEntity:
        """Selects and return 'RequestCatalogEntity' by given name.

        Args:
            name (str): name of the request entity

        Returns:
            RequestCatalogEntity: instance of `RequestCatalogEntity`
        """
        if name not in self.request_catalog:
            return None

        return self.request_catalog[name]

    def _prepare_request_params(self, method: str, path: str,
                                override_defaults: bool, **params) -> dict:
        """Compose request parameters into a dictionary.
        Sets defaults to `timeout` parameter if missign to `self.default_timeout`.

        Args:
            method (str): method name ('get', 'post', etc.).
            path (str): path relative to API base url (e.g. 'v1/check').
            override_defaults (bool): flag to override params if given; if True -
            given params will be used as is; otherwise given params will be
            appended/set with values from request_defaults.

        Returns:
            dict: dictionary of the request parameters.
        """

        print('_prepare_request_params:')
        print(params)

        request_params = {
            'method': method.lower(),
            'url': self._compose_url(path),
            **params
        }

        print('\n')
        print(request_params)

        # If param is set and no override required - combine request
        # values with defaults.
        # If param is not set in request - apply default.
        # So to override Client's defaults - one should just set 'header'/'cookies'
        # with any value.
        for param in ('headers', 'cookies'):
            default = self.request_defaults[param]
            print(f'"{param}" defaults are {default}')

            if param in request_params:
                print(f'"{param}" defined in request. Override flag set to "{override_defaults}".')

                if not override_defaults:
                    print(f'"{param}" will be extended with defaults".')

                    req_value = request_params.get(param, {})
                    self._combine_values(req_value, default)
                    request_params[param] = req_value

            else:
                print(f'"{param}" is not defined in request. Apply defaults".')

                request_params[param] = default

        # Auth param will be set to defaults if not set in request, but never overwritten
        if not 'auth' in request_params:
            request_params['auth'] = self.request_defaults['auth']

        if not 'timeout' in request_params:
            request_params['timeout'] = self.request_defaults['timeout']

        return request_params

    def _combine_values(self, request_value: dict, default_value: dict) -> None:
        """Safely merges 2 dictionaries (without overriding 'request_value').
        Used to apply config level params to request.

        Args:
            request_value (dict): Request data.
            config_value (dict): Config-level values
        """

        # If request has empty dict - just merge both
        if not request_value:
            request_value.update(default_value)
            return

        # Othwerwise - add missing defaults to request param
        for key, value in default_value.items():
            if key not in request_value:
                request_value[key] = value

    def _compose_url(self, path: str) -> str:
        """Composes URL by mergin Base URL, enpoint and given path.
        Strips unneccessary `/` symbols inbetween.

        Args:
            path (str): URI path.

        Returns:
            str: absoulte URL.
        """
        return '/'.join((self.base_url, self.endpoint, path.lstrip(r'/')))

    def _log(self, level: int, msg: str, extra: dict = None, exc_info:bool = False) -> None:
        """Logging request and response data by given logger.

        Args:
            level (int): log level
            msg (str): log message
            extra (dict, optional): extra parameters to log. Defaults to None.
            exc_info (bool, optional): flag to include exception info to log. Defaults to False.
        """
        if not self.logger:
            return
        self.logger.log(level, msg, exc_info=exc_info, extra=extra)
