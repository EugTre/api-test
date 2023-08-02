"""Wrapper for JSON content. Provides easy content editing,
including inner content and external file references."""

import copy
import builtins
from typing import Self, Any
import logging

from utils.json_content.pointer import Pointer, POINTER_PREFIX, REF_SEP
from utils.data_reader import DataReader

class JsonContent:
    """Class to wrap JSON with update/delete methods"""
    __slots__ = ["__content", "__resolver"]
    def __init__(self, content: dict = None, from_file: str = None,
                 make_copy: bool = False,
                 resolve_references: bool = False):
        """Create a new instance of `JsonContent` wrapper class.
        One may use existing dictionary or read JSON data from a file.

        Args:
            content (dict, optional): JSON-like dictionary to wrap. Defaults to None.
            from_file (str, optional): Read JSON from given file. Defaults to None.
            make_copy (bool, optional): Make copy of given 'content' and wraps it.
            Defaults to False.
            resolve_references (bool, optional): Enable reference resolution for
            reference pointers values. Defaults to False.
        """
        imported_content = None
        if from_file:
            imported_content = DataReader.read_json_from_file(from_file)
        else:
            if content is None:
                imported_content = {}
            else:
                imported_content = copy.deepcopy(content) if make_copy else content
        self.__content = self._on_create(imported_content)
        self.__resolver = ReferenceResolver(self) if resolve_references else None

    def get(self, pointer: str = POINTER_PREFIX, make_copy: bool = False) -> Any:
        """Returns property at given pointer. By default returns a copy of value (for mutables).

        Args:
            pointer (str, optional): Pointer to a property as string or
            as instance of `pointer.Pointer` class. Defaults to '/'.
            make_copy (bool, optional): Flag to return a copy of the mutable property.
            Defaults to False.

        Returns:
            Any: value at given pointer.

        Example:
        ```
        cnt = JsonContent({
            "a": {
                "b": {
                    "c": 100
                }
            }
        })
        # selection of property 'c' will look like:
        cnt.get("/a/b/c") # 100
        ```
        """
        storage, key = self.__get_property_storage(pointer)

        if key == '':
            value = storage
        else:
            if self.__has_key(storage, key, False, pointer):
                value = storage[key]

        return (self.__copy_if_mutable(value)
                if make_copy else
                value)

    def update(self, pointer: str, value: str | int | float | list | dict | None) -> Self:
        """Updates or add content to wrapped JSON structure.
        If end key is not exists - it will be added with new value,
        but non-existent keys in the middle cause KeyError exception.

        Args:
            pointer (str): pointer to a node.
            value (str | int | float | list | dict | None): New value.

        Raises:
            ValueError: on attempt to update root node.
            KeyError: when pointer uses non-existent node.

        Returns:
            Self: instance of `JsonContent` class

        Example:
        ```
        # Initial
        ctn = JsonContent({
            "a": {
                "b": {
                    "c": 100
                }
            }
        })
        #  Node update:
        ctn.update("/a/b/c", 20)
        ctn.update("/a/b/d", 30)
        # Result:
        {
            "a": {
                "b": {
                    "c": 20,
                    "d": 30
                }
            }
        }
        """
        storage, key = self.__get_property_storage(pointer, validate_key=False)
        if not key:
            raise ValueError(
                    'Direct root modifications is not allowed! '
                    'Use pointer to add/update keys!')

        storage[key] = value

        # Resolve value after adding it to main content.
        # In case if value has references to it's own structure.
        if self.__resolver:
            storage[key] = self.__resolver.resolve_value(storage[key])

        return self

    def delete(self, pointers: list|tuple|str) -> Self:
        """Deletes node at given pointer or several nodes, if list
        of pointers was given.
        No error will be raised if desired node doesn't exists.

        Node deletion - Args:
            pointers (str): pointer to node. Pointer may be
            root ('/') - entire JSON structure will be cleared.

        Bulk deletion - Args:
            pointers (list | tuple): iterable of pointers.

        Returns:
            Self: instance of `JsonContent` class
        """
        if not isinstance(pointers, list) or not isinstance(pointers, tuple):
            pointers = (pointers, )

        for ptr in pointers:
            storage, key = self.__get_property_storage(ptr, suppress_exc=True)
            if key is None:
                continue

            if key == '':
                storage.clear()
            else:
                # If key is not exists - skip silently
                if self.__has_key(storage, key, True):
                    del storage[key]

        return self

    def _on_create(self, content: dict|list) -> dict|list|None:
        """Method to pre-process content before wrapping.

        Args:
            content (dict | list): JSON content.

        Returns:
            dict|list|None: Pre-processed content.
        """
        return content

    def _on_export(self, content: dict|list) -> dict|list|None:
        """Method to pre-process content before full export
        (e.g. using .get()).

        Args:
            content (dict | list): JSON content.

        Returns:
            dict|list|None: Pre-processed content.
        """
        return content

    def __get_property_storage(self, pointer: str,
                                suppress_exc: bool = False,
                                validate_key: bool = True
                            ) -> tuple[dict|list, str]:
        """Selects node and key from JSON content by given pointer.

        Args:
            pointer (str | Pointer): JSON pointer.
            suppress_exc (bool, optional): supress exception if pointer
            target invalid/non-existent node or key. Instead of exception
            (None, None) is returned. Defaults to False.

        Raises:
            ValueError: when pointer is invalid.
            KeyError: when pointed to invalid/non-existent node.

        Returns:
            tuple[dict|list, str]: node (list/tuple) and keyname,
            or (None, None) if 'suppress_exc' is True and non-existent
            node was accessed.
        """
        logging.debug("Pointer to find: '%s'", pointer)

        if isinstance(pointer, str) and pointer == POINTER_PREFIX:
            # Return root content for root pointer
            return (self.__content, '')

        pointer = Pointer.from_string(pointer)
        logging.debug('Pointer = "%s"', pointer)

        if pointer.is_file:
            raise ValueError(f'{pointer} is invalid (file reference).')

        # Tailing element of pointer is a target keyname
        path = pointer.pointer[:-1]
        keyname = pointer.pointer[-1]
        storage = self.__content

        if not path:
            logging.debug('Root pointer, return root node')
            return (storage, keyname)

        logging.debug('Looking deep for pointer')
        for idx, key in enumerate(path):
            logging.debug('Checking idx=%s, key = "%s" in storage %s', idx, key, storage)

            if not self.__is_valid_node(
                storage, key, suppress_exc, True,
                (pointer.raw, path[:idx])):
                logging.debug('Key/storage is absendt. Return None')
                return (None, None)

            storage = storage[key if isinstance(storage, dict) else int(key)]
            logging.debug('Key "%s" is present, picked it\'s storage: %s', key, storage)


        logging.debug('Deep search finished. Storage=%s, keyname=%s', storage, keyname)


        if not self.__is_valid_node(
            storage, keyname, suppress_exc, validate_key,
            (pointer.raw, path)):
            return (None, None)

        return (storage, keyname if isinstance(storage, dict) else int(keyname))

    @staticmethod
    def __is_valid_node(storage: Any, key: str,
                        suppress_exc: bool,
                        validate_key: bool,
                        context: tuple) -> bool:
        """Checks that node and key are valid (present in JSON).

        Args:
            storage (list | dict): storage to check.
            key (int | str): key to check.
            suppress_exc (bool, optional): when False - raises KeyError exception
            if key is not present or node is invalid. Defaults to False.
            context (tuple, optional): exception context info - used pointer
            and path to failed node. Defaults to ().

        Returns:
            bool: result of check (True if both node and key present and
            may be selected)
        """
        is_storage = JsonContent.__is_storage(storage, suppress_exc, context)
        key_presents = (JsonContent.__has_key( storage, key, suppress_exc, context)
                        if validate_key else
                        True)

        return is_storage and key_presents

    @staticmethod
    def __has_key(storage: list|dict, key: int|str,
                  suppress_exc: bool = False,
                  context: tuple = ()) -> bool:
        """Checks if key present in given storage (True if present).
        By default raises a KeyError exception if key is absent,
        but it may be supressed.

        Args:
            storage (list | dict): storage to check.
            key (int | str): key to check.
            suppress_exc (bool, optional): when False - raises KeyError exception
            if key is not present. Defaults to False.
            context (tuple, optional): exception context info - used pointer
            and path to failed node. Defaults to ().

        Raises:
            KeyError: when non-existent key or index was given

        Returns:
            bool: key presense status.
        """

        path_ctx = (f', node "/{POINTER_PREFIX.join(context[1])}"'
                    if len(context) > 1 else '')
        context = (f', pointer "{context[0]}"{path_ctx}'
                    if context else '.')

        is_list = isinstance(storage, list)
        if is_list:
            if isinstance(key, str) and not key.isdigit():
                if suppress_exc:
                    return False
                raise KeyError(f'Invalid index "{key}" of list{context}')

            key = int(key)

        key_presence = (0 <= key < len(storage)
                        if is_list else
                        key in storage)

        logging.debug('Key: "%s", presence: %s', key, key_presence)
        if not key_presence and not suppress_exc:
            raise KeyError(f'Non-existent key or index "{key}"{context}')

        return key_presence

    @staticmethod
    def __is_storage(node: Any, suppress_exc: bool = False,
                     context: tuple = ()) -> bool:
        """Checks that given 'node' variable is list or dict.

        Args:
            node (Any): variable to check.
            suppress_exc (bool, optional): Supress exception if node is not a
            storage. Defaults to False.
            context (tuple, optional): exception context info - used pointer
            and path to failed node. Defaults to ().

        Raises:
            KeyError: when given node is not a storage.

        Returns:
            bool: result of check (True if node is a storage).
        """
        if isinstance(node, (dict, list)):
            logging.debug('Is Storage!')
            return True

        if suppress_exc:
            logging.debug('Is not storage, but supressing exception!')
            return False

        path_ctx = (f'/{POINTER_PREFIX.join(context[1])}' if len(context) > 1 else '')
        raise KeyError(f'Invalid pointer "{context[0]}", '
            f'"{path_ctx}" is not a list or dict.')

    @staticmethod
    def __copy_if_mutable(value: Any) -> Any:
        """Makes deepcopy of mutable JSON value (dict or list)

        Args:
            value (Any): value to copy.

        Returns:
            Any: copy (if value is mutable) of value or value
        """
        if not isinstance(value, (dict, list)):
            return value

        return copy.deepcopy(value)


class ReferenceResolver:
    """Resolves reference to node/file and update given JsonContent accordingly."""
    __slots__ = ["content",
                 "__stack_nodes", "__stack",
                 "__ref_cache", "__file_cache"]

    def __init__(self, content: JsonContent):
        self.__ref_cache = {}
        self.__file_cache = {}
        self.__stack_nodes = []
        self.__stack = []
        self.content = content
        self.content = self.resolve_value(content.get(make_copy=False), '')

    def resolve_value(self, value: Any, from_node: str) -> Any:
        """Resolves given value:
        - if value is collection - recursevly loop through and resolve nested values;
        - if a string - check for "!ref" and "!file" prefix and resolve references if needed;
        - otherwise - return value as is.

        Args:
            value (Any): value to resolve.
            from_node (str | None): context descriptor, used for error reporting.

        Returns:
            Any: resolved value.
        """

        self.__stack_nodes.append(from_node)

        match type(value):
            case builtins.dict:
                for key, item_value in value.items():
                    value[key] = self.resolve_value(item_value, from_node=key)

            case builtins.list:
                value = [self.resolve_value(element, from_node=str(i))
                         for i, element in enumerate(value)]

            case builtins.str:
                if Pointer.match_ref_pointer(value):
                    ptr = Pointer.from_string(value)
                    if ptr.is_reference:
                        value = self._resolve_reference(ptr)
                    else:
                        value = self._resolve_file_reference(ptr)

        self.__stack_nodes.pop()
        return value

    def _resolve_reference(self, ptr: Pointer) -> str|dict|list|int|float|None:
        """Resolves node/key reference.
        Content's values will be also resolved before returning.

        Caches result for futher use, for same 'ptr' same
        content will be returned.

        Args:
            ptr (Pointer): reference to a JSON's dict node/list index.

        Raises:
            ValueError: when recursion was detected.
            KeyError: when fails to find node or key in dictionary.

        Returns:
            str|dict|list|int|float|None: resolved value.
        """

        # Cached name should be generated anew to avoid duplicates due variations
        # of reference definition (e.g. extra spaces)
        cached_name = REF_SEP.join(ptr.pointer)
        if cached_name in self.__ref_cache:
            return self.__ref_cache[cached_name]

        self.__check_for_recursion(cached_name, context_is_ref=True)
        self.__stack.append(cached_name)

        try:
            value = self.content.get(ptr, make_copy=False)
        except KeyError as err:
            err.add_note(f'Failed to resolve reference "{ptr.raw}" - '
                         f'key "{err.args[0]}" does not exists!\n'
                         f'{self.__get_nodepath_msg()}')
            raise err

        # Reference may point to a another reference or to a file, or nested ref/file.
        # Therefore - resolve data before return
        logging.debug('Resolving values from reference "/%s"', cached_name)
        value = self.resolve_value(value, f'<by ref>{cached_name}')

        self.__ref_cache[cached_name] = value
        self.__stack.pop()

        return value

    def _resolve_file_reference(self, ptr: Pointer) -> dict|list|None:
        """Resolves file reference by reading given JSON file's content.
        Content's values will be also resolved before returning.

        Caches result for futher use, for same 'filepath_str' same
        content will be returned.

        Args:
            filepath_str (str): reference to a JSON file,
            in format '!file path/to/file'

        Raises:
            ValueError: when recursion was detected.
            FileNotFound: when file is missing.
            json.decoder.JSONDecodeError: when JSON decoding failed.

        Returns:
            dict|list|None: JSON content of the file
        """

        cached_name = ptr.pointer
        if cached_name in self.__file_cache:
            return self.__file_cache[cached_name]

        self.__check_for_recursion(cached_name)
        self.__stack.append(cached_name)

        # File may contain references or file references, or/and nested ref/file.
        # Therefore - resolve data before return.
        logging.debug('Read values from file "%s"', cached_name)
        try:
            content = DataReader.read_json_from_file(ptr.pointer)
        except Exception as err:
            err.add_note(self.__get_nodepath_msg())
            raise err

        logging.debug('Resolving values from reference "%s"', cached_name)
        content = self.resolve_value(content, '<from file>')

        self.__file_cache[cached_name] = content
        self.__stack.pop()

        return content

    def __get_nodepath_msg(self) -> str:
        """Formats reference path for error messaging."""
        return ('Problem occured on parsing key "%s"'
                % REF_SEP.join(self.__stack_nodes))

    def __check_for_recursion(self, path: str, context_is_ref: bool = False) -> None:
        """Checks for recursion during reference resolution.
        If recursion detected - raises ValueError exception.

        Recursion will be detected if given 'path' (reference or file path) already
        in the stack, meaning that same path is already in use during resolution of
        another reference.

        Args:
            path (str): path of reference or file to check.
            context_is_ref (bool, optional): mark context as Reference (True), or File (False).
            Defaults to False.

        Raises:
            ValueError: when recursion was detected.
        """
        if path not in self.__stack:
            return

        # Duplicate node found - raise an exception with details
        stack_size = len(self.__stack)
        merge_diff = 0
        if stack_size < len(self.__stack_nodes) - 1:
            merge_diff = len(self.__stack_nodes) - stack_size
            nodes = [
                REF_SEP.join(self.__stack_nodes[:merge_diff]),
                *self.__stack_nodes[merge_diff:-1]
            ]
        else:
            nodes = REF_SEP.join(self.__stack_nodes)

        full_stack = '\n'.join(
            [f'     Node "{node}" -> "{stack}"'
            for node, stack in zip(nodes, self.__stack)])
        failed_at = f' [x] Node: "{self.__stack_nodes[-1]}" -> "{path}"'

        context_name = 'Reference' if context_is_ref else 'File'

        raise RecursionError(
            f'Recursion detected! {context_name} "{path}" already in the stack.\n'
            f'Full stack:\n{full_stack}\n{failed_at}\n'
            f'{self.__get_nodepath_msg()}' )
