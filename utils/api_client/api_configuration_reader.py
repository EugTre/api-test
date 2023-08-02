"""Read and compose configurations of the API clients
   to be ready for use to create API client"""

import logging

from configparser import ConfigParser

from utils.data_reader import DataReader
from utils.json_content.json_content import JsonContent
from utils.api_client.models import ApiConfiguration, \
    ApiClientSpecification, ApiClientsSpecificationCollection, \
    RequestEntity, ResponseEntity, CatalogEntity


class ApiConfigurationReader:
    """Reads configs and creates configurations for every API"""
    REQUEST_CATALOG_DEFINES_KEY = "/$defs"

    def __init__(self, api_base_config_file: str):
        self._config_file = api_base_config_file

    def read_configurations(self) -> ApiClientsSpecificationCollection:
        """Reads and compose configurations from base config file and all nested links.

        Returns:
            ApiClientsConfigurationCollection: collection of API specifications,
            ready-to-use for API Client creation.
        """
        logging.info('Read configuration from "%s".', self._config_file)
        parser = ConfigParser()
        parser.read(self._config_file)

        configs = {}
        for section_name in parser.sections():
            configs[section_name] = self.generate_api_specification(
                section_name, parser[section_name])

        logging.info("API configurations reading done.")
        return ApiClientsSpecificationCollection(
            source_file=self._config_file,
            configs=configs
        )

    def generate_api_specification(self, api_name: str,
                                   cfg: ConfigParser) -> ApiClientSpecification:
        """Reads and compose configuration for specific API in api-config.ini.

        Args:
            api_name (str): name of the API.
            cfg (ConfigParser): configuration of the API.

        Returns:
            ApiSpecification: ready-to-go configuration of the API client.
        """
        logging.info('Generating API specification for API "%s".', api_name)
        api_cfg = ApiConfiguration(name=api_name, **cfg)

        # Timeout will be str if defined in base config, so we need to conver it
        api_cfg.timeout = DataReader.convert_to_int(api_cfg.timeout)

        # Api config values may be raw json or reference to a file.
        # To get data - string will be analyzed and either converted to json
        # or considered as filepath and json will be read from file.
        try:
            api_cfg.headers = DataReader.parse_json(api_cfg.headers)
            api_cfg.cookies = DataReader.parse_json(api_cfg.cookies)
            api_cfg.auth = DataReader.parse_tuple(api_cfg.auth)
        except BaseException as err:
            details = '\n'.join(err.__notes__) if getattr(err, '__notes__', None) else ''
            raise ValueError(f'Error on reading base configuration for "{api_name}" API Client '
                             f'from "{self._config_file}".'
                             f'\nException {err.__class__.__name__}: {err}'
                             f'\nDetails: {details}') from err

        logging.debug(api_cfg)

        # Data in RequestCatalog (e.g. requests.json) is sorta half-baked and
        # need additional compiling to be ready for use
        try:
            request_catalog = self.compile_requests_catalog(api_cfg)
            logging.info('Request Catalog created successfuly!')
        except Exception as err:
            details = '\n'.join(err.__notes__) if getattr(err, '__notes__', None) else ''
            raise ValueError(f'Error on composing Request Catalog from file '
                            f'"{api_cfg.requests}" for "{api_name}" API client.'
                            f'\nException {err.__class__.__name__}: {err}'
                            f'\nDetails: {details}') from err

        logging.debug('API specification for "%s" was created successfully.', api_name)
        return ApiClientSpecification(api_config=api_cfg,
                                      req_catalog=request_catalog)

    def compile_requests_catalog(self, api_config: ApiConfiguration) -> dict:
        """Compiles requests from catalog (e.g. 'requests.json') into request catalogue
        usable by ApiClient (dict of `api_client.models.CatalogEntity` instances).

        Raw request catalog may contain '$defs' section in root as a collection of defines
        to be referenced from other parts of catalog file.

        Args:
            api_config (ApiConfiguration): api configuration.

        Returns:
            dict: Compiled request catalog
        """

        # Compile all references in catalog
        logging.info('Compiling Request catalog for "%s"', api_config.name)

        json_content = JsonContent(
            from_file=api_config.requests,
            make_copy=False,
            resolve_references=True
        )
        json_content.delete(self.REQUEST_CATALOG_DEFINES_KEY)
        compiled_catalog = json_content.get()

        requests_catalog = {}
        if not compiled_catalog:
            logging.info('Request Catalog creation skipped '
                         '(no "requests" config set or empty catalog).')
            return requests_catalog

        logging.info('Composing Request catalog for "%s" of %s request(s).',
                      api_config.name, len(compiled_catalog))

        for request_name, request_data in compiled_catalog.items():
            requests_catalog[request_name] = CatalogEntity(
                request_name,
                RequestEntity(**request_data['request']),
                ResponseEntity(**request_data['response'])
            )

        return requests_catalog
