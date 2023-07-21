"""Read and compose configurations of the API clients
   to be ready for use to create API client"""

import platform
import os
import json
import logging

from configparser import ConfigParser

from utils.api_client.models import BasicApiConfiguration, ApiSpecification, \
    RequestEntity, ResponseEntity, CatalogEntity, ApiClientsConfigurationCollection

class ApiConfigurationReader:
    """Reads configs and creates configurations for every API"""
    def __init__(self, api_base_config_file: str):
        self.config_file = api_base_config_file

    def read_configurations(self) -> ApiClientsConfigurationCollection:
        """Reads and compose configurations from base config file and all nested links.

        Returns:
            ApiClientsConfigurationCollection: collection of API specifications,
            ready-to-use for API Client creation.
        """
        logging.info('Read configuration from "%s".', self.config_file)
        parser = ConfigParser()
        parser.read(self.config_file)

        configs = {}
        for section_name in parser.sections():
            configs[section_name] = self._generate_api_specification(
                section_name, parser[section_name])

        logging.info("API configurations reading done.")
        return ApiClientsConfigurationCollection(
            source_file=self.config_file,
            configs=configs
        )

    def _generate_api_specification(self, api_name: str, cfg: ConfigParser) -> ApiSpecification:
        """Reads and compose configuration for specific API.

        Args:
            api_name (str): name of the API.
            cfg (ConfigParser): configuration of the API.

        Returns:
            ApiSpecification: ready-to-go configuration of the API client.
        """
        logging.info('Generating API specification for API "%s".', api_name)
        api_cfg = BasicApiConfiguration(name=api_name, **cfg)

        # Timeout will be str if defined in base config, so we need to conver it
        api_cfg.timeout = self._convert_to_int(api_cfg.timeout)

        api_cfg.requests = self._read_json_from_file(api_cfg.requests)
        api_cfg.schemas = self._read_json_from_file(api_cfg.schemas)
        api_cfg.headers = self._parse_json(api_cfg.headers)
        api_cfg.cookies = self._parse_json(api_cfg.cookies)
        api_cfg.auth = self._parse_tuple(api_cfg.auth)
        request_catalog = RequestCatalogComposer(api_cfg).compose()

        logging.debug('API specification for "%s" was created successfully.', api_name)
        return ApiSpecification(api_config=api_cfg,
                                req_catalog=request_catalog)

    def _parse_tuple(self, value: str) -> tuple:
        """Parses given value as tuple string or file, depending on value format.

        Args:
            value (str): value to parse.

        Returns:
            tuple: tuple of parsed values
        """
        logging.debug('Parsing tuple from [%s] of type %s.', value, type(value))
        if not value:
            return tuple()

        # Try to parse tuple as is - e.g. quoted comma-separated values
        # in round brackets defined in base config
        parsed_value = [v.strip(' "\'')
                        for v in value.strip(" \n()").split(',')
                        if v.strip(' "\'')]
        if parsed_value is not None:
            logging.debug('Parsed tuple from line = %s', parsed_value)
            return tuple(parsed_value)

        # If not parsed - consider value to be a filename and read it
        logging.debug('Parsing tuple: read from file [%s]', value)
        return self._read_tuple_from_file(value)

    def _parse_json(self, value: str) -> dict:
        """Parses value as JSON string or file, depending on value format.

        Args:
            value (str): value to parse.

        Returns:
            dict: parsed JSON.
        """
        logging.debug('Parsing JSON from [%s] of type %s.', value, type(value))
        if value is None:
            return {}

        parsed_value = None
        # Try to parse JSON as is - e.g. JSON pieces defined in base config
        parsed_value = self._convert_to_json(value)
        if parsed_value is not None:
            return parsed_value

        # If not parsed - consider value to be a filename and read it
        logging.debug('Parsing JSON: read from file [%s]', value)
        return self._read_json_from_file(value)

    def _convert_to_int(self, value: str) -> None:
        """Converts value to integer.

        Args:
            value (str): value to convert.

        Returns:
            int: parsed value.
        """
        if value is None or isinstance(value, int):
            return value

        return int(value)

    def _convert_to_tuple(self, value: str) -> tuple|None:
        """Converts given value to a tuple. If string is not in
        tuple format - returns None.

        Args:
            value (str): string in format ("val1", "val2")

        Returns:
            tuple|None: _description_
        """
        logging.debug('Convert to tuple invoked for [%s].', value)
        value_substr = value.strip(' \n')
        if not value_substr.startswith('('):
            return None

        logging.debug('Converting to tuple.')
        return tuple([v.strip('"\'')
                for v in value_substr.strip('\n()').split(',')
                if v.strip('"\'')])

    def _convert_to_json(self, value: str) -> dict|None:
        """Tries to parse value to JSON, if string is not
        in JSON-like format (single-/double-quoted lines) - returns None.

        Args:
            value (str): value to convert.

        Returns:
            dict|None: parsed JSON as dict,
             or None, if value is not in json format
        """
        logging.debug('Convert to JSON invoked for [%s].', value)
        if not value:
            return {}

        value_substr = ''.join(value.strip('\n').split('\n'))
        if not (value_substr.startswith('"') or value_substr.startswith("'")):
            return None

        logging.debug('Converting to JSON.')
        return json.loads(f'{{{value_substr}}}')

    def _read_json_from_file(self, filename: str) -> dict:
        """Reads json from given file.

        Args:
            filename (str): path to file.

        Raises:
            FileNotFoundError: if file was not found.

        Returns:
            dict: parsed JSON.
        """
        logging.debug('Reading JSON from file: %s', filename)
        if not filename:
            return {}

        filename = self._convert_path_to_platform_specific(filename)
        if not os.path.exists(filename):
            raise FileNotFoundError(f'Failed to found "{filename}" file '
                                    'during API configuration parsing.')

        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)

    def _read_tuple_from_file(self, filename: str) -> tuple:
        """Reads tuple from given file.

        Args:
            filename (str):  path to file.

        Raises:
            FileNotFoundError: if file was not found.

        Returns:
            tuple: parsed tuple.
        """
        logging.debug('Reading tuple from file: %s', filename)
        if not filename:
            return {}

        filename = self._convert_path_to_platform_specific(filename)
        if not os.path.exists(filename):
            raise FileNotFoundError(f'Failed to found "{filename}" file '
                                    'during API configuration parsing.')
        with open(filename, 'r', encoding='utf-8') as file:
            content = ''.join(file.readlines())

        return self._convert_to_tuple(f'({content})')

    def _convert_path_to_platform_specific(self, path: str) -> str|None:
        """Converts separators in path to separator of current platform

        Args:
            path (str): path to file.

        Returns:
            str|None: path to file adopted to current system's style of separators.
        """
        if platform.system().lower() == 'windows':
            return path.replace(r'/', os.sep)

        return path.replace('\\', os.sep)


class RequestCatalogComposer:
    """Composes requests into request catalogue"""
    def __init__(self, api_config: BasicApiConfiguration):
        self.api_config = api_config

    def compose(self) -> dict:
        """Checks each request in catalogue and:
        - links JSON schema if schema name is given;
        - updates request headers with basic config values.

        Raises:
            ValueError: On referencing to unknown schema name.

        Returns:
            dict: dictionary of pre-configured reqeusts
        """
        logging.debug('RequestCatalogComposer: Composing Request catalog '
                     'for "%s" of %s request(s).',
                     self.api_config.name, len(self.api_config.requests))

        catalog = {}
        if not self.api_config.requests:
            logging.debug('RequestCatalogComposer: Not requests found.')
            return catalog

        for request_name, request_data in self.api_config.requests.items():
            logging.debug('RequestCatalogComposer: Preparing "%s" request.', request_name)
            catalog_entity = self._create_catalog_entitity(request_name,
                                                           request_data)

            # Note:
            # Each request must be tested for unknown schema_name and
            # error must be raised error even if schemas was never defined.
            # This might by a configuration mistake, but it should be
            # reported before any test launches. '''
            self._link_response_to_schema(catalog_entity)

            # Apply base config values to each request
            if self.api_config.headers:
                self._compose_request_values(catalog_entity.request.headers,
                                             self.api_config.headers)

            if self.api_config.cookies:
                self._compose_request_values(catalog_entity.request.cookies,
                                             self.api_config.cookies)

            if self.api_config.auth and not catalog_entity.request.auth:
                catalog_entity.request.auth = self.api_config.auth

            if self.api_config.timeout and not catalog_entity.request.timeout:
                catalog_entity.request.timeout = self.api_config.timeout

            catalog[request_name] = catalog_entity

        return catalog

    def _link_response_to_schema(self, entity: CatalogEntity) -> None:
        """Checks whether JSON Schema is defined for request's response or it's
        defined by name, and if later links actual schema to response by it's name.

        Args:
            request (CatalogEntity): catalog entity, instance of
            `utils.apiclient.models.CatalogEntities`.

        Raises:
            ValueError: On referencing to unknown schema name.
        """
        logging.debug('RequestCatalogComposer: Linking response of "%s" '
                      'to schema.', entity.name)
        if entity.response.schema:
            return

        schema_name = entity.response.schema_name
        logging.debug('Schema name is "%s".', schema_name)
        if not schema_name:
            return

        if schema_name not in self.api_config.schemas:
            raise ValueError(f'Failed to find schema with name "{schema_name}" '
                             f'for request "{entity.name}" of "{self.api_config.name}" API.')

        logging.debug('Link response.schema to "%s" schema.', schema_name)
        entity.response.schema = self.api_config.schemas[schema_name]

    def _compose_request_values(self, request_value: dict, config_value: dict) -> None:
        """Apply config-level request values. If request have request-level
        value - merges both (overriding config-level one).

        Args:
            request_value (dict): Request data.
            config_value (dict): Config-level values
        """
        if not request_value:
            request_value.update(config_value)
            return

        # Update request level values and avoid override
        for key, value in config_value.items():
            if key not in request_value:
                request_value[key] = value

    def _create_catalog_entitity(self, request_name: str, request_data: dict) -> CatalogEntity:
        """Creates catalog entity from request dictionary.

        Args:
            request_name (str): name of the request entity
            request_data (dict): request data

        Returns:
            CatalogEntity: catalog entity.
        """
        request = RequestEntity(**request_data.get('request'))
        response = ResponseEntity(**request_data.get('response'))
        return CatalogEntity(request_name, request, response)
