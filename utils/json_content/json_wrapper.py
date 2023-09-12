"""Wraps JSON content and provide interface for accessing it's properties"""
from typing import Any
from .pointer import Pointer, APPEND_CHAR


EXC_MSG__INVALID_POINTER_TYPE = 'Invalid pointer "{pointer_str}". '\
                                'Pointer must be valid JSON pointer (e.g. "/a/b/c").'
EXC_MSG__UPDATE_ROOT_ERROR = 'Direct root modifications is not allowed! ' \
                             'Specified pointer is required to add/update keys!'

EXC_MSG__LIST_INDEX_ERROR = 'Update failed due to invalid list index "{key}" at '\
                                'node "/{path}" of pointer "{pointer}". {hint}'
EXC_MSG__INVALID_STORAGE = 'Not possible to add new key/element to path node "/{path}" '\
                                'at pointer "{pointer}", target node is not a dict or list.'
EXC_MSG_HINT__FORMAT = 'Index must be an integer in list\'s range (to update '\
                       'element at specific index) or "-" (to append new element).'


class JsonWrapper:
    """Class to wrap JSON data with get/update/delete methods that use JSON Pointers.

    Internally creates flattened representation of content that provides fast access
    to the nodes and keeps this representation up-to-date when .update()/.delete() methods
    are used.

    Note: After direct modifications made to the content one should use .refresh() method
    to restore integrity of internal reference structure!
    """
    __slots__ = ["_content", "_node_map"]

    def __init__(self, content: dict|list):
        self._content: dict|list = content
        self._node_map: dict[Pointer, tuple[dict|list, str]] = None
        self.refresh()

    def refresh(self):
        """Recalculates flattened structure of the content. Should be used when
        changes were made to underlaying content directly, in order to refresh
        JsonWrapper's internal representation of content.
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

    def get(self, pointer: str|Pointer) -> Any:
        """Returns property at given pointer.

        Args:
            pointer (str|Pointer): JSON pointer to a property.

        Raises:
            ValueError: when pointer with invalid syntax was given.
            KeyError: when key is missing from pre-calculated document structure
            map.

        Returns:
            Any: value at given pointer.
        """
        pointer = self.__convert_to_pointer_obj(pointer)
        return self.__unsafe_get(pointer)

    def get_or_default(self, pointer: str|Pointer, default_value: Any) -> Any:
        """Returns property at given pointer or default_value
        if property is not present.

        Args:
            pointer (str|Pointer): JSON pointer to a property as string.
            default_value (Any): value to fallback to.

        Raises:
            ValueError: when pointer with invalid syntax was given.

        Returns:
            Any: property's value or 'default_value'
        """
        pointer = self.__convert_to_pointer_obj(pointer)
        if pointer in self._node_map:
            return self.__unsafe_get(pointer)

        return default_value

    def delete(self, pointer: str|Pointer) -> bool:
        """Deletes node at given pointer.
        No error will be raised if desired node doesn't exist.

        Args:
            pointer (str+Pointer): JSON pointer as string. Pointer may be
            root pointer to clear entire JSON structure.

        Raises:
            ValueError: when pointer with invalid syntax was given.

        Returns:
            bool: result of the operation (True if node was removed,
            False if node wasn't found)
        """
        pointer: Pointer = self.__convert_to_pointer_obj(pointer)

        if pointer.path is None:
            self._content.clear()
            self._node_map.clear()
            return True

        if pointer not in self._node_map:
            return False

        storage, key = self.__unsafe_get_storage(pointer)
        del storage[key]
        if isinstance(storage, list):
            # In case of list element delete - recalculate entire storage,
            # because elements may shift, invalidating entire subsection of nodes map
            storage_pointer = pointer.parent()

            if storage_pointer.path is None:
                self.refresh()
            else:
                self.__delete_stale_nodes(storage_pointer)
                self.__add_new_nodes(storage_pointer)

        else:
            # For dict it should be ok to remove map for specific key and it's childs
            # if key contained container.
            del self._node_map[pointer]
            self.__delete_stale_nodes(pointer)

        return True

    def update(self, pointer: str|Pointer, value: Any) -> bool:
        """Updates value of property at given pointer.

        Args:
            pointer (str|Pointer): JSON pointer to a property as string.
            value (Any): new value of the property.

        Raises:
            ValueError: when pointer with invalid syntax was given.
            ValueError: on attempt to update root node or trying to
            add new node/element to not a list/dict.
            IndexError: on attempt to update list element with out of range index.
            KeyError: when pointer have missing nodes in it's path.

        Returns:
            bool: result of the operation (True if success)
        """
        pointer: Pointer = self.__convert_to_pointer_obj(pointer)
        if pointer.path is None:
            raise ValueError(EXC_MSG__UPDATE_ROOT_ERROR)

        # Add case: new key for dict or '-' to append to list
        if pointer not in self._node_map:
            parent_pointer = pointer.parent()
            new_key = pointer.path[-1]
            storage = self.__unsafe_get(parent_pointer)

            if isinstance(storage, list):
                if new_key != APPEND_CHAR:
                    raise IndexError(EXC_MSG__LIST_INDEX_ERROR.format(
                        key=new_key,
                        path=parent_pointer,
                        pointer=pointer,
                        hint=EXC_MSG_HINT__FORMAT
                    ))

                storage.append(value)

                new_index = len(storage) - 1
                pointer = parent_pointer.child(new_index)
                self._node_map[pointer] = (storage, new_index)
            elif isinstance(storage, dict):
                storage[new_key] = value
                self._node_map[pointer] = (storage, new_key)
            else:
                raise ValueError(EXC_MSG__INVALID_STORAGE.format(
                    path=parent_pointer,
                    pointer=pointer
                ))

            if isinstance(value, list|dict):
                self.__add_new_nodes(pointer)

            return True

        # Update case
        # - delete stale nodes for given pointer (e.g. pointers to list elements)
        # - change value
        # - if new value is container - calculate nested nodes and add to map
        storage, key = self.__unsafe_get_storage(pointer)

        if isinstance(storage[key], (dict|list)):
            self.__delete_stale_nodes(pointer)

        storage[key] = value
        self._node_map[pointer] = (storage, key)

        if isinstance(value, (dict|list)):
            self.__add_new_nodes(pointer)

        return True

    def __unsafe_get(self, pointer: Pointer) -> Any:
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

    def __unsafe_get_storage(self, pointer: Pointer) -> tuple[list|dict, str]:
        """Returns storage and key selected by given pointer

        Args:
            pointer (str|Pointer): pointer to find.

        Raises:
            KeyError: when given pointer is missing in the content.

        Returns:
            tuple(list|dict, str): storage and key name/index by pointer.
        """
        if pointer.path is None:
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

    def __add_new_nodes(self,  storage_pointer: Pointer):
        """Scans for new child nodes of given pointer"""

        new_nodes = self.__scan_storage(self.__unsafe_get(storage_pointer), storage_pointer.path)
        self._node_map.update(new_nodes)

    def __delete_stale_nodes(self, storage_pointer: Pointer):
        """Delete existing child nodes of given pointer"""
        stale_nodes = [node for node in self._node_map if node.is_child_of(storage_pointer)]
        for node in stale_nodes:
            del self._node_map[node]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, (JsonWrapper, dict, list)):
            return False

        if isinstance(other, JsonWrapper):
            return self._content == other._content

        return self._content == other

    def __contains__(self, pointer: str|Pointer) -> bool:
        """Checks that property presents in the content.
        Returns True if pointer refers to existing property.

        Args:
            pointer (str|Pointer): JSON pointer to a property as string.

        Returns:
            bool: True if property presents, otherwise False.
        """
        pointer = self.__convert_to_pointer_obj(pointer)
        return pointer in self._node_map

    def __iter__(self):
        for ptr in self._node_map.keys():
            val = self.__unsafe_get(ptr)
            if isinstance(val, (list, dict)):
                continue
            yield ptr, val

    def __repr__(self):
        elements = []
        for ptr, value in self:
            value = f'"{value}"' if isinstance(value, str) else str(value)
            elements.append(f'"{ptr}"={value}')

        return f'JsonWrapper({", ".join(elements)})'

    @staticmethod
    def __convert_to_pointer_obj(pointer):
        if isinstance(pointer, Pointer):
            return pointer

        try:
            ptr: Pointer = Pointer.from_string(pointer)
        except ValueError as err:
            raise ValueError(EXC_MSG__INVALID_POINTER_TYPE.format(
                pointer_str=pointer)) from err

        return ptr
