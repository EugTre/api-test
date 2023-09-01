"""Data read module"""
import re
import json
import pathlib
from typing import Any


class DataReader:
    """Data processing class to help deserialize data"""
    INT_PATTERN = re.compile(r'^-?\d+$')
    FLOAT_PATTERN = re.compile(r'^-?\d+\.\d+?$')

    @staticmethod
    def read_from_file(filename: str|pathlib.Path, extension: str = None) -> Any:
        """Reads data from file and parse it according to file extension.

        JSON files will be parsed using standard json lib.
        Plain files will be parsed to value of pythonic data type or to a string.

        Args:
            filename (str | pathlib.Path): path to file.
            extension (str, optional): Extension use for parser selection.
            Defaults to None, file exstension will be used.

        Raises:
            FileNotFoundError: when file path doesn't exists.
            json.decoder.JSONDecodeError: if JSON file parsed and syntax is invalid.

        Returns:
            Any: file content.
        """
        if not filename:
            return None

        if isinstance(filename, str):
            filename = pathlib.Path(filename)

        if not filename.exists():
            raise FileNotFoundError(f'DataReader failed to find "{filename}" file.')

        if extension is None:
            extension = filename.suffix.strip('.')

        if extension == 'json':
            return DataReader._read_json_from_file(filename)

        return DataReader._read_plain_text_file(filename)

    @staticmethod
    def _read_json_from_file(filename: pathlib.Path) -> dict:
        """Reads JSON from given file. Additionaly removes one-line C-like
        comments ('// comment') before passing content to json parser.

        Args:
            filename (pathlib.Path): path to file.

        Raises:
            json.decoder.JSONDecodeError: if JSON syntax is invalid.

        Returns:
            dict: parsed JSON.
        """
        one_line_comment = re.compile(r'^\s*//.*')
        with open(filename, 'r', encoding='utf-8') as file:
            content = []
            while line := file.readline():
                if one_line_comment.match(line.strip()):
                    continue
                content.append(line)

        content = '\n'.join(content)
        try:
            json_content = json.loads(content)
        except json.decoder.JSONDecodeError as err:
            lines = err.doc.splitlines()
            error_line = lines[err.lineno - 1] if lines else ''
            mark_error_line = ' ' * (err.colno-1)
            err.add_note(f'Syntax error occured during "{filename}" file parsing.')
            err.add_note(f'Failed on line {err.lineno} (char: {err.colno-1}): '
                        f'\n{error_line}\n{mark_error_line}^')
            if not error_line.strip():
                err.add_note('No content to parse.')
            raise err

        return json_content

    @staticmethod
    def _read_plain_text_file(filename: pathlib.Path) -> int|float|bool|str:
        """Reads plain file text and tries to convert it to one of python data types:
        - if multilines detected - convert to string, appended with whitespace
        - if value matches digit syntax - convert to int or float
        - if value matches to 'true' or 'false' - convert to bool
        - otherwise - convert to str

        Args:
            filename (pathlib.Path): _description_

        Returns:
            int|float|bool|str: _description_
        """
        with open(filename, 'r', encoding='utf-8') as file:
            content = [line.strip() for line in file.readlines()]

        # Multiline - return concatenated string
        if len(content) > 1:
            return ' '.join(content)

        content = content[0]

        # Bool
        if content.lower() in ('true', 'false'):
            return content.lower() == 'true'

        # Integer
        if DataReader.INT_PATTERN.match(content):
            return int(content)

        # Float
        if DataReader.FLOAT_PATTERN.match(content):
            return float(content)

        # Otherwise - return as is
        return content
