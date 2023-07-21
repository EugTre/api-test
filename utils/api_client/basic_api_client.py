"""Basic API Client wrapper"""
import logging
from logging import ERROR, INFO
from enum import Enum

import requests

DEFAULT_TIMEOUT = 240

class HTTPMethod(Enum):
    """Enumerations of supported HTTP methods"""
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    PATCH = 'patch'
    DELETE = 'delete'


class BasicApiClient():
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

        self.request_made = 0

        self._log(INFO, f'BasicApiClient {self.instance_id} was created!!!')
        self._log(INFO, self)

    def get(self, path: str='/', **kwargs) -> requests.Response:
        """Makes GET request with given params.

        Args:
            `path` (str, optional): specific URL sub-path. Defaults to '/';
            `**kwargs`: other request params, see parameters for `requests.api.request()`.
        """
        return self.request(
            method=HTTPMethod.GET,
            path=path,
            **kwargs
        )

    def post(self, path: str = '/', data: dict = None, json=None, **kwargs) -> requests.Response:
        """Makes POST request with given params.

        Args:
            `path` (str, optional): specific URL sub-path. Defaults to '/'.
            `data` (dict, optional): Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            `json` (optional): A JSON serializable Python object to send in the body
                of the :class:`Request`.
            `**kwargs` (optional): other request params, see parameters for
            `requests.api.request()`.
        """
        return self.request(
            method=HTTPMethod.POST,
            path=path,
            data=data, json=json, **kwargs
        )

    def put(self, path: str = '/', data: dict = None, **kwargs) -> requests.Response:
        """Makes PUT request with given params.

        Args:
            `path` (str, optional): specific URL sub-path. Defaults to '/'.
            `data` (dict, optional): Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            `**kwargs` (optional): other request params, see parameters for
            `requests.api.request()`.
        """
        return self.request(
            method=HTTPMethod.PUT,
            path=path,
            data=data, **kwargs
        )

    def patch(self, path: str = '/', data: dict = None, **kwargs) -> requests.Response:
        """Makes PATCH request with given params.

        Args:
            `path` (str, optional): specific URL sub-path. Defaults to '/'.
            `data` (dict, optional): Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            `**kwargs` (optional): other request params, see parameters for
            `requests.api.request()`.
        """
        return self.request(
            method=HTTPMethod.PATCH,
            path=path,
            data=data, **kwargs
        )

    def delete(self, path: str = '/', **kwargs) -> requests.Response:
        """Makes DELETE request with given params.

        Args:
            `path` (str, optional): specific URL sub-path. Defaults to '/'.
            `**kwargs` (optional): other request params, see parameters for
            `requests.api.request()`.
        """
        return self.request(
            method=HTTPMethod.DELETE,
            path=path,
             **kwargs
        )

    def request(self, method: str|HTTPMethod, path: str, **params) -> requests.Response:
        """Performs request with given method and paramerters to given path of API.
        Send request and response data to logger.

        Args:
            method (str or `HTTPMethod` enum): method to make a request ('get', 'post', etc.)
            path (str): path relative to API base url (e.g. 'v1/check')

        Returns:
            `requests.Response:`: :class:`Response <Response>` object
        """
        if isinstance(method, HTTPMethod):
            method = method.value

        request_params = self._prepare_request_params(method, path, **params)
        response = None
        try:
            response = requests.request(**request_params)
        except Exception:
            self._log(ERROR, 'Exception', exc_info=True,
                      extra={'request': request_params, 'response': response})
            raise

        self.request_made += 1
        self._log(INFO, f'Request {self.request_made} by {self.instance_id} made {response.url}',
                  extra={'request': request_params, 'response': response})
        return response

    def get_api_url(self) -> str:
        '''Returns API URL - base url + endpoint'''
        return self._compose_url('')

    def _prepare_request_params(self, method: str, path: str, **params) -> dict:
        """Compose request parameters into a dictionary.
        Sets defaults to `timeout` parameter if missign to `self.default_timeout`.

        Args:
            method (str): method name ('get', 'post', etc.).
            path (str): path relative to API base url (e.g. 'v1/check').

        Returns:
            dict: dictionary of the request parameters.
        """
        request_params = {
            'method': method.lower(),
            'url': self._compose_url(path),
            **params
        }

        for param in ('timeout', 'headers', 'cookies', 'auth'):
            if not request_params.get(param):
                request_params[param] = self.request_defaults[param]

        return request_params

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
