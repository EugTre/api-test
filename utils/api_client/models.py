"""Models of framework data related to API Client"""
from dataclasses import dataclass, field

@dataclass
class BasicApiConfiguration:
    """Model for API configuration from
       `--api-config` command-line argument
    """
    url: str
    endpoint: str = ''
    client: str = 'utils.api_client.basic_api_client.BasicApiClient'
    logger: str = ''
    timeout: str|int = None
    requests: str|dict = None
    auth: str|tuple = None
    headers: str|dict = None
    cookies: str|dict = None
    schemas: str|dict = None
    name: str = ''

@dataclass
class RequestEntity:
    """Model for API request"""
    method: str
    path: str
    headers: dict = field(default_factory=dict)
    query_params: dict = field(default_factory=dict)
    path_params: dict = field(default_factory=dict)
    cookies: dict = field(default_factory=dict)
    auth: tuple = None
    timeout: int = None

@dataclass
class ResponseEntity:
    """Model for  API response"""
    status_code: int
    schema_name: str = None
    schema: dict = None

@dataclass
class CatalogEntity:
    """Model for API Request catalogue dictionary value"""
    name: str
    request: RequestEntity
    response: ResponseEntity

@dataclass
class ApiClientsConfigurationCollection:
    """Collection of API Clients configurations"""
    source_file: str
    configs: dict

@dataclass
class ApiSpecification:
    """Model to store values needed for API Client creation"""
    base_url: str
    endpoint: str
    client: str
    logger_name: str
    request_defaults: dict
    request_catalog: dict
    name: str

    def __init__(self, api_config: BasicApiConfiguration, req_catalog: dict):
        self.base_url = api_config.url
        self.endpoint = api_config.endpoint
        self.client = api_config.client
        self.logger_name = api_config.logger
        self.name = api_config.name
        self.request_defaults = {
            'timeout': api_config.timeout,
            'headers': api_config.headers,
            'cookies': api_config.cookies,
            'auth': api_config.auth,
            'schemas': api_config.schemas
        }
        self.request_catalog = req_catalog

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
