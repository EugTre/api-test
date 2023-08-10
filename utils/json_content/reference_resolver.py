"""Helper class to resolve !ref and !file references in JSON structures."""
import copy
import builtins
from typing import Any
from abc import ABC, abstractmethod

from utils.data_reader import DataReader
from utils.json_content.pointer import Pointer, REF_SEP, ROOT_POINTER
from utils.json_content.json_content_wrapper import AbstractContentWrapper

class AbstractReferenceResolver(ABC):
    """Abstract class for JSON Content reference resolution"""
    @abstractmethod
    def __init__(self, content_context: AbstractContentWrapper, enable_cache: bool):
        self.content = content_context

    @abstractmethod
    def resolve_all(self):
        """Scans entire content and resolves all references"""

    @abstractmethod
    def resolve(self, value: Any, node_context: str) -> Any:
        """Resolves reference of given value and return new value to assign"""

    @abstractmethod
    def invalidate_cache(self):
        """Clears referece/file cache."""


class ReferenceResolver(AbstractReferenceResolver):
    """Class to resolve references  in given `AbstractContentWrapper` object."""
    __slots__ = ["content","cache_enabled",
                 "__stack_nodes", "__stack",
                 "__ref_cache", "__file_cache"]
    def __init__(self, content_context: AbstractContentWrapper,
                 enable_cache: bool = False):
        """Creates instance of `ReferenceResolver` class.

        Args:
            content_context (AbstractContentWrapper): content wrapper to use as context
            for reference resolution.
            enable_cache (bool, optional): flag to enable cache. If set to True result
            of the reference resolution will be saved in re-used on next occurrence
            of this referecne. Defaults to False.
        """
        self.content = content_context
        self.cache_enabled = enable_cache

        self.__stack_nodes = []
        self.__stack = []

        if enable_cache:
            self.__file_cache = {}
            self.__ref_cache = {}

    def resolve_all(self):
        """Scans entire content and resolves all references"""
        self.resolve(self.content.get(''), ROOT_POINTER)

    def resolve(self, value: Any, node_context: str) -> Any:
        """Resolves given value:
        - if value is collection - recursevly loop through and resolve nested values;
        - if a string - check for "!ref" and "!file" prefix and resolve references if needed;
        - otherwise - return value as is.

        Args:
            value (Any): value to resolve.
            node_context (str | None): context descriptor (parent node), used for
            error reporting.

        Returns:
            Any: resolved value.
        """
        self.__stack_nodes.append(node_context)

        match type(value):
            case builtins.dict:
                for key, item_value in value.items():
                    value[key] = self.resolve(item_value, key)

            case builtins.list:
                for i, element in enumerate(value):
                    value[i] = self.resolve(element, str(i))

            case builtins.str:
                if Pointer.match_ref_pointer(value):
                    value = self._resolve_reference(value)
                elif Pointer.match_file_ref_pointer(value):
                    value = self._resolve_file_reference(value)

        self.__stack_nodes.pop()
        return value

    def invalidate_cache(self):
        """Clears referece/file cache."""
        self.__file_cache.clear()
        self.__ref_cache.clear()

    def _resolve_reference(self, ptr: str) -> str|dict|list|int|float|None:
        """Resolves node/key reference.
        Content's values will be also resolved before returning.

        Caches result for futher use, for same 'ptr' same
        content will be returned.

        Args:
            ptr (Pointer): reference to a JSON's dict node/list index in
            format "!ref /path/to/key".

        Raises:
            ValueError: when recursion was detected.
            KeyError: when fails to find node or key in dictionary.

        Returns:
            str|dict|list|int|float|None: resolved value.
        """

        rfc_pointer = Pointer.from_string(ptr).get_rfc_pointer()

        if self.cache_enabled and rfc_pointer in self.__ref_cache:
            return self.__copy_value(self.__ref_cache[rfc_pointer])

        self.__check_for_recursion(ptr, context_is_ref=True)
        self.__stack.append(ptr)

        try:
            value = self.content.get(rfc_pointer)
        except Exception as err:
            raise ValueError(f'Failed to resolve reference "{ptr}".\n'
                             f'{self.__get_nodepath_msg()}\n'
                             f'{err} See original exception details above.'
                             ) from err

        # Reference may point to a another reference or to a file,
        # therefore - resolve data before return
        value = self.resolve(value, f'<by ref>{rfc_pointer}')

        if self.cache_enabled:
            self.__ref_cache[rfc_pointer] = value

        self.__stack.pop()

        return self.__copy_value(value)

    def _resolve_file_reference(self, ptr: str) -> dict|list|None:
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

        path_to_file = Pointer.from_string(ptr).pointer

        if self.cache_enabled and path_to_file in self.__file_cache:
            return self.__copy_value(self.__file_cache[path_to_file])

        self.__check_for_recursion(ptr)
        self.__stack.append(ptr)

        # File may contain references or file references, or/and nested ref/file.
        # Therefore - resolve data before return.
        try:
            content = DataReader.read_json_from_file(path_to_file)
        except Exception as err:
            raise ValueError(f'Failed to resolve file reference "{ptr}".\n'
                             f'{self.__get_nodepath_msg()}\n'
                             f'{err} See original exception details above.'
                             ) from err

        content = self.resolve(content, '<from file>')

        if self.cache_enabled:
            self.__file_cache[path_to_file] = content

        self.__stack.pop()

        return content

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
            for node, stack in zip(nodes, self.__stack)]
        )
        failed_at = f' [x] Node: "{self.__stack_nodes[-1]}" -> "{path}"'

        context_name = 'Reference' if context_is_ref else 'File'
        raise RecursionError(
            f'Recursion detected! {context_name} "{path}" already in the stack.\n'
            f'Full stack:\n{full_stack}\n{failed_at}\n'
            f'{self.__get_nodepath_msg()}' )

    def __get_nodepath_msg(self) -> str:
        """Formats reference path for error messaging."""
        return f'Problem occured on parsing key "{REF_SEP.join(self.__stack_nodes)}".'

    @staticmethod
    def __copy_value(value: Any):
        """Makes deepcopy of mutable JSON value (dict or list)

        Args:
            value (Any): value to copy.

        Returns:
            Any: copy (if value is mutable) of value or value
        """
        return copy.deepcopy(value) if isinstance(value, (dict, list)) else value
