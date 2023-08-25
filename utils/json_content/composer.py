"""Helper class to resolve !ref and !file references in JSON structures."""
import copy
from typing import Any, Type

from utils.json_content.pointer import Pointer
from utils.json_content.json_wrapper import JsonWrapper
from utils.json_content.composition_handlers import CompositionHandler, \
    DEFAULT_COMPOSITION_HANDLERS_COLLECTION

HANDLER_CONTEXT_KEY = "content_context"

class Composer:
    """Class to compose content by resolving references, generating values
    in given `AbstractContentWrapper` object."""

    __slots__ = ["content", "handlers", "_target_nodes", "__stack_nodes"]

    def __init__(self,
                 content_context: JsonWrapper,
                 handlers: dict[Type[CompositionHandler], dict]|None = None):
        """Creates an instance of `ReferenceResolver` class.

        Args:
            content_context (JsonWrapper): content wrapper to compose.
            handlers (dict[Type[CompositionHandler], dict] | None, optional): collection
            of handlers classes and their parameters to use. Defaults to
            'DEFAULT_COMPOSITION_HANDLERS_COLLECTION' from
            `utils.json_content.compositionhandlers`.

            Note that if handler parameter "content_context" is set to None, Composer's
            content_context will be passed to handler isntead.

            Handlers example
            ```
            {
                CompositionHandler1: {
                    "kwarg1": ...,
                    "kwarg2": ...
                },
                ...
            }
            ```
        """
        self.content: JsonWrapper = content_context
        self.handlers: list[CompositionHandler] = []

        # Instantiate handlers
        if handlers is None:
            handlers = DEFAULT_COMPOSITION_HANDLERS_COLLECTION

        for handler, handler_kwargs in handlers.items():
            # Provide content context to handler requesting it.
            # Copy before change, as dicts passed by reference, and direct change will
            # change handlers list forevery other composer created after
            if HANDLER_CONTEXT_KEY in handler_kwargs and \
                    handler_kwargs[HANDLER_CONTEXT_KEY] is None:

                handler_kwargs = copy.deepcopy(handler_kwargs)
                handler_kwargs[HANDLER_CONTEXT_KEY] = content_context

            try:
                handler_instance = handler(**handler_kwargs)
            except Exception as err:
                err.add_note('Error occured on Json Content Composer instance creation, '
                             'during composition handlers preparation.')
                raise
            self.handlers.append(handler_instance)

        self._target_nodes: list[Pointer] = None
        self.__stack_nodes = []

    def compose_content(self, node_pointer: Pointer|str = ''):
        """Scans content and converts every composition met to a value.

        Method start loop and checks required nodes for compositions.
        Once found - compositions handled and converted to some
        value, then on next pass changed nodes will be checked again.
        This allows chain referencing and ensures, that referencing to
        nodes that only expected to be composed won't cause parsing errors.

        Exception is raised if in the end of the pass there are:
        - still nodes to check presents
        - and list of the nodes is the same as before current pass
        - and no changes was made to a content.

        Args:
            node_pointer (Pointer | str, optional): pointer to a node
            that should be composed. Defaults to '' (entire content).

        Raises:
            RuntimeError: when some composition cannot be resolved (e.g.
            recursion reference)
        """
        if isinstance(node_pointer, str):
            node_pointer = Pointer.from_string(node_pointer)

        self._target_nodes = [node_pointer]

        while self._target_nodes:
            nodes = self._target_nodes
            self._target_nodes = []
            values_changed = False

            for node_ptr in nodes:
                current_value = self.content.get(node_ptr)
                new_value = self.scan_and_compose_values(current_value, node_ptr.path)
                if current_value != new_value:
                    self.content.update(node_ptr, new_value)
                    values_changed = True

            # If revisited nodes weren't updated on previous pass and there are still
            # nodes to revisit, then something gone wrong -- recursive reference?
            if not values_changed and self._target_nodes and self._target_nodes == nodes:
                nodes_info = '\n'.join([
                    f'- node: "{node}", current value: {self.content.get(node)}'
                    for node in self._target_nodes])
                raise RuntimeError('Unresolved errors occured during content composition '
                    'for nodes:\n'
                    f'{nodes_info}.\n'
                    'Please, ensure that compositions used in given nodes are valid!\n'
                    'Possible problems:\n'
                    '- referencing to non-existent nodes;\n'
                    '- recursion references;\n'
                    '- unresolvable order of referencing, etc.')

    def scan_and_compose_values(self, value: Any, node_context: str|tuple|None) -> Any:
        """Recursively scans deep into given collection and search for compositions.
        When found - composes it to value and updates content.
        Returns resulting value or untouched value, if no composition was found.

        Args:
            value (Any): value to scan/compose.
            node_context (str | tuple | None): parent node descriptor to track context.

        Returns:
            Any: resolved value.
        """

        if not isinstance(value, (dict, list)):
            return value

        self.__append_node_stack(node_context)

        if isinstance(value, dict):
            handler: CompositionHandler = self._look_for_handler(value)
            if handler:
                # Composition will be resolved into values
                value = self._handle_composition(handler, self.__get_current_node_pointer(), value)
            else:
                # Loop through dict keys and try to compose their values
                for key, item_value in value.items():
                    self._process_nested_element(key, item_value)

        elif isinstance(value, list):
            # Loop through list elements and try to compose them
            for i, item_value in enumerate(value):
                self._process_nested_element(str(i), item_value)

        self.__pop_node_stack()

        return value

    def _process_nested_element(self, key, value):
        """Scans value at given key and updates if needed."""
        new_value = self.scan_and_compose_values(value, key)
        if new_value != value:
            self.content.update(
                self.__get_current_node_pointer(key),
                new_value
            )

    def _look_for_handler(self, obj: dict):
        """Checks given dict to be a composition compatible to some handler"""
        for handler in self.handlers:
            if handler.match(obj):
                return handler

        return None

    def _handle_composition(self, handler: CompositionHandler, pointer: Pointer, composition: dict):
        """Converts composition into a value, handling additional logic to track changed nodes"""
        try:
            composition_result, result_value = handler.compose(composition)
        except Exception as err:
            err.add_note(f'Error occured on composing value at pointer "{pointer}".')
            raise err

        if not composition_result:
            # On error - register problematic node and return untouched value
            self._target_nodes.append(pointer)
            return composition

        # On success - return new value, but if value is dict/list - register
        # current node for re-visit (in case there are nested compositions may be found)
        if isinstance(result_value, (list, dict)):
            self._target_nodes.append(pointer)

        return result_value

    def __get_current_node_pointer(self, key: str|int|None = None) -> Pointer:
        """Returns Pointer of currently scanned node"""
        path = [*self.__stack_nodes, str(key)] if key is not None else self.__stack_nodes
        return Pointer.from_path(path)

    def __append_node_stack(self, node: str|tuple|None):
        """Sets or update node stack"""
        if node is None:
            self.__stack_nodes = []
        elif isinstance(node, tuple):
            self.__stack_nodes = list(node)
        else:
            self.__stack_nodes.append(node)

    def __pop_node_stack(self):
        """Removes last node from the node stack"""
        if not self.__stack_nodes:
            return
        self.__stack_nodes.pop()
