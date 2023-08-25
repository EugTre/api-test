"""Tiny wrapper class to handle collection of items and provide
access point to it"""
from typing import Any

class BasicManager():
    """Basic manager to handle collection of items and provide way
    to add, remove and access item by some registration name."""
    def __init__(self) -> None:
        self.collection = {}

    def add(self, item: Any, name: str|None = None, override: bool = False):
        """Registers given item under given name.

        Args:
            item (Any): class, instance or callable.
            name (str, optional): registration name. Defaults to item.__name__.
            override (bool, optional): flag to override already registered names.
            Defaults to False.

        Raises:
            ValueError: when name already occupied.
        """
        self._check_type_on_add(item)

        name = name if name else self.__exctract_name(item)
        if name in self.collection and not override:
            raise ValueError(f'"{name}" already registered!')

        self.collection[name] = item

    def add_all(self, items: tuple[Any, str|None]|list[Any, str|None],
                override: bool = False):
        """Registers given colelction of items.

        Args:
            items (tuple | list): collection of
            (class/instance/callable, registration name) pairs.
            override (bool, optional): flag to override already registered names.
            Defaults to False.

        Raises:
            ValueError: when name already occupied.
        """
        for item in items:
            if isinstance(item, (tuple, list)):
                self.add(override=override, *item)
            else:
                self.add(item, override=override)

    def remove(self, item: Any) -> bool:
        """Removes (unregister) item by given name.

        Args:
            name (str): name of the item in collection.

        Returns:
            bool: True if item was removed, False if
            there is no item found by given name.
        """
        name = self.__exctract_name(item)

        if name not in self.collection:
            return False

        del self.collection[name]
        return True

    def _check_type_on_add(self, item: Any):
        """Raises exception, if given item have unexpected type."""

    def __contains__(self, item):
        return self.__exctract_name(item) in self.collection

    def __exctract_name(self, item: Any):
        """Exctracts name if given item is not a string"""
        if isinstance(item, str):
            return item
        return item.__name__
