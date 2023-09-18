"""Creates API client by given API name, using specific configuration
"""
import importlib
import logging

from .models import ApiClientsSpecificationCollection
from .simple_api_client import BaseApiClient

def setup_api_client(api_name: str,
                     api_clients_configurations: ApiClientsSpecificationCollection
) -> BaseApiClient:
    """Creates and configures API Client object with config file data.

    Args:
        api_name (str): name of the API to search config for
        api_configurations (ApiClientsConfigurationCollection): collection of API configurations

    Returns:
        BaseApiClient: object of `BaseApiClient` class
    """
    if api_name not in api_clients_configurations.configs:
        raise ValueError(f'There is no config for API "{api_name}" '
                         f'in "{api_clients_configurations.source_file}" config file! '
                         f'Available: {",".join(api_clients_configurations.configs.keys())}')

    api_spec = api_clients_configurations.configs[api_name]

    module_name, klass_name = api_spec.client_class.rsplit('.', 1)
    client_class_loader = importlib.util.find_spec(module_name)
    if not client_class_loader:
        raise ModuleNotFoundError(f'Failed to find API client module named \'{module_name}\' '
                                  f'for "{api_spec.name}" API.')

    module = importlib.import_module(module_name)
    if not hasattr(module, klass_name):
        raise ModuleNotFoundError(f'Failed to find API client class "{klass_name}" in module '
                                  f'\'{module_name}\' for "{api_spec.name}" API.')
    client_class = getattr(module, klass_name)

    if logging.getLogger().handlers[0].level < logging.INFO:
        logging.debug('-' * 100)
        spec = api_spec.as_dict()
        logging.debug('API Specification:')
        for name in ('name', 'base_url', 'endpoint', 'logger_name'):
            logging.debug(f'{name:>15}: {spec[name]}')

        logging.debug('\nRequest Defaults:')
        for name in ('headers', 'cookies', 'auth', 'timeout'):
            logging.debug(f'{name:>15}: {spec["request_defaults"][name]}')

        logging.debug('\nRequest Catalogue:')
        if spec['request_catalog'] is None:
            logging.debug(f'{"- Empty -":>15}')
        else:
            for entity_name, entity in spec['request_catalog'].items():
                logging.debug(f'  Entity: {entity_name}')
                logging.debug(entity)
        logging.debug('-' * 100)

    return client_class(api_spec.as_dict())
