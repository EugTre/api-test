"""Pointer to JSON element"""
from dataclasses import dataclass

POINTER_PREFIX = "/"
POINTER_SEP = "/"
ROOT_POINTER = ''
APPEND_CHAR = '-'

POINTER_SYNTAX_HINT_MSG = \
    'JSON Pointer must start with "/" symbol ' \
    '(e.g. "/a/b/c") or be empty string "" to reference entire document.'

POINTER_CHILD_SYNTAX_HINT_MSG = \
    'Child sub-path must be non empty string symbol, integer, '\
    'or list/tuple of nodes names.'


@dataclass(frozen=True, slots=True)
class Pointer:
    """Class to wrap JSON Pointer (RFC6901).
    Provides parsing and validation of pointers.
    """
    path: tuple | None
    raw: str
    rfc_pointer: str

    def parent(self) -> "Pointer":
        """Returns immediate parent pointer of current pointer.
        For example for pointer "/a/b/c" this function returns
        pointer "/a/b".

        Returns:
            Pointer: instance of `Pointer` class
        """
        if self.path is None:
            return self
        return Pointer.from_path(self.path[:-1])

    def child(self, path: str | int | tuple | list) -> "Pointer":
        """Creates child pointer by appending given 'path' to current pointer.

        Args:
            path (str | int | tuple | list): sub-path as string or as
            collection of nodes names.

        Returns:
            Pointer: instance of `Pointer` class
        """
        # Check for data types / None
        if any((
            path is None,
            not isinstance(path, (int, str, tuple, list)),
            isinstance(path, (tuple, list)) and (not path or None in path)
        )):
            raise ValueError(POINTER_CHILD_SYNTAX_HINT_MSG)

        # Parse string to list
        if isinstance(path, str):
            path = path.lstrip(POINTER_PREFIX).split(POINTER_SEP)
        elif isinstance(path, int):
            path = (str(path), )

        if self.path is not None:
            path = (*self.path, *path)

        return Pointer.from_path(path)

    def is_child_of(self, pointer: 'Pointer') -> bool:
        """Returns True if current pointer is a child of
        given pointer.

        Args:
            pointer (Self): possible parent pointer.

        Returns:
            bool: True if given pointer is a parent of the current,
            False otherwise.
        """
        if self.path is None or self.path == pointer.path:
            # If current pointer is root pointer
            # or same pointer - not a child
            return False

        # If given pointer root - every other pointer is child of it
        if pointer.path is None:
            return True

        # Otherwise check for path chain to be the same
        return pointer.path == self.path[:len(pointer.path)]

    def is_parent_of(self, pointer: 'Pointer') -> bool:
        """Returns True if current pointer is a parent of
        given pointer.

        Args:
            pointer (Self): possible child pointer.

        Returns:
            bool: True if given pointer is a child of the current,
            False otherwise.
        """
        if pointer.path is None or self.path == pointer.path:
            # If given pointer is root pointer
            # or same pointer - not a parent
            return False

        # If current pointer root - every other pointer is child of it
        if self.path is None:
            return True

        # Otherwise check for path chain to be the same
        return self.path == pointer.path[:len(self.path)]

    def __eq__(self, other):
        return isinstance(other, Pointer) and self.path == other.path

    def __str__(self):
        return self.rfc_pointer

    @staticmethod
    def match(pointer_str: str) -> bool:
        """Checks that given string matches expected pointer syntax:
        is string that starts with '/' or be equal to ''.
        May be used to check string before pointer creation, to avoid
        raising unwanted exception.

        Args:
            value (str): String to check.

        Returns:
            bool: True if string matches pointer syntax, otherwise Fasle
        """
        return isinstance(pointer_str, str) and (
            pointer_str == ROOT_POINTER
            or pointer_str.startswith(POINTER_PREFIX)
        )

    @staticmethod
    def from_string(pointer_str: str) -> "Pointer":
        """Parses given string pointer and return instance of Pointer class.
        Raises errors if pointer has invalid structure.

        Raises:
            ValueError: when None passed, not a string was passed, or pointer
            is not an entire document pointer, but doesn't start from
            root ('/').

        Returns:
            Pointer: instance of `Pointer` class
        """
        if not Pointer.match(pointer_str):
            raise ValueError(f'Invalid JSON Pointer syntax "{pointer_str}". '
                             f'{POINTER_SYNTAX_HINT_MSG}')

        if pointer_str == '':
            return Pointer(None, pointer_str, pointer_str)

        return Pointer(
            path=tuple(
                Pointer.decode_escaped_chars(v)
                for v in pointer_str[1:].split(POINTER_SEP)
            ),
            rfc_pointer=pointer_str,
            raw=pointer_str
        )

    @staticmethod
    def from_path(pointer_path: tuple | list) -> "Pointer":
        """Creates pointer from path

        Args:
            pointer_path (tuple | list): path of pointer.

        Returns:
            Pointer: instance of `Pointer` class
        """
        if not pointer_path:
            return Pointer(None, ROOT_POINTER, ROOT_POINTER)

        pointer_path = tuple(str(p) for p in pointer_path)
        escaped_path = POINTER_SEP.join(
            (Pointer.encode_escaped_chars(p) for p in pointer_path)
        )

        rfc_pointer = f'{POINTER_SEP}{escaped_path}'
        return Pointer(pointer_path, rfc_pointer, rfc_pointer)

    @staticmethod
    def decode_escaped_chars(value: str) -> str:
        """Decodes escaped characts:
        ~0 - to ~
        ~1 - to /

        Args:
            value (str): string to decode.

        Returns:
            str: decoded string
        """
        return value.replace('~1', '/').replace('~0', '~')

    @staticmethod
    def encode_escaped_chars(value: str) -> str:
        """Decodes escaped characts:
        ~0 - to ~
        ~1 - to /

        Args:
            value (str): string to decode.

        Returns:
            str: decoded string
        """
        return value.replace('~', '~0').replace('/', '~1')
