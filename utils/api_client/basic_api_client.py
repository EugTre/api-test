"""Basic API Client wrapper"""
import logging
from logging import ERROR, INFO
from abc import ABC, abstractmethod

import requests
from utils.api_client.models import HTTPMethod, ApiClientSpecification, RequestCatalogEntity

DEFAULT_TIMEOUT = 60


class AbstractApiClient(ABC):
    """Abstract class for API Client"""
    @abstractmethod
    def __init__(self, api_spec_as_dict: dict):
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
    """
    instnace_count = 0   # TODO: Remove debug info

    def __init__(self, api_spec_as_dict: dict):
        """Creates an instance of `BasicApiClient` class.

        Args:
            api_spec_as_dict (dict): api client parameters as dict.
            Dict keys and values:
            - base_url (str): base URL of API.
            - endpoint (str, optional): API's endpoint.
            - name (str, optional): API name.
            - logger_name (str, optional): logger name to use for reqeust/response
            logging.
            - request_defaults (dict, optional): settings to apply for each request -
            headers, cookies, auth and timeout (each optional).
            - request_catalog (dict, optional): catalog of API requests.
        """
        self.base_url = api_spec_as_dict['base_url'].rstrip(r'/')
        self.endpoint = api_spec_as_dict['endpoint'].strip(r'/')

        self.request_catalog = api_spec_as_dict.get('request_catalog', None)
        self.request_defaults = api_spec_as_dict.get('request_defaults', {})

        self.logger = None
        if api_spec_as_dict.get('logger_name') is not None:
            self.logger = logging.getLogger(api_spec_as_dict['logger_name'])

        self.name = api_spec_as_dict.get('name', f'Client for {self.get_api_url()} API')

        # Apply defaults
        if not self.request_defaults.get('timeout'):
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
        if isinstance(method, HTTPMethod):
            method = method.value

        request_params = self.prepare_request_params(method, path,
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
        return self.compose_url('')

    def get_from_catalog(self, name: str) -> RequestCatalogEntity:
        """Selects and return 'RequestCatalogEntity' by given name.

        Args:
            name (str): name of the request entity

        Returns:
            RequestCatalogEntity: instance of `RequestCatalogEntity`
        """
        if not self.request_catalog or name not in self.request_catalog:
            return None

        return self.request_catalog[name]

    def compose_url(self, path: str) -> str:
        """Composes URL by mergin Base URL, enpoint and given path.
        Strips unneccessary `/` symbols inbetween.

        Args:
            path (str): URI path.

        Returns:
            str: absoulte URL.
        """
        url_path = [self.base_url]
        if self.endpoint:
            url_path.append(self.endpoint)
        if path:
            url_path.append(path.strip(r'/'))
        return '/'.join(url_path)

    def prepare_request_params(self, method: str, path: str,
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
        request_params = {
            'method': method.lower(),
            'url': self.compose_url(path),
            **params
        }

        # If param is set and no override required - combine request
        # values with defaults.
        # If param is not set in request - apply default.
        # So to override Client's defaults - one should just set 'header'/'cookies'
        # with any value.
        for param in ('headers', 'cookies'):
            default = self.request_defaults.get(param)

            if param in request_params:
                if not override_defaults:
                    req_value = request_params.get(param, {})
                    self._combine_values(req_value, default)
                    request_params[param] = req_value
            else:
                request_params[param] = default

        # Auth param will be set to defaults if not set in request, but never overwritten
        if not 'auth' in request_params:
            request_params['auth'] = self.request_defaults.get('auth')

        if not 'timeout' in request_params:
            request_params['timeout'] = self.request_defaults.get('timeout')

        return request_params

    def _combine_values(self, request_value: dict, default_value: dict) -> None:
        """Safely merges 2 dictionaries (without overriding 'request_value').
        Used to apply config level params to request.

        Args:
            request_value (dict): Request data.
            config_value (dict): Config-level values
        """
        # Default value is None - ignore and return
        if not default_value:
            return

        # If request has empty dict - just merge both
        if not request_value:
            request_value.update(default_value)
            return

        # Othwerwise - add missing defaults to request param
        for key, value in default_value.items():
            if key not in request_value:
                request_value[key] = value

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
