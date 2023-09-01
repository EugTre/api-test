"""Models of framework data related to API Client"""
from dataclasses import dataclass
from enum import Enum

@dataclass(slots=True)
class ApiConfiguration:
    """Model for API configuration from
       `--api-config` command-line argument
    """
    url: str
    endpoint: str = ''
    client: str = 'utils.api_client.basic_api_client.BasicApiClient'
    logger: str = None
    timeout: str|int = None
    requests: str|dict = None
    auth: str|tuple = None
    headers: str|dict = None
    cookies: str|dict = None
    name: str = ''

@dataclass(slots=True)
class ApiClientsSpecificationCollection:
    """Collection of API Clients configurations"""
    source_file: str
    configs: dict

@dataclass(slots=True)
class ApiClientSpecification:
    """Model to store values needed for API Client creation"""
    name: str
    base_url: str
    endpoint: str
    request_defaults: dict|None
    request_catalog: dict|None
    logger_name: str|None
    client_class: str

    def __init__(self, api_config: ApiConfiguration, req_catalog: dict|None = None):
        self.base_url = api_config.url
        self.endpoint = api_config.endpoint
        self.client_class = api_config.client
        self.logger_name = api_config.logger
        self.name = api_config.name
        self.request_defaults = {
            'timeout': api_config.timeout,
            'headers': api_config.headers,
            'cookies': api_config.cookies,
            'auth': tuple(api_config.auth) if api_config.auth else api_config.auth
        }
        self.request_catalog = req_catalog if req_catalog is not None else None

    def as_dict(self) -> dict:
        """Exports object properties as dictionary.
        Excludes 'client' property that is not used in BaseApiClient initialization.

        Returns:
            dict: Api specification as dictionary, excludint 'client' property.
        """
        return {
            "name": self.name,
            "base_url": self.base_url,
            "endpoint": self.endpoint,
            "logger_name": self.logger_name,
            "request_defaults": self.request_defaults,
            "request_catalog": self.request_catalog
        }

@dataclass(slots=True)
class RequestEntity:
    """Model for API request"""
    method: str
    path: str
    headers: dict = None
    query_params: dict = None
    path_params: dict = None
    cookies: dict = None
    auth: tuple = None
    json: dict|list = None
    timeout: int = None

@dataclass(frozen=True, slots=True)
class ResponseEntity:
    """Model for  API response"""
    status_code: int
    schema: dict = None
    json: dict|list = None
    headers: dict = None

@dataclass(frozen=True, slots=True)
class RequestCatalogEntity:
    """Model for API Request catalogue dictionary value"""
    name: str
    request: RequestEntity
    response: ResponseEntity

class HTTPMethod(Enum):
    """Enumerations of supported HTTP methods"""
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    PATCH = 'patch'
    DELETE = 'delete'
