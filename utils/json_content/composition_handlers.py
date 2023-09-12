"""Composition handlers provide various classes that able to convert
JSON nodes of specifc structure into specific values (e.g. value by reference,
generated value, etc.)"""
import json
import copy
import pathlib
from typing import Any
from abc import ABC, abstractmethod
from enum import Enum

from utils.data_reader import DataReader
from utils.matchers import MatchersManager, matchers_manager
from utils.generators import GeneratorsManager, generators_manager

from .json_wrapper import JsonWrapper
from .pointer import Pointer


class CompositionStatus(Enum):
    """Status of the composition after handling"""

    # Composition processed and futher handling is allowed
    SUCCESS = 0
    # Composition failed to process, need to retry later
    RETRY = 10
    # Composition is fully processed and should never be processed again
    COMPLETED = 20
    # Result of composition should be processed in custom context before
    # mergin data to main content
    COMPOSE_IN_SEPARATE_CONTEXT = 21


class CompositionHandler(ABC):
    """Handler provide logic to convert composition object
    to specific value"""
    DEFINITION_KEY: str = ""

    def match(self, obj: dict) -> bool:
        """Returns True if given dict object is compatible with handler.

        Args:
            obj (dict): dictionary object to check.

        Returns:
            bool: True if object may be handled.
        """
        return self.DEFINITION_KEY in obj

    @abstractmethod
    def compose(self, obj: dict) -> tuple[CompositionStatus, Any]:
        """Transform object into definite value.

        Args:
            obj (dict): dictionary object to check.

        Returns:
            tuple[CompositionStatus, Any]: result of processing and composed value.
        """

    @staticmethod
    def _copy_value(value: Any):
        """Makes deepcopy of mutable JSON value (dict or list)

        Args:
            value (Any): value to copy.

        Returns:
            Any: copy (if value is mutable) of value or value
        """
        return copy.deepcopy(value) if isinstance(value, (dict, list)) else value


class ReferenceCompositionHandler(CompositionHandler):
    """Handles reference to JSON node.
    Returns value by JSON Pointer.

    Reference syntax:
    `{"!ref": "/path/to/node"}

    Should be instantiated with `utils.json_content.json_wrapper.JsonWrapper` instance,
    to provide context for reference resolution.
    """
    DEFINITION_KEY = "!ref"

    def __init__(self, content_context: JsonWrapper):
        self.content_context: JsonWrapper = content_context

    def compose(self, obj: dict) -> Any:
        try:
            pointer: Pointer = Pointer.from_string(obj[self.DEFINITION_KEY])
            if pointer.path is None:
                raise ValueError("Referencing to document root is not allowed!")
        except Exception as err:
            err.add_note(f'Error occured on composing Reference Composition {json.dumps(obj)}.')
            raise

        if pointer not in self.content_context:
            return CompositionStatus.RETRY, None

        value = self.content_context.get(pointer)
        return CompositionStatus.SUCCESS, self._copy_value(value)


class FileReferenceCompositionHandler(CompositionHandler):
    """Handles file references.
    Returns JSON content of the file as dict or list for futher processing
    by composer.

    File referense composition syntax:
    `{"!file": "path/to/file.ext"}`

    Should be instantiated with `use_cache` bool flag to enable/disable
    file content cache.
    """
    DEFINITION_KEY = "!file"
    CONTEXT = "<file content>{file_path}"

    def __init__(self, use_cache: bool = False):
        self.use_cache = use_cache
        self.cache = {} if use_cache else None

    def compose(self, obj: dict) -> Any:
        path = obj[self.DEFINITION_KEY]

        if self.use_cache and path in self.cache:
            # Return copy to avoid modification by reference
            return CompositionStatus.SUCCESS, self._copy_value(self.cache[path])

        try:
            content = DataReader.read_from_file(path)
        except Exception as err:
            err.add_note('Error occured on composing File '
                         f'Reference Composition {json.dumps(obj)}.')
            raise

        if self.use_cache:
            # Save copy as content may be changed afterwards
            self.cache[path] = self._copy_value(content)

        return CompositionStatus.SUCCESS, content


class IncludeFileCompositionHandler(CompositionHandler):
    """Handles file references.
    Returns content of the file depending on it's extension or given '!format'.
    For JSON - parses using 'json' lib. Otherwise return content as text, or
    as parsed int/float/bool.

    Include File composition syntax:
    `{
        "!include": "path/to/file.ext",
        "!compose": True/False,
        "!format": "json"/"txt"
    }`

    Params:
        "!include" (str) - path to file.
        "!compose" (optional, bool) - flag to compose file content before including
        to it's data to parent document. Defaults to False.
        "!format" (optional, str) - explicit file format definition as lower case.
        If not set - uses file extension.

    Should be instantiated with `use_cache` bool flag to enable/disable
    file content cache.
    """
    DEFINITION_KEY = "!include"
    COMPOSE_KEY = "!compose"
    FORMAT_KEY = "!format"

    CONTEXT = "<include content>{file_path}"
    ERROR_HINT = 'Error occured on Including File Composition {composition}.'

    def __init__(self, use_cache: bool = False):
        self.use_cache = use_cache
        self.cache = {} if use_cache else None

    def compose(self, obj: dict) -> Any:
        path = pathlib.Path(obj[self.DEFINITION_KEY])
        compose = obj.get(self.COMPOSE_KEY, False)
        data_format = obj.get(self.FORMAT_KEY)

        handling_result = CompositionStatus.COMPOSE_IN_SEPARATE_CONTEXT \
            if compose else CompositionStatus.COMPLETED

        if self.use_cache and path in self.cache:
            # Return copy to avoid modification by reference
            return handling_result, self._copy_value(self.cache[path])

        content = None
        try:
            content = DataReader.read_from_file(path, data_format)
        except Exception as err:
            err.add_note(self.ERROR_HINT.format(composition=json.dumps(obj)))
            raise

        if self.use_cache:
            # Save copy as content may be changed afterwards
            self.cache[path] = self._copy_value(content)

        return handling_result, content


class GeneratorCompositionHandler(CompositionHandler):
    """Handles data generation composition.
    Returns generated data.

    Some value will be generated by given generator and args.
    If "!id" is given - same value will be returned for all compositions
    with the same generator name and id.

    All keys except "!gen", "!args" and "!id" will be passed to generator as
    keyword arguments.

    Composition syntax:
    ```
    {
        "!gen": "GeneratorName",
        "!args": [...],
        "!id": "generation_id",
        "keyword_arg1": ...,
        ...
    }
    ```

    Should be instantiated with `utils.generators.GeneratorsManager` instance, containing
    generators collection.
    """
    DEFINITION_KEY = "!gen"
    ARGS_KEY = "!args"
    ID_KEY = "!id"

    def __init__(self, manager: GeneratorsManager) -> None:
        self.manager = manager

    def compose(self, obj: dict) -> tuple[bool, Any]:
        name = obj[self.DEFINITION_KEY]
        args = obj.get(self.ARGS_KEY, tuple())
        kwargs = dict((
            (key, obj[key])
            for key in obj
            if key not in (self.DEFINITION_KEY, self.ARGS_KEY, self.ID_KEY)
        ))
        correlation_id = obj.get(self.ID_KEY, None)

        try:
            value = self.manager.generate(name, args, kwargs, correlation_id)
        except Exception as err:
            err.add_note(f"Error occured on composing Generator Composition {json.dumps(obj)}.")
            raise

        return CompositionStatus.SUCCESS, value


class MatcherCompositionHandler(CompositionHandler):
    """Handles matchers compostion.
    Creates and returns matcher.

    Matcher will be instantiated by given name ("!match") and with given args ("!args").

    Other keys except "!match" and "!args" will be passed to matcher as
    keyword arguments.

    Composition syntax:
    ```
    {
        "!match": "MatcherName",
        "!args": [...],
        "keyword_arg1": ...,
        ...
    }
    ```

    Should be instantiated with `utils.matcher.MatchersManager` instance, containing
    matchers collection.
    """
    DEFINITION_KEY = "!match"
    ARGS_KEY = "!args"

    def __init__(self, manager: MatchersManager):
        self.manager = manager

    def compose(self, obj: dict) -> tuple[bool, Any]:
        name = obj[self.DEFINITION_KEY]
        args = obj.get("!args", tuple())
        kwargs = dict((
                            (key, obj[key])
                            for key in obj.keys()
                            if key not in (self.DEFINITION_KEY, self.ARGS_KEY)))

        try:
            matcher = self.manager.get(name, args=args, kwargs=kwargs)
        except Exception as err:
            err.add_note(f"Error occured on composing Matcher Composition {json.dumps(obj)}.")
            raise

        return CompositionStatus.SUCCESS, matcher


# Default collection of handlers.
# Keys - classes of the handlers,
# Values - handlers __init__ keyword arguments (**kwargs).
#
# May be updated from anywhere by standard dict methods
DEFAULT_COMPOSITION_HANDLERS_COLLECTION: dict[CompositionHandler, dict[str, Any]] = {
	ReferenceCompositionHandler: {"content_context": None},
    FileReferenceCompositionHandler: {"use_cache": False},
    IncludeFileCompositionHandler: {"use_cache": False},
    GeneratorCompositionHandler: {"manager": generators_manager},
    MatcherCompositionHandler: {"manager": matchers_manager}
}
