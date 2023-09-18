"""Basic classes for matchers"""
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass


from utils.basic_manager import BasicManager

# --- Manager ---
# ---------------
class MatchersManager(BasicManager):
    """Class to register and provide access to matcher objects from various points
    in the framework (e.g. for compiler procedures).
    """
    matchers = []

    def __init__(self, include_known_matchers: bool = True):
        """Creates instance of Matchers Manager class.

        Args:
            include_known_matchers (bool, optional): Flag to automatically register all
            known matchers to collection. Known matchers are matchers inherited from
            BaseMatcher. Defaults to True.
        """
        super().__init__()
        if include_known_matchers:
            self.add_all(MatchersManager.matchers)

    def add(self, item: 'BaseMatcher', name: str | None = None, override: bool = False):
        """Registers given matcher under given name.

        Args:
            matcher (AbstractMatcher): matcher class.
            name (str, optional): registration name. Defaults to class.__name__.

        Raises:
            ValueError: when name already occupied.
        """
        return super().add(item, name, override)

    def add_all(self, items: tuple['BaseMatcher', str] | list['BaseMatcher'],
                override: bool = False):
        """Registers given collection of matchers.

        Args:
            matchers (list | tuple): collection of matchers where each element is
            'class<cls>' or ('class<cls>', 'name<str>').
        """
        return super().add_all(items, override)

    def get(self, name: str, args:tuple=(), kwargs:dict=None) -> 'BaseMatcher':
        """Creates an instance of registerd matcher object by it's name and
        with given args/kwargs.

        Args:
            name (str): registered name of the matcher.
            args (tuple, optional): matcher's constructor arguments. Defaults to ().
            kwargs (dict, optional): matcher's constructor keyword arguments.
            Defaults to None.

        Raises:
            ValueError: when given name is not found.

        Returns:
            AbstractMatcher: instance of `AbstractMatcher` class implementation
        """
        if name not in self.collection:
            raise ValueError(f'Failed to find matcher with name "{name}"!')

        if kwargs is None:
            kwargs = {}
        matcher_cls = self.collection[name]
        matcher = matcher_cls(*args, **kwargs)
        return matcher

    def _check_type_on_add(self, item: typing.Any):
        """Raises exception, if given item have unexpected type."""
        if issubclass(item, BaseMatcher):
            return

        raise ValueError(f'Registraion failed for item "{item}" at {self.__class__.__name__}. '
                         f'Only subclass items of class "{BaseMatcher.__name__}" '
                         f'are allowed!')


# --- Base Matcher class ---
# --------------------------
@dataclass(frozen=True, eq=False, repr=False)
class BaseMatcher(ABC):
    """Abstract Matcher to any value"""

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        MatchersManager.matchers.append(cls)

    def __post_init__(self):
        # Validates values against fields typing
        # pylint: disable=no-member, protected-access
        not_matching_fields = []
        for field in self.__dataclass_fields__.values():
            if isinstance(field.type, (typing._SpecialForm, type(typing.Any))):
                # Ignore Any and typing of SpecialForm (parameterless Union, ClassVar)
                continue

            field_type = field.type
            origin = typing.get_origin(field_type)
            if origin:
                # Skip stuff like classvar
                if isinstance(origin, (typing._SpecialForm, type(typing.Any))):
                    continue
                # For unions - type is a tuple
                field_type = typing.get_args(field_type)
                if typing.Any in field_type:
                    continue

            value = getattr(self, field.name)
            if not isinstance(value, field_type):
                value_repr = f'"{value}"' if isinstance(value, str) else str(value)
                not_matching_fields.append(
                    f'"{field.name}" = {value_repr} ({type(value)}) doesn\'t '
                    f'match expected type(s) {field_type}'
                )

        # pylint: enable=no-member, protected-access
        if not_matching_fields:
            details = ',\n - '.join(not_matching_fields)
            raise TypeError("Matcher initialized with invalid types of parameters:\n - "
                            f"{details}")

    @abstractmethod
    def __eq__(self, other):
        return True

    @abstractmethod
    def __repr__(self):
        return ''

    @staticmethod
    @abstractmethod
    def assertrepr_compare(left, right) -> list[str]:
        """Return full list of string as explanation of why values are not equal"""
        return []

    @staticmethod
    @abstractmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        """Return shortened list of string as explanation of why values are not equal"""
        return []

    @staticmethod
    def shorten_repr(list_or_dict):
        """Helper method to shorten object repr in
        assertrepr_compare_brief method output"""
        repr_str = repr(list_or_dict)
        if isinstance(list_or_dict, (list, dict)) and len(repr_str) > 55:
            repr_str = f'{repr_str[:35]} ...{repr_str[-20:]}'
        return repr_str

@dataclass(frozen=True, eq=False, repr=False)
class Anything(BaseMatcher):
    """Matches to any value"""
    def __eq__(self, other):
        return other is not None

    def __repr__(self):
        return '<Any>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Anything matcher:",
            f"{BaseMatcher.shorten_repr(left)} != {right}"
        ]
        output.extend(Anything.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return ['Value is None, but expecte to be anything']
