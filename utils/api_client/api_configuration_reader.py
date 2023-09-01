"""Read and compose configurations of the API clients
   to be ready for use to create API client"""

import logging

from utils.json_content.json_content import JsonContentBuilder
from utils.api_client.models import ApiConfiguration, \
    ApiClientSpecification, ApiClientsSpecificationCollection, \
    RequestEntity, ResponseEntity, RequestCatalogEntity


class ApiConfigurationReader:
    """Reads configs and creates configurations for every API"""

    def __init__(self, api_base_config_file: str):
        self._config_file = api_base_config_file

    def read_configurations(self) -> ApiClientsSpecificationCollection:
        """Reads and compose configurations from base config file and all nested links.

        Returns:
            ApiClientsConfigurationCollection: collection of API specifications,
            ready-to-use for API Client creation.
        """
        logging.info('Read configuration from "%s".', self._config_file)

        try:
            config_content = JsonContentBuilder() \
                            .from_file(self._config_file) \
                            .use_composer() \
                            .build() \
                            .get()
        except Exception as err:
            err.add_note('Error occured during API Config parsing '
                         f'from "{self._config_file}" file')
            raise

        configs = {
            api_name_key: self.generate_api_specification(api_name_key, api_config_data)
            for api_name_key, api_config_data in config_content.items()
        }

        logging.info("API configurations reading done.")
        return ApiClientsSpecificationCollection(
            source_file=self._config_file,
            configs=configs
        )

    def generate_api_specification(self, api_name: str,
                                   cfg: dict) -> ApiClientSpecification:
        """Reads, pre-validates and compose configuration for specific API from config.

        Args:
            api_name (str): name of the API.
            cfg (dict): configuration of the API client.

        Returns:
            ApiSpecification: ready-to-go configuration of the API client.
        """
        logging.info('Generating API specification for API "%s".', api_name)

        if not cfg.get('url'):
            raise ValueError(f'There is no "url" defined for "{api_name}" API Client '
                             f'in configuration file "{self._config_file}".')

        # Handle error and append some user-friendly message
        try:
            api_cfg = ApiConfiguration(name=api_name, **cfg)
            request_catalog = self.compile_requests_catalog(api_cfg)
        except Exception as err:
            details = '\n'.join(err.__notes__) if getattr(err, '__notes__', None) else ''
            raise ValueError(
                f'Error on composing API Specification for "{api_name}" API client.'
                f'\nException {err.__class__.__name__}: {err}'
                f'\nDetails: {details}'
            ) from err

        logging.debug('API specification for "%s" was created successfully.', api_name)
        return ApiClientSpecification(
            api_config=api_cfg,
            req_catalog=request_catalog
        )

    def compile_requests_catalog(self, api_config: ApiConfiguration) -> dict:
        """Converts JSON data into Request Catalog using model objects
        to validate fields.

        Args:
            api_config (ApiConfiguration): api configuration.

        Returns:
            dict: Compiled request catalog
        """
        if not api_config.requests:
            return None

        logging.info('Composing Request catalog for "%s" of %s request(s).',
                      api_config.name, len(api_config.requests))
        requests_catalog = {}
        for request_name, request_data in api_config.requests.items():
            requests_catalog[request_name] = RequestCatalogEntity(
                request_name,
                RequestEntity(**request_data['request']),
                ResponseEntity(**request_data['response'])
            )

        return requests_catalog
