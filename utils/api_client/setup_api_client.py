"""Creates API client by given API name, using specific configuration
"""
import importlib

from utils.api_client.models import ApiClientsSpecificationCollection
from utils.api_client.basic_api_client import AbstractApiClient

def setup_api_client(api_name: str,
                     api_clients_configurations: ApiClientsSpecificationCollection
) -> AbstractApiClient:
    """Creates and configures API Client object with config file data.

    Args:
        api_name (str): name of the API to search config for
        api_configurations (ApiClientsConfigurationCollection): collection of API configurations

    Returns:
        BasicApiClient: object of `BasicApiClient` class
    """
    if api_name not in api_clients_configurations.configs:
        raise ValueError(f'There is no config for API "{api_name}" '
                         f'in "{api_clients_configurations.source_file}" config file! '
                         f'Available: {",".join(api_clients_configurations.configs.keys())}')

    api_spec = api_clients_configurations.configs[api_name]

    module_name, klass_name = api_spec.client.rsplit('.', 1)
    client_loader = importlib.util.find_spec(module_name)
    if not client_loader:
        raise ModuleNotFoundError(f'Failed to find API client module named \'{module_name}\' '
                                  f'for "{api_spec.name}" API.')

    module = importlib.import_module(module_name)
    if not hasattr(module, klass_name):
        raise ModuleNotFoundError(f'Failed to find API client class "{klass_name}" in module '
                                  f'\'{module_name}\' for "{api_spec.name}" API.')
    client = getattr(module, klass_name)

    print('-' * 100)
    spec = api_spec.as_dict()
    print('\nAPI Specification:')
    for name in ('name', 'base_url', 'endpoint', 'logger_name'):
        print(f'{name:>15}: {spec[name]}')

    print('\nRequest Defaults:')
    for name in ('headers', 'cookies', 'auth', 'timeout'):
        print(f'{name:>15}: {spec["request_defaults"][name]}')

    print('\nRequest Catalogue:')
    for entity_name, entity in spec['request_catalog'].items():
        print(f'  Entity: {entity_name}')
        print(entity)
    print('-' * 100)

    return client(**api_spec.as_dict())
