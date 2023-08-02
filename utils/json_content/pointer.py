"""Pointer to JSON element"""
from enum import Enum
from dataclasses import dataclass
from typing import Self

POINTER_PREFIX = "/"
REF_PREFIX = "!ref "
FILE_PREFIX = "!file "
REF_SEP = "/"

class PointerType(Enum):
    """Type of pointer"""
    POINTER = 0
    REFERENCE = 1
    FILE_REF = 2

@dataclass(frozen=True, slots=True)
class Pointer:
    """Class to wrap JSON Pointer.
    Provides parsing and validation of pointers.
    Adds support of !ref and !file keywords for advanced JSON parsing.
    """
    pointer: tuple
    type: PointerType
    raw: str
    is_file: bool
    is_reference: bool
    is_pointer: bool

    def __str__(self):
        return f'{self.type.name}: {self.raw}'

    @staticmethod
    def from_string(pointer_str: str) -> Self:
        """Parses given string pointer and return instance of Pointer class.
        Raises errors if pointer has invalid structure.

        Raises:
            ValueError: when None passed
            ValueError: when pointer is empty
            ValueError: when Pointer/Ref pointer doesn't start from root ('/')
            ValueError: when Pointer/Ref pointer have undefined (empty) path element
        """
        if pointer_str is None:
            raise ValueError('Pointer should be a string in format '
                             '"/a/b/c" or "!ref /a/b/c" or "!file path/to/file"')
        raw = pointer_str
        path = None
        ptr_type = None
        is_file = False
        is_pointer = False
        is_reference = False

        if pointer_str.startswith(FILE_PREFIX):
            ptr_type = PointerType.FILE_REF
            is_file = True
            path = pointer_str[len(FILE_PREFIX):].strip()
        else:
            if pointer_str.startswith(REF_PREFIX):
                ptr_type = PointerType.REFERENCE
                is_reference = True
                pointer = pointer_str[len(REF_PREFIX):].strip()
            else:
                ptr_type = PointerType.POINTER
                is_pointer = True
                pointer = pointer_str

            if not pointer.startswith(POINTER_PREFIX):
                raise ValueError(f'Pointer "{pointer_str}" should start '
                                  'from root "/" element.')

            if len(pointer) > 1:
                path = tuple(v.strip() for v in pointer[1:].split(REF_SEP))
                if '' in path:
                    raise ValueError(f'Undefined (empty) reference in "{pointer_str}" '
                                  'is not allowed.')
            else:
                path = ('',)

        if not path:
            raise ValueError(f'Pointer "{pointer_str}" has invalid/empty path!')

        return Pointer(pointer=path, raw=raw, type=ptr_type,
                       is_file=is_file, is_pointer=is_pointer, is_reference=is_reference)

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
            value.startswith(POINTER_PREFIX)
            or value.startswith(FILE_PREFIX)
            or value.startswith(REF_PREFIX))

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
        return isinstance(value, str) and (
            value.startswith(FILE_PREFIX)
            or value.startswith(REF_PREFIX))



if __name__ == '__main__':
    # Tests
    ptrs = [
        "/kek",
        "/",
        "/kek/lol/a",
        "!ref /kek/lol",
        "!file content/file.json",
        "!ref    /kek   /lol   /a  ",
        "!file    content  /  file.json",
        "some other value",
        "!ref /sad//sds"
    ]
    for p in ptrs:
        title = f'PTR: "{p}"'
        print(f'{"-" * 24} {title:^50} {"-" * 24}')
        is_ptr = Pointer.match_any_pointer(p)
        print(f'Contains any pointer?: {is_ptr}')

        is_ref_ptr = Pointer.match_ref_pointer(p)
        print(f'Contains Ref pointer?: {is_ref_ptr}')

        try:
            ptr = Pointer.from_string(p)
        except ValueError as err:
            print('E' * 50)
            print(f'E    Error occured on parsing "{p}" pointer.')
            print(f'E    {err}')
            print('E' * 50)
            print('-' * 100)
            continue
        print(ptr)
        print(f'Is pointer?: {ptr.is_pointer}')
        print(f'Is reference?: {ptr.is_reference}')
        print(f'Is file?: {ptr.is_file}')
        print('-' * 100)
