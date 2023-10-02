"""Basic API Client wrapper"""
import os
import uuid
import logging
from logging import ERROR, INFO, DEBUG
from abc import ABC, abstractmethod

import requests
from .models import HTTPMethod, ApiClientIdentificator, RequestCatalogEntity, \
    ApiRequestLogEventType, ApiLogEntity

DEFAULT_TIMEOUT = 30


class BaseApiClient(ABC):
    """Abstract class for API Client"""
    def __init__(self, api_spec_as_dict: dict):
        """Init required fields"""
        self.base_url = api_spec_as_dict['base_url'].rstrip(r'/')
        self.endpoint = api_spec_as_dict['endpoint'].strip(r'/')

        self.request_catalog = api_spec_as_dict.get('request_catalog', None)
        self.request_defaults = api_spec_as_dict.get('request_defaults', {})
        if not self.request_defaults.get('timeout'):
            self.request_defaults['timeout'] = DEFAULT_TIMEOUT

        name = api_spec_as_dict.get('name', self.get_api_url())
        self.client_id = ApiClientIdentificator(
            instance_id=f"{name}"
            f"_{os.getenv('PYTEST_XDIST_WORKER', 'master')}"
            f"_{os.getenv('PYTEST_XDIST_TESTRUNUID', uuid.uuid4().hex)}",
            api_name=name,
            url=self.get_api_url()
        )
        self.request_count = 0

        self.logger = None
        if api_spec_as_dict.get('logger_name') is not None:
            self.logger = logging.getLogger(api_spec_as_dict['logger_name'])

    @abstractmethod
    def request(self, method, path, override_defaults, **kwargs):
        """Makes HTTP request, wrapping actual lib request fucntion call"""

    def get_api_url(self):
        """Return fully qualified API url (url + endpoint)"""
        return self.compose_url('')

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

    def get_from_catalog(self, name: str) -> RequestCatalogEntity:
        """Get `RequestCatalogEntity` from api's client request catalog by
        given name.

        Args:
            name (str): name of the request entity

        Returns:
            RequestCatalogEntity: instance of `RequestCatalogEntity`
        """
        if not self.request_catalog or name not in self.request_catalog:
            return None

        return self.request_catalog[name]

    def log_request(self, request_params):
        """Logs prepared request data.
        By default"""
        if not self.logger:
            return

        self.logger.log(
            INFO,
            msg=f"Going to sent '{request_params['method']}' "
                f"request (#{self.request_count}) to {request_params['url']}",
            extra=ApiLogEntity(
                event_type=ApiRequestLogEventType.PREPARED,
                request_id=self.request_count,
                client_id=self.client_id,
                request_params=request_params,
            )
        )

    def log_response(self, response):
        """Logs response data of the successful request"""
        if not self.logger:
            return

        request_str = self.request_object_to_str(response.request)
        response_str = self.response_object_to_str(response)
        self.logger.log(
            INFO,
            msg=f"Request (#{self.request_count}) "
                f"'{response.request.method}' to "
                f"{response.request.url} completed successfully.",
            extra=ApiLogEntity(
                event_type=ApiRequestLogEventType.SUCCESS,
                request_id=self.request_count,
                client_id=self.client_id,
                request=request_str,
                response=response_str
            )
        )
        self.logger.log(DEBUG, "Request: %s", request_str)
        self.logger.log(DEBUG, "Response: %s", response_str)

    def log_error(self, exc, response):
        """Logs error info of the unsuccessful request (exception raised)"""
        if not self.logger:
            return

        self.logger.log(
            ERROR,
            msg=f"Request (#{self.request_count}) failed: {exc}",
            exc_info=True,
            extra=ApiLogEntity(
                event_type=ApiRequestLogEventType.ERROR,
                request_id=self.request_count,
                client_id=self.client_id,
                request=self.request_object_to_str(response.request),
                response=self.response_object_to_str(response)
            )
        )

    def __repr__(self):
        return f"<{self.__class__.__name__}" \
            f"(id='{self.client_id.instance_id}', " \
            f"url='{self.client_id.url}')>"

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
            'cookies':
                request.headers["Cookie"]
                if "Cookie" in request.headers
                else {},
            'body': request.body
        }
        return str(fields)

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


class SimpleApiClient(BaseApiClient):
    """Basic API Client class and base class for inheritence.
    Wraps `requests` module with little custom logic and logging of
    request & response.
    """
    def request(self, method: str | HTTPMethod,
                path: str,
                override_defaults: bool = False,
                **params) -> requests.Response | None:
        """Performs request with given method and paramerters to given
        path of API.
        Send request and response data to logger.

        Each request will be extended with defaults parameters (headers,
        cookies, auth, timeout) from config file (e.g. api_config.ini).
        If 'override_defaults' flag set to True - only missing parameters
        will be set to defaults (e.g. if 'override_defaults' is True,
        default headers is set and request invoked with headers - only
        passed headers will be used)

        Args:
            method (str or `HTTPMethod` enum): method to make a request ('get',
            'post', etc.)
            path (str): path relative to API base url (e.g. 'v1/check')
            override_defaults(bool): flag to override default values
            of API Client. If True - values passed in **params will override
            API Client's defaults. However for params that
            not passed - defaults will still apply.
            params(): additional keyword arguments for request.

        Returns:
            `requests.Response:`: :class:`Response <Response>` object
        """
        if isinstance(method, HTTPMethod):
            method = method.value

        request_params = self.prepare_request_params(
            method, path, override_defaults, **params
        )

        self.log_request(request_params)
        response = None
        try:
            response = requests.request(**request_params)
        except Exception as exc:
            self.log_error(exc, response)
            raise

        self.log_response(response)
        self.request_count += 1

        return response

    def prepare_request_params(self, method: str, path: str,
                               override_defaults: bool, **params) -> dict:
        """Compose request parameters into a dictionary.
        Sets defaults to `timeout` parameter if missign to
        `self.default_timeout`.

        Args:
            method (str): method name ('get', 'post', etc.).
            path (str): path relative to API base url (e.g. 'v1/check').
            override_defaults (bool): flag to override params if given;
            if True - given params will be used as is; otherwise given
            params will be appended/set with values from request_defaults.

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
        # So to override Client's defaults - one should just
        # set header/cookies with any value.
        for param in ('headers', 'cookies'):
            default = self.request_defaults.get(param)

            if param in request_params:
                if not override_defaults:
                    req_value = request_params.get(param, {})
                    self._combine_values(req_value, default)
                    request_params[param] = req_value
            else:
                request_params[param] = default

        # Auth param will be set to defaults if not set in request,
        # but never overwritten
        if 'auth' not in request_params:
            request_params['auth'] = self.request_defaults.get('auth')

        if 'timeout' not in request_params:
            request_params['timeout'] = self.request_defaults.get('timeout')

        return request_params

    def _combine_values(self, request_value: dict, default_value: dict
                        ) -> None:
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
