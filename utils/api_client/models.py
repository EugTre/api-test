"""Models of framework data related to API Client"""
from dataclasses import dataclass, fields as dataclass_fields
from enum import Enum, StrEnum, auto
from typing import Any


class HTTPMethod(StrEnum):
    """Enumerations of supported HTTP methods"""
    GET = auto()
    POST = auto()
    PUT = auto()
    PATCH = auto()
    DELETE = auto()
    OPTIONS = auto()
    HEAD = auto()

    def __repr__(self):
        return self.value.upper()


class ApiRequestLogEventType(Enum):
    """Type of log event from Api Client"""
    PREPARED = 0
    SUCCESS = 1
    ERROR = -1


# --- Configurations ---
@dataclass(slots=True)
class ApiConfiguration:
    """Model for API configuration from
       `--api-config` command-line argument
    """
    url: str
    endpoint: str = ''
    client: str = 'utils.api_client.simple_api_client.SimpleApiClient'
    logger: str = None
    timeout: str | int = None
    requests: str | dict = None
    auth: str | tuple = None
    headers: str | dict = None
    cookies: str | dict = None
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
    request_defaults: dict | None
    request_catalog: dict | None
    logger_name: str | None
    client_class: str

    def __init__(self, api_config: ApiConfiguration,
                 req_catalog: dict | None = None):
        self.base_url = api_config.url
        self.endpoint = api_config.endpoint
        self.client_class = api_config.client
        self.logger_name = api_config.logger
        self.name = api_config.name
        self.request_defaults = {
            'timeout': api_config.timeout,
            'headers': api_config.headers,
            'cookies': api_config.cookies,
            'auth':
                tuple(api_config.auth)
                if api_config.auth else
                api_config.auth
        }
        self.request_catalog = req_catalog if req_catalog is not None else None

    def as_dict(self) -> dict:
        """Exports object properties as dictionary.
        Excludes 'client' property that is not used in BaseApiClient
        initialization.

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

    def get_repr(self, include_catalog: bool = False) -> list[str]:
        """Returns object representation as list of strings."""
        ignore = ["request_catalog"]

        output = ['Specification:']
        for field in dataclass_fields(self):
            if field.name in ignore:
                continue
            output.append(
                f'  {field.name}: {getattr(self, field.name)}'
            )

        if not include_catalog:
            return output

        output.append('Request catalog:')
        for val in self.request_catalog.values():
            output.append(f'  {val.name}:')
            for line in val.request.get_repr():
                output.append(f'    {line}')
            for line in val.response.get_repr():
                output.append(f'    {line}')

        return output


# --- Request catalog ---
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
    json: dict | list | None = None
    text: str | None = None
    timeout: int = None

    def get_repr(self) -> list[str]:
        """Returns instance representation as list of strings"""
        output = ['Request:']
        for field in dataclass_fields(self):
            output.append(
                f'  {field.name}: {getattr(self, field.name)}'
            )
        return output


@dataclass(slots=True)
class ResponseEntity:
    """Model for  API response"""
    status_code: int
    schema: dict = None
    json: dict | list = None
    text: str | None = None
    headers: dict = None

    def get_repr(self) -> list[str]:
        """Returns instance representation as list of strings"""
        output = ['Response (expected):']
        for field in dataclass_fields(self):
            output.append(
                f'  {field.name}: {getattr(self, field.name)}'
            )
        return output


@dataclass(frozen=True, slots=True)
class RequestCatalogEntity:
    """Model for API Request catalogue dictionary value"""
    name: str
    request: RequestEntity
    response: ResponseEntity


# --- BaseApiClient entities ---
@dataclass(slots=True)
class IterableDataclass:
    """Dataclass with dict interface"""
    def __iter__(self):
        for field in dataclass_fields(self):
            yield field.name

    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)


@dataclass(slots=True)
class ApiClientIdentificator(IterableDataclass):
    """Contains identifiaction data for specific Api Client instance"""
    instance_id: str
    api_name: str
    url: str


@dataclass(slots=True)
class ApiLogEntity(IterableDataclass):
    """Struct that can be consumed by DatabaseHandler class (logging)"""
    event_type: ApiRequestLogEventType
    request_id: int
    client_id: ApiClientIdentificator
    request_params: dict[str, Any] | None = None
    # request data as string
    request: str | None = None
    # response data as string
    response: str | None = None
