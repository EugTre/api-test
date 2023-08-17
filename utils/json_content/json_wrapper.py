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
                           'is not a dict or list.'
EXC_MSG__DICT_KEY_NOT_EXISTS = 'Key "{key}" is not present ' \
                               'in node "/{path}" of pointer "{pointer}".'
EXC_MSG__LIST_INDEX_OOB = 'Index "{key}" is out of range for given node "/{path}" ' \
                          'at pointer "{pointer}". {hint}'
EXC_MSG__LIST_INDEX_ERROR = 'Invalid list index "{key}" at node "/{path}" of pointer "{pointer}". '\
                            '{hint}'

EXC_MSG_HINT__RANGE = 'Index must be signed integer in list\'s range.'
EXC_MSG_HINT__FORMAT = 'Index must be signed integer (to update specific '\
                       'index in list bounds) or "-" (to append new element).'

EXC_MSG__LIST_INDEX_ERROR_FAST = 'Update failed due to invalid list index "{key}" at node "/{path}" '\
                                'of pointer "{pointer}". {hint}'
EXC_MSG__INVALID_STORAGE_FAST = 'Not possible to add new key/element to path node "/{path}" '\
                                'at pointer "{pointer}", target node is not a dict or list.'
EXC_MSG_HINT__FORMAT_FAST = 'Index must be an integer in list\'s range (to update specific '\
                             'index) or "-" (to append new element).'

class AbstractContentWrapper(ABC):
    """Abstract cl1ass for content wrappers"""
    @abstractmethod
    def __init__(self, content: dict|list):
        """Instance should be created using "content" variable"""

    @abstractmethod
    def has(self, pointer: str) -> bool:
        """Returns True if key exists in the content"""

    @abstractmethod
    def get(self, pointer: str) -> Any:
        """Returns value at given pointer from the content
        or return entire content.
        May raise IndexError or KeyError.
        """

    @abstractmethod
    def get_or_default(self, pointer: str, default_value: Any) -> Any:
        """Returns value of existent key or default_value if not found."""

    @abstractmethod
    def update(self, pointer: str, value: Any) -> bool:
        """Updates value at given pointer in the content."""

    @abstractmethod
    def delete(self, pointer: str) -> bool:
        """Removes value at given pointer from the content
        or clears entire content."""

    @abstractmethod
    def __eq__(self, other) -> bool:
        """Equals should compare content"""

    @abstractmethod
    def __contains__(self, pointer) -> bool:
        """Pointer is in the content"""

    @abstractmethod
    def __iter__(self):
        """Iterable of content"""


class JsonWrapper(AbstractContentWrapper):
    """Class to wrap JSON data with get/update/delete methods that use JSON Pointers.
    Allows iteration through underlaying dict in way like it is flat dict/list.

    Implements next features:
    - elements search without caching, which allows editing of the underlaying dict
    from other points in exchange to slower access speed.
    - allow to access list items using pythonic negative indicies.
    """
    __slots__ = ['_content', '__suppress_exceptions', '__context']

    def __init__(self, content: dict|list):
        self._content = content
        self.__suppress_exceptions = False
        self.__context = None

    def has(self, pointer: str) -> bool:
        """Checks that property presents in the content.
        Returns True if pointer refers to existing property.

        Args:
            pointer (str): JSON pointer to a property as string.

        Returns:
            bool: True if property presents, otherwise False.
        """
        if pointer == ROOT_POINTER:
            return True

        _, key = self.__get_property_storage(pointer, suppress_exc=True)
        return key is not None

    def get(self, pointer: str) -> Any:
        """Returns property at given pointer.

        Args:
            pointer (str): JSON pointer to a property as string.

        Raises:
            IndexError: on attempt to get element of list by out of bound index.
            KeyError: when pointer uses non-existent node.

        Returns:
            Any: value at given pointer.
        """
        if pointer == ROOT_POINTER:
            return self._content

        storage, key = self.__get_property_storage(pointer)
        return storage[key]

    def get_or_default(self, pointer: str, default_value: Any) -> Any:
        """Returns property at given pointer or default_value
        if property is not present.

        Args:
            pointer (str): JSON pointer to a property as string.
            default_value (Any): value to fallback to.

        Returns:
            Any: property's value or 'default_value'
        """
        if pointer == ROOT_POINTER:
            return self._content

        storage, key = self.__get_property_storage(pointer, suppress_exc=True)
        if key is None:
            return default_value

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
        No error will be raised if desired node doesn't exist.

        Args:
            pointer (str): JSON pointer as string. Pointer may be
            root ('') - entire JSON structure will be cleared.

        Returns:
            bool: result of the operation (True if node was removed,
            False if node wasn't found)
        """

        # Clear entire content if method called for Root pointer
        if pointer == ROOT_POINTER:
            self._content.clear()
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

        # Exctract final key from path
        path = ptr.path[:-1]

        # Initialize search from root
        self.__suppress_exceptions = suppress_exc
        storage = self._content

        for idx, key in enumerate(path):
            self.__context = (ptr.raw, path[:idx])
            key = self.__resolve_key(storage, key, check_key_exists=True)

            # Storage or key is not valid (and exception is suppressed)
            # exit with empty results
            if key is None:
                return (None, None)

            storage = storage[key]

        self.__context = (ptr.raw, ptr.path)
        keyname = self.__resolve_key(storage, ptr.path[-1], check_key_exists)

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
            KeyError: when storage is not a list or dict or when non-existent key was given
            IndexError: when out of range index was given.

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

                raise KeyError(self.__format_exc(EXC_MSG__INVALID_STORAGE))

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

                raise IndexError(self.__format_exc(
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

    def __iter(self, value: Any, ptr_path: tuple = tuple()):
        if isinstance(value, list):
            for idx, item in enumerate(value):
                sub_path = (*ptr_path, str(idx))
                yield from self.__iter(item, sub_path)
        elif isinstance(value, dict):
            for key, item in value.items():
                sub_path = (*ptr_path, key)
                yield from self.__iter(item, sub_path)
        else:
            yield (Pointer.from_path(ptr_path), value)

    def __eq__(self, other: AbstractContentWrapper):
        if not isinstance(other, AbstractContentWrapper):
            return False
        return self._content == other.get('')

    def __contains__(self, pointer: str):
        return self.has(pointer)

    def __iter__(self):
        yield from self.__iter(self._content)


class FastJsonWrapper(JsonWrapper):
    """Class to wrap JSON data with get/update/delete methods that use JSON Pointers.

    Extends `JsonWrapper` class with fast get mechanism (using pre-calculated flattened reference
    structure of content).

    Please note, that this implementation has some restrictions:
    - negative indicies are not allowed for lists;
    - due to nature of get mechanism direct editing of underlaying content may cause issues on
    accessing edited keys/indicies. One should use .recalculate() method to update
    internal reference structure after external changes!
    """
    __slots__ = ["_node_map"]

    def __init__(self, content: dict|list):
        super().__init__(content)
        self.recalculate()

    def recalculate(self):
        """Recalculates flattened structure of the content. Should be used after
        changes was made to underlaying content to refresh it's internal
        representation.
        """
        self._node_map = dict(self.__scan_storage(self._content))

    def __scan_storage(self, storage: list|dict,
                       pointer_path: tuple = tuple()) -> tuple[str, tuple]:
        """Deeply scans a storage and yield JSON pointer-like key and storage/key pairs
        to represent flat document structure.

        Args:
            storage (list|dict): storage to scan.
            pointer_path (tuple): current pointer of upper level.

        Yields:
            tuple[str, tuple]: JSON Pointer like key and tuple of storage and key pointer
            is refer to
        """
        is_list_storage = isinstance(storage, list)

        iter_source = enumerate(storage) if is_list_storage else storage.items()
        for key, value in iter_source:
            # Generate JSON pointer for each member of the storage
            sub_path = (*pointer_path, str(key))
            yield Pointer.from_path(sub_path), (storage, key)

            # Continue deep scan
            if isinstance(value, (dict, list)):
                yield from self.__scan_storage(value, sub_path)

    def has(self, pointer: str) -> bool:
        return self.__has(pointer)

    def get(self, pointer: str) -> Any:
        return self.__unsafe_get(pointer)

    def get_or_default(self, pointer: str, default_value: Any) -> Any:
        pointer = self.__convert_to_pointer_obj(pointer)
        if self.__has(pointer):
            return self.__unsafe_get(pointer)

        return default_value

    def delete(self, pointer: str) -> bool:
        pointer = self.__convert_to_pointer_obj(pointer)
        if pointer.path is None:
            self._content.clear()
            return True

        if not self.__has(pointer):
            return False

        storage, key = self.__unsafe_get_storage(pointer)
        del storage[key]

        # One may delete container with nested values/container
        # so recalculate storage's substructure to reflect changes
        self.__recalculate_for_storage(storage, pointer)
        return True

    def update(self, pointer: str, value: Any) -> bool:
        pointer = self.__convert_to_pointer_obj(pointer)
        if pointer.path is None:
            raise ValueError(EXC_MSG__UPDATE_ROOT_ERROR)

        # Add case: new key for dict or '-' to append to list
        if pointer not in self._node_map:
            parent_pointer = pointer.parent()
            new_key = pointer.path[-1]
            storage = self.__unsafe_get(parent_pointer)

            if isinstance(storage, list):
                if new_key != APPEND_CHAR:
                    raise IndexError(EXC_MSG__LIST_INDEX_ERROR_FAST.format(
                        key=new_key,
                        path=parent_pointer,
                        pointer=pointer,
                        hint=EXC_MSG_HINT__FORMAT_FAST
                    ))

                storage.append(value)
            elif isinstance(storage, dict):
                storage[new_key] = value
            else:
                raise KeyError(EXC_MSG__INVALID_STORAGE_FAST.format(
                    path=parent_pointer,
                    pointer=pointer
                ))

            # Add new node to map and scan for added node
            self._node_map[pointer] = (storage, new_key)
            if isinstance(value, list|dict):
                self.__recalculate_for_storage(value, pointer)

            return True

        # Update case
        storage, key = self.__unsafe_get_storage(pointer) #self._node_map[pointer]
        storage[key] = value

        if isinstance(value, (dict|list)):
            # If container added - update node map with pointer nodes
            self.__recalculate_for_storage(storage, pointer)

        return True

    def __has(self, pointer: str|Pointer) -> bool:
        if not isinstance(pointer, Pointer):
            pointer = Pointer.from_string(pointer)
        return pointer in self._node_map

    def __unsafe_get(self, pointer: str|Pointer) -> Any:
        """Returns value by given pointer using pre-calculcated document
        structure map.

        Unsafe operation - do not check for key existense and raise KeyError
        if operation fails.

        Args:
            pointer (str): JSON Pointer.

        Raises:
            KeyError: when key is missing from pre-calculated document structure
            map.

        Returns:
            Any: found value.
        """
        storage, key = self.__unsafe_get_storage(pointer)

        # In case pointer is root pointer - return whole content
        if key is None:
            return storage

        return storage[key]

    def __unsafe_get_storage(self, pointer: str|Pointer) -> tuple[list|dict, str]:
        """Returns storage and key selected by given pointer

        Args:
            pointer (str|Pointer): pointer to find.

        Raises:
            KeyError: when given pointer is missing in the content.

        Returns:
            tuple(list|dict, str): storage and key name/index by pointer.
        """
        if (isinstance(pointer, str) and pointer == ROOT_POINTER) or \
           (isinstance(pointer, Pointer) and pointer.path is None):
            return self._content, None

        pointer = self.__convert_to_pointer_obj(pointer)

        try:
            node_info = self._node_map[pointer]
        except KeyError as exc:
            # Original key error doesn't give any interesting info,
            # so overwritting exception completely
            # pylint: disable-next=raise-missing-from
            raise KeyError(f'Failed to find value by "{pointer}" JSON Pointer in the document. '
                           'Pointer refers to non-existing node or document content '
                           'was modified directly (consider calling .recalculate() '
                           'to restore integrity)') from exc
        return node_info

    def __recalculate_for_storage(self, storage: list|dict,
                                  storage_pointer: Pointer) -> dict:

        # Delete existing child nodes of storage
        stale_nodes = [node for node in self._node_map if node.is_child_of(storage_pointer)]
        for node in stale_nodes:
            del self._node_map[node]

        # Add new nodes
        new_nodes = self.__scan_storage(storage, storage_pointer.path)
        self._node_map.update(new_nodes)

    def __iter__(self):
        for ptr in self._node_map.keys():
            val = self.__unsafe_get(ptr)
            if isinstance(val, (list, dict)):
                continue
            yield ptr, val

    @staticmethod
    def __convert_to_pointer_obj(pointer):
        if isinstance(pointer, Pointer):
            return pointer

        return Pointer.from_string(pointer)