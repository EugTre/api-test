"""Wrapper for JSON content. Provides easy content editing,
including inner content and external file references."""

import copy

from typing import Self, Any
from utils.data_reader import DataReader
from utils.json_content.json_wrapper import JsonWrapper
from utils.json_content.composer import Composer

from utils.json_content.pointer import Pointer, ROOT_POINTER
from utils.json_content.composition_handlers import DEFAULT_COMPOSITION_HANDLERS_COLLECTION

class JsonContent:
    """Class to wrap JSON with get/update/delete methods and
    reference resolution mechanism"""
    __slots__ = ["content", "composer"]

    def __init__(self, content: dict|list, composer_setup: dict = None):
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
            wrapper (AbstractContentWrapper, optional): Content wrapper class to
            use for content wrapping. Defaults to JsonContentWrapper.
        """
        if content is None:
            content = {}

        if not isinstance(content, (dict, list)):
            raise ValueError('Content must be JSON-like of type dict or list! '
                             f'Given value is {type(content)}.')

        self.content = JsonWrapper(content)
        self.composer = None
        if composer_setup is not None:
            self.composer = Composer(self.content, handlers=composer_setup)
            self.composer.compose_content()

    def get(self, pointer: str|Pointer = ROOT_POINTER, make_copy: bool = False) -> Any:
        """Returns property at given JSON pointer.

        Args:
            pointer (str|Pointer, optional): JSON pointer to a property as string.
            Defaults to empty (return whole content).
            make_copy (bool, optional): Flag to return a copy of the mutable property.
            Defaults to False.

        Raises:
            IndexError: on attempt to get element of list by out of bound index.
            KeyError: when pointer uses non-existent node.

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

    def get_or_default(self, pointer: str|Pointer,
                       default_value: Any, make_copy: bool = False) -> Any:
        """Returns property at given pointer or default_value
        if property is not present.

        Args:
            pointer (str|Pointer): JSON pointer to a property as string.
            default_value (Any): value to fallback to.
            make_copy (bool, optional): Flag to return a copy of the mutable property.
            Defaults to False.

        Returns:
            Any: property's value or 'default_value'
        """
        value = self.content.get_or_default(pointer, default_value)
        return self.__copy_value(value) if make_copy else value

    def update(self, pointer: str|Pointer, value: Any) -> Self:
        """Updates or add content to wrapped JSON structure.
        If end key is not exists - it will be added with new value,
        but non-existent keys in the middle cause KeyError exception.
        On update of a list one can use:
        - element index in range of list (starts from 0) - '/a/b/0'
        - append char "-" to add new element in the end - /a/b/-'

        Args:
            pointer (str|Pointer): JSON pointer to a property as string.
            value (Any): New value to set. May be a '!ref' or '!file' pointer which
            will be resolved before updating content.

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
            "a": {"nested": 100}
            "b": [1,2,3]
        })
        #  Node update:
        ctn.update("/a/nested", 20)
        ctn.update("/b/0", 20)
        # Node add
        ctn.update("/a/new", 40)
        ctn.update("/b/-", 40)
        # Result:
        {
            "a": {
                "nested": 20,
                "new": 40
            }
            "b": [20, 2, 3, 40]
        }
        """

        self.content.update(pointer, value)
        if self.composer is not None:
            self.composer.compose_content(pointer)

        return self

    def delete(self, *pointers: str|Pointer) -> Self:
        """Deletes node at given pointer or several nodes, if list
        of pointers was given.
        No error will be raised if desired node doesn't exists.

        Node deletion - Args:
            pointers (str): JSON pointers to a property as strings. Pointer may be
            root ('/') - entire JSON structure will be cleared.

        Bulk deletion - Args:
            pointers (list | tuple): iterable of pointers.

        Returns:
            Self: instance of `JsonContent` class
        """
        for ptr in pointers:
            self.content.delete(ptr)

        return self

    def __str__(self):
        return str(self.content.get(ROOT_POINTER))

    def __eq__(self, other):
        if isinstance(other, JsonContent):
            return self.content.get(ROOT_POINTER) == other.content.get(ROOT_POINTER)

        if isinstance(other, dict|list):
            return self.content.get(ROOT_POINTER) == other

        return False

    def __contains__(self, pointer: str|Pointer):
        if not isinstance(pointer, (str, Pointer)):
            return False
        return pointer in self.content

    def __iter__(self):
        return self.content.__iter__()

    @staticmethod
    def __copy_value(value: Any):
        """Makes deepcopy of mutable JSON value (dict or list)

        Args:
            value (Any): value to copy.

        Returns:
            Any: copy (if value is mutable) of value or value
        """
        return copy.deepcopy(value) if isinstance(value, (dict, list)) else value

class JsonContentBuilder:
    """Builder class to create and setup isntnace of JsonContent.

    By default:
        - Content is empty dict = {};
        - Reference resolution is disabled;
        - Reference cache is disabled;
        - Wrapper class is `json_content.json_content_wrapper.JsonContentWrapper`;
        - Reference resolver is `json_content.reference_resolver.ReferenceResolver`.

    """

    __slots__ = ["__content", "__use_composer",
                 "__composer_handlers",]

    def __init__(self):
        self.__content = {}
        self.__use_composer = False
        self.__composer_handlers = None

    def build(self) -> JsonContent:
        """Creates instance of `JsonContent` class with desired setup."""
        return JsonContent(
            content=self.__content,
            composer_setup=(self.__composer_handlers if self.__use_composer else None)
        )

    def from_data(self, content: dict|list, make_copy: bool = False) -> Self:
        """Sets source of data for JsonContent object - variable or literal.

        Args:
            content (dict | list): data to wrap by JsonContent.
            make_copy (bool, optional): Flag to use a deep copy of data. Defaults to False.

        Returns:
            Self: builder instance
        """
        self.__content = copy.deepcopy(content) if make_copy else content
        return self

    def from_file(self, filepath: str) -> Self:
        """Reads content data for JsonContent object from given JSON file.

        Args:
            filepath (str): path to file with JSON content.

        Returns:
            Self: builder instance.
        """
        self.__content = DataReader.read_json_from_file(filepath)
        return self

    def use_composer(self, use: bool = True, handlers: dict = None) -> Self:
        """Enable compsoer for instance of JsonWrapper

        Args:
            use (bool, optional): flag to enable/disable compsoer. Defaults to True.
            handlers (dict, optional): configuration of handlers as dict, where keys - class names
            of the handles and values - dict of kwargs for handler constructor.
            Defaults to DEFAULT_COMPOSITION_HANDLERS_COLLECTION.

        Returns:
            Self: builder instance.
        """
        self.__use_composer = use

        if use:
            if handlers is None:
                handlers = DEFAULT_COMPOSITION_HANDLERS_COLLECTION
            self.__composer_handlers = handlers

        return self
