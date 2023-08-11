"""Wrapper for JSON content. Provides easy content editing,
including inner content and external file references."""

import copy

from typing import Self, Any
from utils.data_reader import DataReader
from utils.json_content.json_content_wrapper import AbstractContentWrapper, JsonContentWrapper
from utils.json_content.reference_resolver import AbstractReferenceResolver, ReferenceResolver
from utils.json_content.pointer import ROOT_POINTER

class JsonContent:
    """Class to wrap JSON with get/update/delete methods and
    reference resolution mechanism"""
    __slots__ = ["content", "resolver"]

    def __init__(self, content: dict|list,
                 allow_references: bool = False,
                 enable_cache: bool = False,
                 wrapper: AbstractContentWrapper = JsonContentWrapper,
                 resolver: AbstractReferenceResolver = ReferenceResolver
                ):
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

        self.content: AbstractContentWrapper = wrapper(content)
        self.resolver: AbstractReferenceResolver = None
        if allow_references:
            self.resolver = resolver(self.content, enable_cache)
            self.resolver.resolve_all()

    def has(self, pointer: str) -> bool:
        """Checks that property presents in the content.
        Returns True if pointer refers to existing property.

        Args:
            pointer (str): JSON pointer to a property as string.

        Returns:
            bool: True if property presents, otherwise False.
        """
        return self.content.has(pointer)

    def get(self, pointer: str = ROOT_POINTER, make_copy: bool = False) -> Any:
        """Returns property at given pointer.

        Args:
            pointer (str, optional): JSON pointer to a property as string.
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

    def get_or_default(self, pointer: str, default_value: Any, make_copy: bool = False) -> Any:
        """Returns property at given pointer or default_value
        if property is not present.

        Args:
            pointer (str): JSON pointer to a property as string.
            default_value (Any): value to fallback to.
            make_copy (bool, optional): Flag to return a copy of the mutable property.
            Defaults to False.

        Returns:
            Any: property's value or 'default_value'
        """
        value = self.content.get_or_default(pointer, default_value)
        return self.__copy_value(value) if make_copy else value

    def update(self, pointer: str, value: Any) -> Self:
        """Updates or add content to wrapped JSON structure.
        If end key is not exists - it will be added with new value,
        but non-existent keys in the middle cause KeyError exception.
        On update of a list one can use:
        - element index in range of list (starts from 0)
        - element's negative index in range of list (e.g. -1 means last element)
        - append char "-" to add new element in the end

        Args:
            pointer (str): JSON pointer to a property as string.
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

        if self.resolver is not None:
            value = self.resolver.resolve(value, '<update>')
        self.content.update(pointer, value)
        return self

    def delete(self, *pointers: str) -> Self:
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

    def invalidate_cache(self) -> Self:
        """Invalidate cache of underlaying ReferenceResolver.

        Returns:
            Self: instance of `JsonContent` class
        """
        self.resolver.invalidate_cache()

    def __str__(self):
        return str(self.content.get(ROOT_POINTER))

    def __eq__(self, other):
        if isinstance(other, JsonContent):
            return self.content.get(ROOT_POINTER) == other.content.get(ROOT_POINTER)

        if isinstance(other, dict|list):
            return self.content.get(ROOT_POINTER) == other

        return False

    def __contains__(self, pointer: str):
        if not isinstance(pointer, str):
            return False
        return pointer in self.content

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

    __slots__ = ["__content", "__allow_reference_resolution",
                 "__enable_reference_cache", "__wrapper_cls", "__resolver_cls"]

    def __init__(self):
        self.__content = {}
        self.__allow_reference_resolution = False
        self.__enable_reference_cache = False
        self.__wrapper_cls = JsonContentWrapper
        self.__resolver_cls = ReferenceResolver

    def build(self) -> JsonContent:
        """Creates instance of `JsonContent` class with desired setup."""
        return JsonContent(content=self.__content,
                            allow_references=self.__allow_reference_resolution,
                            enable_cache=self.__enable_reference_cache,
                            wrapper=self.__wrapper_cls,
                            resolver=self.__resolver_cls)

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

    def set_reference_policy(self, allow: bool, cache: bool) -> Self:
        """Sets policy of reference handling. If references allowed (`allow` = True),
        values like '!ref /a/b' or '!file file.json' will be considered as references,
        and will be resolved to actual values (e.g. !ref /a/b will be replaced
        with value at pointer /a/b of content; for file - file content fill be read
        and placed as value).

        If `cache` is set to True: resolved references will be saved and if the same
        reference occures once again - it will be instantly resolved to the very
        same value (copy will be used).
        Use it when your content refers to the same file or value.

        Args:
            allow (bool): allow reference resolution.
            cache (bool): allow caching of resolved references.

        Returns:
            Self: builder instance.
        """
        self.__allow_reference_resolution = allow
        self.__enable_reference_cache = cache
        return self

    def set_wrapper(self, wrapper: AbstractContentWrapper) -> Self:
        """Sets preferred wrapper class.
        Wrapper is a class inherited from `AbstractContentWrapper`
        that's provide get, update and delete methods to access actual
        content by JSON pointer.

        By default `json_content.json_content_wrapper.JsonContentWrapper`
        will be used.

        Args:
            wrapper (AbstractContentWrapper): _description_

        Returns:
            Self: _description_
        """
        self.__wrapper_cls = wrapper
        return self

    def set_resolver(self, resolver: AbstractReferenceResolver) -> Self:
        """Sets preferred reference resolver class.
        Reference resolver is a class inherited from `AbstractReferenceResolver`
        that's provide resolve method to resolve reference values in actual data.

        By default `json_content.reference_resolver.ReferenceResolver`
        will be used.

        Args:
            wrapper (AbstractContentWrapper): _description_

        Returns:
            Self: _description_
        """
        self.__resolver_cls = resolver
        return self
