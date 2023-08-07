"""Wraps JSON content and provide interface for accessing it's properties"""
import builtins
from typing import Any
from abc import ABC, abstractmethod

from utils.json_content.pointer import Pointer, ROOT_POINTER, APPEND_CHAR, POINTER_PREFIX

EXC_MSG__INVALID_POINTER_TYPE = 'Invalid pointer "{pointer_str}". '\
                                'Pointer must be valid JSON pointer (e.g. "/a/b/c").'
EXC_MSG__UPDATE_ROOT_ERROR = 'Direct root modifications is not allowed! ' \
                             'Specified pointer is required to add/update keys!'
EXC_MSG__INVALID_STORAGE = 'Path node "/{path}" at pointer "{pointer}" '\
                           'is not a dict or list'
EXC_MSG__DICT_KEY_NOT_EXISTS = 'Key "{key}" is not present ' \
                               'in node "/{path}" of pointer "{pointer}".'
EXC_MSG__LIST_INDEX_OOB = 'Index "{key}" is out of range for given node "/{path}" ' \
                          'at pointer "{pointer}". {hint}'
EXC_MSG__LIST_INDEX_ERROR = 'Invalid list index "{key}" at node "/{path}" of pointer "{pointer}". '\
                            '{hint}'

EXC_MSG_HINT__RANGE = 'Index must be signed integer in list\'s range.'
EXC_MSG_HINT__FORMAT = 'Index must be signed integer (to update specific '\
                       'index in list bounds) or "-" (to append new element).'


class AbstractJsonContentWrapper(ABC):
    """Abstract cl1ass for json content wrappers"""
    @abstractmethod
    def get(self, pointer) -> Any:
        """Returns value at given pointer from the content
        or return entire content."""

    @abstractmethod
    def update(self, pointer, value) -> bool:
        """Updates value at given pointer in the content."""

    @abstractmethod
    def delete(self, pointer) -> bool:
        """Removes value at given pointer from the content
        or clears entire content."""


class JsonContentWrapper(AbstractJsonContentWrapper):
    """Class to wrap JSON data with get/update/delete methods that use JSON Pointers"""
    __slots__ = ['__content', '__suppress_exceptions', '__context']

    def __init__(self, content: dict):
        self.__content = content
        self.__suppress_exceptions = False
        self.__context = None

    def get(self, pointer: str) -> Any:
        """Returns property at given pointer.

        Args:
            pointer (str, optional): JSON pointer to a property as string.

        Raises:
            IndexError: on attempt to get element of list by out of bound index.
            KeyError: when pointer uses non-existent node.

        Returns:
            Any: value at given pointer.
        """
        if pointer == ROOT_POINTER:
            return self.__content

        storage, key = self.__get_property_storage(pointer)
        return storage[key]

    def update(self, pointer: str, value: Any) -> bool:
        """Updates value of property at given pointer.

        Args:
            pointer (str): JSON pointer to a property as string.
            value (Any): new value of the property.

        Raises:
            ValueError: on attempt to update root node.
            IndexError: on attempt to update list element with out of range index.
            KeyError: when pointer uses non-existent node.

        Returns:
            bool: result of the operation (True if success)
        """
        if pointer == ROOT_POINTER:
            raise ValueError(EXC_MSG__UPDATE_ROOT_ERROR)

        # Validation mode ADD will handle both update dict/list
        # and append list case. If key is not valid - exception
        # will be raised
        storage, key = self.__get_property_storage(
            pointer,
            check_key_exists=False
        )

        if (isinstance(storage, dict) or isinstance(key, int)):
            # Key for dictionary OR key is valid index for list -- update dict/list
            storage[key] = value
        else:
            # Key is not index for storage - is Append to list
            storage.append(value)

        return True

    def delete(self, pointer: str) -> bool:
        """Deletes node at given pointer.
        No error will be raised if desired node doesn't exists.

        Args:
            pointer (str): JSON pointer as string. Pointer may be
            root ('') - entire JSON structure will be cleared.

        Returns:
            bool: result of the operation (True if node was removed,
            False if node wasn't found)
        """

        # Clear entire content if method called for Root pointer
        if pointer == ROOT_POINTER:
            self.__content.clear()
            return True

        # Suppress exceptions, to avoid unwanted errors on deletion of
        # already deleted node
        storage, key = self.__get_property_storage(pointer, suppress_exc=True)

        # Path to node is incorrect or key not exists - do nothing
        if key is None:
            return False

        del storage[key]
        return True

    def __get_property_storage(self, pointer: str,
            suppress_exc: bool = False,
            check_key_exists: bool = True
        ) -> tuple[dict|list, str]:

        try:
            ptr: Pointer = Pointer.from_string(pointer)
        except ValueError as err:
            raise ValueError(EXC_MSG__INVALID_POINTER_TYPE.format(
                pointer_str=pointer)) from err

        if not ptr.is_pointer:
            raise ValueError(EXC_MSG__INVALID_POINTER_TYPE.format(pointer_str=pointer))

        # Exctract final key from path
        path = ptr.pointer[:-1]

        # Initialize search from root
        self.__suppress_exceptions = suppress_exc
        storage = self.__content

        for idx, key in enumerate(path):
            self.__context = (ptr.raw, path[:idx])
            key = self.__resolve_key(storage, key, check_key_exists=True)

            # Storage or key is not valid (and exception is suppressed)
            # exit with empty results
            if key is None:
                return (None, None)

            storage = storage[key]

        self.__context = (ptr.raw, ptr.pointer)
        keyname = self.__resolve_key(storage, ptr.pointer[-1], check_key_exists)

        # Reset state
        self.__suppress_exceptions = False
        self.__context = None

        return (storage, keyname)

    def __resolve_key(self, storage: Any, key: str, check_key_exists: bool) -> str|int|None :
        """Validates and resolves key (e.g. index for list) and storage.
        Checks that storage is a list or dict.
        If 'validate_mode' is not KeyValidationMode.NONE - validates key:
        - for list storage:
            - check that index is an valid integer (or '-' char)
            - index is in list's range
        - for dict: check that key presents

        Args:
            storage (Any): possible storage to check.
            key (str): key to check.
            check_key_exists (bool): if set to True - validated key is present/in range of list.
            Otherwise - avoid validation for dictionary storage, for list storage still checks
            that key is in range or key is append sign ("-")

        Raises:
            ValueError: when storage is not a list or dict.
            KeyError: when non-existent key or index was given.

        Returns:
            str|int: resolved key as integer index or string. If exceptions
            are suppressed, but validation failed - returns None.
        """

        match type(storage):
            case builtins.list:
                key = self.__validate_list_index(storage, key, check_key_exists)
            case builtins.dict:
                key = self.__validate_dict_key(storage, key, check_key_exists)
            case _:
                if self.__suppress_exceptions:
                    return None

                raise ValueError(self.__format_exc(EXC_MSG__INVALID_STORAGE))

        return key

    def __validate_list_index(self, storage: list, key: str,
                              check_key_exists: bool) -> str|int|None:
        """Validates that list's index is an integer in range or '-'
        sign (if validation mode is 'ADD').

        Returns:
            str|int|None: index or '-' sign if validation successful.
            Otherwise None or exception raises.
        """

        if isinstance(key, str):
            if key.lstrip('-').isdigit():
                # Signed number - check for OOB below
                key = int(key)
            elif (not check_key_exists and key == APPEND_CHAR):
                # Append character on update case - return as is
                return key
            else:
                # Some string - raise an error
                if self.__suppress_exceptions:
                    return None

                raise KeyError(self.__format_exc(
                    EXC_MSG__LIST_INDEX_ERROR,
                    key = key,
                    hint = (EXC_MSG_HINT__RANGE
                            if check_key_exists else
                            EXC_MSG_HINT__FORMAT)
                ))

        # Out of range error

        if key >= len(storage) or abs(key) > len(storage):
            if self.__suppress_exceptions:
                return None

            raise IndexError(self.__format_exc(
                EXC_MSG__LIST_INDEX_OOB,
                key = key, hint = EXC_MSG_HINT__RANGE
            ))

        return key

    def __validate_dict_key(self, storage: dict, key: str,
                            check_key_exists: bool) -> str|None:
        """Validates list's index to be integer in range or '-' sign"""
        if not check_key_exists or key in storage:
            return key

        if self.__suppress_exceptions:
            return None
        raise KeyError(
            self.__format_exc(EXC_MSG__DICT_KEY_NOT_EXISTS, key = key))

    def __format_exc(self, message: str, **kwargs) -> str:
        """Formats exception message, providing context's
        'pointer' and 'path' values"""
        return message.format(
            pointer = self.__context[0],
            path = POINTER_PREFIX.join(self.__context[1]),
            **kwargs
        )
