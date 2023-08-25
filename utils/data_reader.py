"""Data read module"""
import os
import json
import pathlib
import logging


class DataReader:
    """Data processing class to help deserialize data"""
    @staticmethod
    def parse_tuple(value: str|list) -> tuple:
        """Parses given value as tuple string or file, depending on value format.
        Used to parse base config file values.

        Args:
            value (str): value to parse, e.g. `("val1", "val2")`.
        Returns:
            tuple: tuple of parsed values
        """
        if not value:
            return tuple()

        if isinstance(value, list):
            return tuple(list)

        # Try to parse tuple as is - e.g. quoted comma-separated values
        # in round brackets defined in base config
        parsed_value = [v.strip(' "\'')
                        for v in value.strip(" \n()").split(',')
                        if v.strip(' "\'')]
        if len(parsed_value) > 1:
            return tuple(parsed_value)

        # If not parsed - consider value to be a filename and read it
        return tuple(DataReader.read_json_from_file(value))

    @staticmethod
    def parse_json(value: str) -> dict:
        """Parses value as JSON string or file, depending on value format.
        Used to parse base config file values.
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
        parsed_value = DataReader.convert_to_json(value)
        if parsed_value is not None:
            return parsed_value

        # If not parsed - consider value to be a filename and read it
        logging.debug('Parsing JSON: read from file [%s]', value)
        return DataReader.read_json_from_file(value)

    @staticmethod
    def convert_to_int(value: str) -> None:
        """Converts value to integer.
        Args:
            value (str): value to convert.
        Returns:
            int: parsed value.
        """
        if value is None or isinstance(value, int):
            return value
        return int(value)

    @staticmethod
    def convert_to_tuple(value: str) -> tuple|None:
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

    @staticmethod
    def convert_to_json(value: str) -> dict|None:
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

        # Key-value pair should start from " or '
        value_substr = ''.join(value.strip('\n').split('\n'))
        if not (value_substr.startswith('"') or value_substr.startswith("'")):
            return None

        logging.debug('Converting to JSON.')
        content = None
        try:
            content = json.loads(f'{{{value_substr}}}')
        except json.decoder.JSONDecodeError as err:
            error_line = err.doc.splitlines()[err.lineno - 1]
            mark_error_line = ' ' * (err.colno-1)
            err.add_note(f'Failed on line: \n{error_line}\n{mark_error_line}^')
            raise err

        return content

    @staticmethod
    def read_json_from_file(filename: str|pathlib.Path) -> dict:
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

        if isinstance(filename, str):
            filename = pathlib.Path(filename)

        if not os.path.exists(filename):
            raise FileNotFoundError(f'Failed to find "{filename}" file.')

        with open(filename, 'r', encoding='utf-8') as file:
            content = None
            try:
                content = json.load(file)
            except json.decoder.JSONDecodeError as err:
                error_line = err.doc.splitlines()[err.lineno - 1] or ''
                mark_error_line = ' ' * (err.colno-1)
                err.add_note(f'Syntax error occured during "{filename}" file parsing.')
                err.add_note(f'Failed on line {err.lineno} (char: {err.colno-1}): '
                            f'\n{error_line}\n{mark_error_line}^')
                if not error_line.strip():
                    err.add_note('No content to parse.')
                raise err

            return content
