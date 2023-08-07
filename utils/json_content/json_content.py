"""Wrapper for JSON content. Provides easy content editing,
including inner content and external file references."""

import copy
import builtins

from typing import Self, Any
from utils.data_reader import DataReader
from utils.json_content.json_content_wrapper import AbstractJsonContentWrapper, JsonContentWrapper
from utils.json_content.pointer import Pointer, REF_SEP, ROOT_POINTER

class JsonContent:
    """Class to wrap JSON with get/update/delete methods and
    reference resolution mechanism"""
    __slots__ = ["content",
                 "__stack_nodes", "__stack", "__ref_cache", "__file_cache"]

    def __init__(self, content: dict|list = None, from_file: str = None,
                 make_copy: bool = False, allow_references: bool = False,
                 wrapper: AbstractJsonContentWrapper = JsonContentWrapper):
        """Create a new instance of `JsonContent` wrapper class.
        One may use existing dictionary (by using 'content' arg) or read JSON
        data from a file ('from_file' arg).

        Args:
            content (dict, optional): JSON-like dictionary to wrap. Defaults to None.
            from_file (str, optional): Read JSON from given file. Overrides 'content'
            if defined. Defaults to None.
            make_copy (bool, optional): Make a copy of content and wraps it.
            Defaults to False.
            allow_references (bool, optional): Enable reference resolution for
            reference pointers values (like '!ref /a/b' and '!file file.json').
            Defaults to False.
            wrapper (AbstractJsonContentWrapper, optional): Content wrapper class to
            use for content wrapping. Defaults to JsonContentWrapper.
        """
        if from_file:
            content = DataReader.read_json_from_file(from_file)

        if content is None:
            content = {}
        elif not from_file and make_copy:
            content = copy.deepcopy(content)

        self.content = wrapper(content)
        self.__stack_nodes = []
        self.__stack = []
        self.__file_cache = {}
        self.__ref_cache = {}
        if allow_references:
            self._resolve(self.get(), ROOT_POINTER)

    def get(self, pointer: str = ROOT_POINTER, make_copy: bool = False) -> Any:
        """Returns property at given pointer.

        Args:
            pointer (str, optional): JSON pointer to a property as string.
            Defaults to empty (return whole content).
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
        value = self.content.get(pointer)
        return self.__copy_value(value) if make_copy else value

    def update(self, pointer: str, value: Any) -> Self:
        """Updates or add content to wrapped JSON structure.
        If end key is not exists - it will be added with new value,
        but non-existent keys in the middle cause KeyError exception.

        Args:
            pointer (str): JSON pointer to a property as string.
            value (Any): New value to set.

        Raises:
            ValueError: on attempt to update root node.
            IndexError: on attempt to update list element with out of range index.
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

        self.content.update(pointer, value)
        return self

    def delete(self, pointers: str|tuple|list) -> Self:
        """Deletes node at given pointer or several nodes, if list
        of pointers was given.
        No error will be raised if desired node doesn't exists.

        Node deletion - Args:
            pointers (str): JSON pointer to a property as string. Pointer may be
            root ('/') - entire JSON structure will be cleared.

        Bulk deletion - Args:
            pointers (list | tuple): iterable of pointers.

        Returns:
            Self: instance of `JsonContent` class
        """
        if isinstance(pointers, str):
            pointers = (pointers, )

        for ptr in pointers:
            self.content.delete(ptr)

        return self

    def _resolve(self, value: Any, context_str: str) -> Any:
        """Resolves given value:
        - if value is collection - recursevly loop through and resolve nested values;
        - if a string - check for "!ref" and "!file" prefix and resolve references if needed;
        - otherwise - return value as is.

        Args:
            value (Any): value to resolve.
            context_str (str | None): context descriptor (parent node), used for
            error reporting.

        Returns:
            Any: resolved value.
        """
        self.__stack_nodes.append(context_str)

        match type(value):
            case builtins.dict:
                for key, item_value in value.items():
                    value[key] = self._resolve(item_value, key)

            case builtins.list:
                value = [self._resolve(element, str(i))
                         for i, element in enumerate(value)]

            case builtins.str:
                if Pointer.match_ref_pointer(value):
                    value = self._resolve_reference(value)
                elif Pointer.match_file_ref_pointer(value):
                    value = self._resolve_file_reference(value)

        self.__stack_nodes.pop()
        return value

    def _resolve_reference(self, ptr: str) -> str|dict|list|int|float|None:
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

        if ptr in self.__ref_cache:
            return self.__copy_value(self.__ref_cache[ptr])

        self.__check_for_recursion(ptr, context_is_ref=True)
        self.__stack.append(ptr)

        try:
            value = self.content.get(ptr)
        except KeyError as err:
            err.add_note(f'Failed to resolve reference "{ptr}" - '
                         f'key "{err.args[0]}" does not exists!\n'
                         f'{self.__get_nodepath_msg()}')
            raise err

        # Reference may point to a another reference or to a file, or nested ref/file.
        # Therefore - resolve data before return
        print('Resolving values from reference "%s"', ptr)
        value = self._resolve(value, f'<by ref>{ptr}')

        self.__ref_cache[ptr] = value
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

        if ptr in self.__file_cache:
            return self.__copy_value(self.__file_cache[ptr])

        self.__check_for_recursion(ptr)
        self.__stack.append(ptr)

        # File may contain references or file references, or/and nested ref/file.
        # Therefore - resolve data before return.
        print('Read values from file "%s"', ptr)
        try:
            content = DataReader.read_json_from_file(ptr.pointer)
        except Exception as err:
            err.add_note(self.__get_nodepath_msg())
            raise err

        print('Resolving values from reference "%s"', ptr)
        content = self._resolve(content, '<from file>')

        self.__file_cache[ptr] = content
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
        return f'Problem occured on parsing key "{REF_SEP.join(self.__stack_nodes)}"'

    @staticmethod
    def __copy_value(value: Any):
        """Makes deepcopy of mutable JSON value (dict or list)

        Args:
            value (Any): value to copy.

        Returns:
            Any: copy (if value is mutable) of value or value
        """
        return copy.deepcopy(value) if isinstance(value, (dict, list)) else value
