"""Basic API Client wrapper"""
import os
import uuid
import logging
from logging import ERROR, INFO
from abc import ABC, abstractmethod
from enum import Enum

import requests
from .models import HTTPMethod, RequestCatalogEntity

DEFAULT_TIMEOUT = 60

class RequestLogEventType(Enum):
    """Type of log event from Api Client"""
    PREPARED = 0
    SUCCESS = 1
    ERROR = -1


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

    @staticmethod
    def response_object_to_str(response: requests.Response) -> str:
        """Converts response object to dict of parameters

        Args:
            response (requests.Response): response object to convert.

        Returns:
            str: response object data as string.
        """
        if response is None:
            return None

        fields = {
            'status_code': response.status_code,
            'reason': response.reason,
            'headers': response.headers,
            'cookies': response.cookies.get_dict(),
            'latency_ms': response.elapsed.microseconds / 1000,
            'history': response.history,
            'encoding': response.encoding,
            'raw_content': response.content,
            'text': response.text,
            'is_redirect': response.is_redirect
        }

        return str(fields)

    @staticmethod
    def request_object_to_str(request: requests.PreparedRequest):
        """Converts request object to dict of parameters

        Args:
            request (requests.Response): request object to convert.

        Returns:
            str: request object data as string.
        """
        if request is None:
            return None

        fields = {
            'method': request.method,
            'url': request.url,
            'headers': request.headers,
            'cookies': request.headers["Cookie"].get_dict()
                        if "Cookie" in request.headers
                        else {},
            'body': request.body
        }
        return str(fields)


class BasicApiClient(AbstractApiClient):
    """Basic API Client class and base class for inheritence.
    Wraps `requests` module with little custom logic and logging of request & response.
    """
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
        if not self.request_defaults.get('timeout'):
            self.request_defaults['timeout'] = DEFAULT_TIMEOUT

        self.name = api_spec_as_dict.get('name', f'{self.get_api_url()} API Client')
        self.client_id = {
            'id': f"{self.name}"\
                f"_{os.getenv('PYTEST_XDIST_WORKER', 'master')}" \
                f"_{os.getenv('PYTEST_XDIST_TESTRUNUID', uuid.uuid4().hex)}",
            'api': self.name,
            'url': self.get_api_url()
        }
        self.request_count = 0

        self.logger = None
        if api_spec_as_dict.get('logger_name') is not None:
            self.logger = logging.getLogger(api_spec_as_dict['logger_name'])

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

        self._log_request(request_params)
        response = None
        try:
            response = requests.request(**request_params)
        except Exception:
            self._log_error(response)
            raise

        self._log_response(response)
        self.request_count += 1

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

    def _log_request(self, request_params):
        """Logs prepared request data"""
        if not self.logger:
            return

        self.logger.log(INFO, msg="", extra={
            'event_type': 0,
            'request_id': self.request_count,
            'request_params': request_params,
            'client_id': self.client_id
        })

    def _log_response(self, response):
        """Logs response data of the successful request"""
        if not self.logger:
            return

        self.logger.log(INFO, msg="", extra={
            'event_type': 1,
            'request_id': self.request_count,
            'request': self.request_object_to_str(response.request),
            'response': self.response_object_to_str(response),
            'client_id': self.client_id
        })

    def _log_error(self, response):
        """Logs error info of the unsuccessful request (exception raised)"""
        if not self.logger:
            return

        self.logger.log(
            ERROR,
            msg="",
            exc_info=True,
            extra={
                'event_type': -1,
                'request_id': self.request_count,
                'request': self.request_object_to_str(response.request) if response else None,
                'response': self.response_object_to_str(response),
                'client_id': self.client_id
            }
        )
