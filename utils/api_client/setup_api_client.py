"""Creates API client by given API name, using specific configuration
"""
import importlib
import logging

from .models import ApiClientsSpecificationCollection
from .simple_api_client import BaseApiClient


def setup_api_client(
    api_name: str,
    api_clients_configurations: ApiClientsSpecificationCollection
) -> BaseApiClient:
    """Creates and configures API Client object with config file data.

    Args:
        api_name (str): name of the API to search config for
        api_configurations (ApiClientsConfigurationCollection): collection
        of API configurations

    Returns:
        BaseApiClient: object of `BaseApiClient` class
    """
    if api_name not in api_clients_configurations.configs:
        raise ValueError(
            f'There is no config for API "{api_name}" '
            f'in "{api_clients_configurations.source_file}" config file! '
            f'Available: {",".join(api_clients_configurations.configs.keys())}'
        )

    api_spec = api_clients_configurations.configs[api_name]

    module_name, klass_name = api_spec.client_class.rsplit('.', 1)
    client_class_loader = importlib.util.find_spec(module_name)
    if not client_class_loader:
        raise ModuleNotFoundError(
            f'Failed to find API client module named \'{module_name}\' '
            f'for "{api_spec.name}" API.'
        )

    module = importlib.import_module(module_name)
    if not hasattr(module, klass_name):
        raise ModuleNotFoundError(
            f'Failed to find API client class "{klass_name}" in module '
            f'\'{module_name}\' for "{api_spec.name}" API.'
        )
    client_class = getattr(module, klass_name)

    if logging.getLogger().handlers[0].level < logging.INFO:
        logging.debug('')
        logging.debug('-' * 100)
        for line in api_spec.get_repr():
            logging.debug(line)
        if api_spec.request_catalog:
            logging.debug(
                '  Request catalog of %s item(s)',
                len(api_spec.request_catalog)
            )
        else:
            logging.debug('  No Request catalog')
        logging.debug('-' * 100)

    return client_class(api_spec.as_dict())
