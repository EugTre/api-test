"""Pointer to JSON element"""
from enum import Enum
from dataclasses import dataclass
from typing import Self

POINTER_PREFIX = "/"
REF_PREFIX = "!ref"
FILE_PREFIX = "!file"
REF_SEP = "/"
APPEND_CHAR = '-'
ROOT_POINTER = ''

REF_PREFIX_SYNTAX = f'{REF_PREFIX} '
FILE_PREFIX_SYNTAX = f'{FILE_PREFIX} '

POINTER_SYNTAX_HINT_MSG = 'Pointer must be a string in format ' \
                          '"/a/b/c" or "!ref /a/b/c" or "!file path/to/file".'

class PointerType(Enum):
    """Type of pointer"""
    POINTER = 0
    REFERENCE = 1
    FILE_REF = 2

@dataclass(frozen=True, slots=True)
class Pointer:
    """Class to wrap JSON Pointer (RFC6901).
    Provides parsing and validation of pointers.
    Adds support of !ref and !file keywords for advanced JSON parsing.
    """
    pointer: tuple|None
    type: PointerType
    raw: str
    is_file: bool
    is_reference: bool
    is_pointer: bool

    def __str__(self):
        return f'{self.type.name}: {self.raw}'

    def get_rfc_pointer(self) -> str:
        """Returns pointer in format defined in RFC6901.
        For Reference pointer - only pointer part will be returned.
        For File reference pointer - empty string will be returned.

        Returns:
            str: pointer in RFC6901 format.
        """
        result = ''
        if self.is_pointer:
            result = self.raw
        elif self.is_reference:
            ptr = REF_SEP.join([p.replace('~', '~0').replace('/', '~1') for p in self.pointer])
            result = f'{REF_SEP}{ptr}'

        return result

    @staticmethod
    def from_string(pointer_str: str) -> Self:
        """Parses given string pointer and return instance of Pointer class.
        Raises errors if pointer has invalid structure.

        Raises:
            ValueError: when None passed
            ValueError: when Pointer/Ref pointer doesn't start from root ('/')
            ValueError: when Ref pointer target the whole document
        """

        if pointer_str is None:
            raise ValueError(f'Null pointer was given. {POINTER_SYNTAX_HINT_MSG}')

        raw = pointer_str
        path = None
        ptr_type = None
        is_file = False
        is_pointer = False
        is_reference = False

        if pointer_str == '':
            return Pointer(None, PointerType.POINTER, pointer_str,
                           False, False, True)

        tokens = pointer_str.split(' ', maxsplit=1)
        type_token = None
        if len(tokens) > 0:
            type_token = tokens[0]
            if tokens[0] in (FILE_PREFIX, REF_PREFIX) and len(tokens) == 1:
                raise ValueError(f'Invalid pointer syntax of pointer "{pointer_str}". '
                                 '{POINTER_SYNTAX_HINT_MSG}')
            tokens = tokens[1:]

        if type_token and type_token == FILE_PREFIX:
            ptr_type = PointerType.FILE_REF
            is_file = True
            path = ''.join(tokens).strip()
        elif type_token and type_token == REF_PREFIX:
            ptr_type = PointerType.REFERENCE
            is_reference = True
            pointer = ''.join(tokens).lstrip()
        else:
            ptr_type = PointerType.POINTER
            is_pointer = True
            pointer = pointer_str

        if is_file:
            if not path:
                raise ValueError(f'Pointer "{pointer_str}" has invalid/empty path!')

        else:
            if not pointer.startswith(POINTER_PREFIX):
                raise ValueError(f'Pointer "{pointer_str}" should start '
                              'from root "/" element.'
                              if is_pointer or pointer.strip() != '' else
                              'Reference to the whole document is prohibited.')

            if len(pointer) > 1:
                path = tuple(
                    v.replace('~1', '/').replace('~0', '~')
                    for v in pointer[1:].split(REF_SEP)
                )
            else:
                path = ('',)

        return Pointer(pointer=path, raw=raw, type=ptr_type,
                       is_file=is_file,
                       is_pointer=is_pointer,
                       is_reference=is_reference)

    @staticmethod
    def match_any_pointer(value: str) -> bool:
        """Checks that given string matches expected pointer syntax:
        starts from '/' or keywords "!ref"/"!file".
        May be used to check string before pointer creation, to avoid
        raising unwanted exception.

        Args:
            value (str): String to check.

        Returns:
            bool: True if string matches pointer syntax, otherwise Fasle
        """
        return isinstance(value,str) and (
            value == ''
            or value.startswith(POINTER_PREFIX)
            or value.startswith(REF_PREFIX_SYNTAX)
            or value.startswith(FILE_PREFIX_SYNTAX))

    @staticmethod
    def match_ref_pointer(value: str) -> bool:
        """Checks that given string matches expected reference
        pointer syntax (have keywords "!ref"/"!file").
        May be used to check string before pointer creation, to avoid
        raising unwanted exception.

        Args:
            value (str): String to check.

        Returns:
            bool: True if string matches ref pointer syntax, otherwise Fasle
        """
        return isinstance(value, str) and value.startswith(REF_PREFIX_SYNTAX)

    @staticmethod
    def match_file_ref_pointer(value: str) -> bool:
        """Checks that given string matches expected file reference
        pointer syntax (starts from keyword !file").
        May be used to check string before pointer creation, to avoid
        raising unwanted exception.

        Args:
            value (str): String to check.

        Returns:
            bool: True if string matches ref pointer syntax, otherwise Fasle
        """
        return isinstance(value, str) and value.startswith(FILE_PREFIX_SYNTAX)
