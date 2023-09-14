"""Module provides matche object of various kinds"""
import re
import typing
import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod

import pytest
from _pytest.assertion.util import assertrepr_compare

from utils.basic_manager import BasicManager

# --- Manager
class MatchersManager(BasicManager):
    """Class to register and provide access to matcher objects from various points
    in the framework (e.g. for compiler procedures).
    """
    matchers = []

    def __init__(self, include_known_matchers: bool = True):
        super().__init__()
        if not include_known_matchers:
            return
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

# --------
# Matcher classes
# --------

def shorten_repr(list_or_dict):
    """Helper method to shorten object repr in
    assertrepr_compare_brief method output"""
    repr_str = repr(list_or_dict)
    if isinstance(list_or_dict, (list, dict)) and len(repr_str) > 55:
        repr_str = f'{repr_str[:35]} ...{repr_str[-20:]}'
    return repr_str

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
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(Anything.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return ['Value is None, but expecte to be anything']


# --------
# Text
# --------
@dataclass(frozen=True, eq=False, repr=False)
class AnyText(BaseMatcher):
    """Matches to any text (string), including empty string"""
    def __eq__(self, other):
        return isinstance(other, (str, Anything, AnyText))

    def __repr__(self):
        return '<Any Text>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Text matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyText.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return [
            'Type mismatch:',
            f'{type(left)} != {type("")}'
        ]

@dataclass(frozen=True, eq=False, repr=False)
class AnyTextLike(AnyText):
    """Matches to any text (string) that matches to given regex"""
    pattern: str
    case_sensitive: bool = False

    def __eq__(self, other):
        if isinstance(other, (Anything, AnyText)):
            return True

        return isinstance(other, str) and re.match(
            self.pattern, other, re.NOFLAG if self.case_sensitive else re.IGNORECASE)

    def __repr__(self):
        return f'<Any Text Like "{self.pattern}", ' \
               f'case {"" if self.case_sensitive else "in"}sensitive>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Text Like matcher:",
            f'{shorten_repr(left)} != {right}'
        ]
        output.extend(AnyTextLike.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        if not isinstance(left, str):
            return [
                'Type mismatch:',
                f'Type {type(left)} doesn\'t match to expected {type("")} type.'
            ]

        return [
            'Pattern mismatch:',
            f'"{shorten_repr(left)}" doesn\'t match case '
            f'{"" if right.case_sensitive else "in"}sensitive pattern "{right.pattern}"'
        ]

@dataclass(frozen=True, eq=False, repr=False)
class AnyTextWith(AnyText):
    """Object that matches to any text (string) that
    contains given substring"""
    substring: str
    case_sensitive: bool = False

    def __eq__(self, other):
        if isinstance(other, (Anything, AnyText)):
            return True
        if not isinstance(other, str):
            return False

        return (self.substring in other
                if self.case_sensitive else
                self.substring.lower() in other.lower())

    def __repr__(self):
        return f'<Any Text With "{self.substring}">'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Text Contains matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyTextWith.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        if not isinstance(left, str):
            return [
                'Type mismatch:',
                f'Type {type(left)} doesn\'t match to expected {type("")} type.'
            ]

        return [
            'Content mismatch:',
            f'"{shorten_repr(left)}" doesn\'t contain case '
            f'{"" if right.case_sensitive else "in"}sensitive substring "{right.substring}"'
        ]


# --------
# Number
# --------
@dataclass(frozen=True, eq=False, repr=False)
class AnyNumber(BaseMatcher):
    """Object that matches to any number (int or float)"""
    def __eq__(self, other):
        return isinstance(other, (int, float, Anything, AnyNumber))

    def __repr__(self):
        return '<Any Number>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Number matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyNumber.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return [
            'Type mismatch:',
            f'Type {type(left)} doesn\'t match to expected {type(1)} or {type(1.1)} types.'
        ]

@dataclass(frozen=True, eq=False, repr=False)
class AnyNumberGreaterThan(AnyNumber):
    """Object that matches to any number (int or float) that
    is greater than given 'number'"""
    number: int|float

    def __eq__(self, other):
        result = False
        #if isinstance(other, AnyNumberGreaterThan):
        #    # >16 vs >2 -- definetly in range of other, so ok, but >2 in >16 is not.
        #    result = self.number >= other.number
        #elif isinstance(other, AnyNumberLessThan):
        #    # >6 vs <10 -- range will always be pretty narrow in scale of +-inf, so not equal
        #    result = False
        if isinstance(other, (AnyNumber, Anything)):
            result = True
        elif not isinstance(other, (int, float)):
            result = False
        else:
            result = other > self.number

        return result

    def __repr__(self):
        return f'<Any Number Greater Than ({self.number})>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Number Greater Than matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyNumberGreaterThan.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        if not isinstance(left, (int, float)):
            return [
                'Type mismatch:',
                f'Type {type(left)} doesn\'t match to expected {type(1)} or {type(1.1)} types.'
            ]

        return [
            'Number is less than expected:',
            f'{left} < {right.number}'
        ]

@dataclass(frozen=True, eq=False, repr=False)
class AnyNumberLessThan(AnyNumber):
    """Object that matches to any number (int or float) that
    is less than given 'number'"""
    number: int|float

    def __eq__(self, other):
        result = False
        # if isinstance(other, AnyNumberLessThan):
        #     # <6 vs <10 -- definetly in range of other, so ok, but >2 in >16 is not.
        #     result = self.number <= other.number
        # elif isinstance(other, AnyNumberGreaterThan):
        #     # <16 vs >2 -- range will always be pretty narrow in scale of +-inf, so not equal
        #     result = False
        if isinstance(other, (AnyNumber, Anything)):
            result = True
        elif not isinstance(other, (int, float)):
            result = False
        else:
            result = other < self.number

        return result

    def __repr__(self):
        return f'<Any Number Less Than ({self.number})>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Number Less Than matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyNumberLessThan.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        if not isinstance(left, (int, float)):
            return [
                'Type mismatch:',
                f'Type {type(left)} doesn\'t match to expected {type(1)} or {type(1.1)} types.'
            ]

        return [
            'Number is greater than expected:',
            f'{left} > {right.number}'
        ]

@dataclass(frozen=True, eq=False, repr=False)
class AnyNumberInRange(AnyNumber):
    """Object that matches to any number (int or float) that
    is less than given 'number'"""
    min_number: int|float
    max_number: int|float

    def __post_init__(self):
        super().__post_init__()
        if self.min_number > self.max_number:
            raise ValueError('Invalid matcher range limits! '
                '"min_number" must be less than "max_number", '
                f'but {self.min_number} > {self.max_number} was given.')

    def __eq__(self, other):
        if isinstance(other, (AnyNumber, Anything)):
            return True

        if not isinstance(other, (int, float)):
            return False

        return self.min_number <= other <= self.max_number

    def __repr__(self):
        return f'<Any Number In Range from {self.min_number} to {self.max_number}>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Number In Range matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyNumberInRange.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        if not isinstance(left, (int, float)):
            return [
                'Type mismatch:',
                f'Type {type(left)} doesn\'t match to expected {type(1)} or {type(1.1)} types.'
            ]

        if left > right.max_number:
            output = [
                "Value is out of range:",
                f"{left} is greater than {right.max_number} (right limit)"
            ]
        else:
            output = [
                "Value is out of range:",
                f"{left} is less than {right.min_number} (left limit)"
            ]

        return output


# --------
# Bool
# --------
@dataclass(frozen=True, eq=False, repr=False)
class AnyBool(BaseMatcher):
    """Object that matches to any bool"""
    def __eq__(self, other):
        return isinstance(other, (bool, Anything))

    def __repr__(self):
        return '<Any Bool>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Bool matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyBool.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return [
            'Type mismatch:',
            f'Type {type(left)} doesn\'t match to expected {type(True)} type.'
        ]


# --------
# Lists
# --------
@dataclass(frozen=True, eq=False, repr=False)
class AnyList(BaseMatcher):
    """Object that matches to any list"""
    def __eq__(self, other):
        return isinstance(other, (list, Anything, AnyList))

    def __repr__(self):
        return '<Any List>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to List matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyList.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return [
            'Type mismatch:',
            f'Type {type(left)} doesn\'t match to expected {type([])} type.'
        ]

@dataclass(frozen=True, eq=False, repr=False)
class AnyListOf(AnyList):
    """Object that matches to any list of given size and/or
    having elements of given type"""
    size: int|None = None
    item_type: str|int|float|bool|dict|list|None = None

    REPR_MSG = '<Any List Of{size_desc}{type_desc}>'
    SIZE_COMPARE_OP = '=='

    def __post_init__(self):
        super().__post_init__()
        if self.item_type is not None:
            object.__setattr__(self, 'item_type', type(self.item_type))

    def __eq__(self, other) -> bool:
        result = False
        if isinstance(other, AnyListLongerThan):
            result = (any((self.size is None,
                           self.size >= other.size))
                      and
                      any((self.item_type is None,
                           self.item_type == other.item_type)) )
        elif isinstance(other, AnyListShorterThan):
            result = (any((self.size is None,
                           self.size <= other.size))
                      and
                      any((self.item_type is None,
                           self.item_type == other.item_type)))
        elif isinstance(other, AnyListOf):
            result = all((
                any(
                    (self.size is None or other.size is None,
                    self.size == other.size
                )),
                any((
                    self.item_type is None or other.item_type is None,
                    self.item_type == other.item_type
                ))
            ))
        elif isinstance(other, (AnyList, Anything)):
            result = True
        elif not isinstance(other, list):
            result = False
        else:
            size_test = True
            if self.size is not None:
                match self.SIZE_COMPARE_OP:
                    case '==': size_test = len(other) == self.size
                    case '>': size_test = len(other) > self.size
                    case '<': size_test = len(other) < self.size

            type_test = True if self.item_type is None else \
                all((isinstance(itm, self.item_type) for itm in other))

            result = size_test and type_test

        return result

    def __repr__(self):
        size_desc = "" if self.size is None else f' {self.size} item(s)'
        type_desc = "" if self.item_type is None else f' type "{self.item_type.__name__}"'
        if size_desc and type_desc:
            type_desc = f' of {type_desc}'
        return self.REPR_MSG.format(size_desc=size_desc, type_desc=type_desc)

    @staticmethod
    def assertrepr_compare(left, right):
        """Method to print detailed comparison fail info"""
        output = [
            "Comparing to List Of matcher:",
            f"{shorten_repr(left)} != {right}"
        ]

        output.extend(AnyListOf.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        if not isinstance(left, list):
            return [
                'Type mismatch:',
                f'Type {type(left)} doesn\'t match to expected {type([])} type.'
            ]

        output = []
        if right.size is not None:
            size_matches = False
            match (right.SIZE_COMPARE_OP):
                case "==":
                    size_matches = len(left) == right.size
                case "<":
                    size_matches = len(left) < right.size
                case ">":
                    size_matches = len(left) > right.size

            if not size_matches:
                output.append("Size mismatch:")
                output.append(
                    f"{len(left)} {right.SIZE_COMPARE_OP} {right.size} is not true.")

        type_mismatch_info = []
        if right.item_type is not None:
            for idx, type_matches in enumerate([isinstance(v, right.item_type) for v in left]):
                if type_matches:
                    continue

                type_mismatch_info.append(
                    f'   {idx}) {shorten_repr(left[idx])} '
                    f'(of unexpected type "{type(left[idx]).__name__}")'
                )

        if type_mismatch_info:
            output.extend([
                "Element type mismatch:",
                f'Expected type of elements is "{right.item_type.__name__}":',
                *type_mismatch_info
            ])

        return output

@dataclass(frozen=True, eq=False, repr=False)
class AnyListLongerThan(AnyListOf):
    """Object that matches to any list with size
    greater than given 'size' and, optionally,
    having elements of given type"""
    size: int
    REPR_MSG = '<Any List Longer Than{size_desc}{type_desc}>'
    SIZE_COMPARE_OP = '>'

@dataclass(frozen=True, eq=False, repr=False)
class AnyListShorterThan(AnyListOf):
    """Object that matches to any list with size
    less than given 'size' and, optionally,
    having elements of given type"""
    size: int
    REPR_MSG = '<Any List Shorter Than{size_desc}{type_desc}>'
    SIZE_COMPARE_OP = '<'

@dataclass(frozen=True, eq=False, repr=False)
class AnyListOfRange(BaseMatcher):
    """Object that matches to any list of size in given range and/or
    having elements of given type"""
    min_size: int
    max_size: int
    item_type: str|int|float|bool|dict|list|None = None

    def __post_init__(self):
        super().__post_init__()
        if self.min_size >= self.max_size:
            raise ValueError('Invalid matcher range limits! '
                '"min_size" must be less than "max_size", '
                f'but {self.min_size} > {self.max_size} was given.')

        if self.item_type is not None:
            object.__setattr__(self, 'item_type', type(self.item_type))

    def __eq__(self, other) -> bool:
        if isinstance(other, (Anything, AnyList)):
            return True
        if not isinstance(other, list):
            return False

        size_test = self.min_size <= len(other) <= self.max_size
        type_test = True if self.item_type is None else \
            all((isinstance(itm, self.item_type) for itm in other))

        return size_test and type_test

    def __repr__(self):
        range_desc = f'of {self.min_size} to {self.max_size} items'
        type_desc = "" if self.item_type is None else f' of type "{self.item_type.__name__}"'
        return f'<Any List Of Range {range_desc}{type_desc}>'

    @staticmethod
    def assertrepr_compare(left, right):
        """Method to print detailed comparison fail info"""
        output = [
            "Comparing to List Of Range matcher:",
            f"{shorten_repr(left)} != {right}"
        ]

        output.extend(AnyListOfRange.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        if not isinstance(left, list):
            return [
                'Type mismatch:',
                f'Type {type(left)} doesn\'t match to expected {type([])} type.'
            ]

        output = []
        other_size = len(left)
        if right.min_size > other_size:
            output.append('Size mismatch:')
            output.append(f'Given list\'s size {other_size} is shorter than '
                          f'expected minimum of {right.min_size} elements!')

        elif right.max_size < other_size:
            output.append('Size mismatch:')
            output.append(f'Given list\' size {other_size} is longer than '
                          f'expected maximum of {right.max_size} elements!')

        type_mismatch_info = []
        if right.item_type is not None:
            for idx, type_matches in enumerate([isinstance(v, right.item_type) for v in left]):
                if type_matches:
                    continue
                type_mismatch_info.append(
                    f'   {idx}) {shorten_repr(left[idx])} '
                    f'(of unexpected type "{type(left[idx]).__name__}")'
                )

        if type_mismatch_info:
            output.extend([
                "Element type mismatch:",
                f'Expected type of elements is "{right.item_type.__name__}":',
                *type_mismatch_info
            ])

        return output


@dataclass(frozen=True, eq=False, repr=False)
class AnyListOfMatchers(BaseMatcher):
    """Object that matches to any list of given size and
    having elements that match to given matcher object
    (another AbstactMatcher or any other object)"""
    matcher: BaseMatcher | typing.Any
    size: int|None = None

    SIZE_COMPARE_OP = '=='

    def __eq__(self, other):
        result = True
        if isinstance(other, list):
            size_test = True
            if self.size is not None:
                match self.SIZE_COMPARE_OP:
                    case '==': size_test = len(other) == self.size
                    case '>': size_test = len(other) > self.size
                    case '<': size_test = len(other) < self.size

            type_test = all((
                item == self.matcher
                for item in other
            ))

            result = size_test and type_test

        elif isinstance(other, (AnyList, Anything)):
            result = True
        else:
            result = False

        return result

    def __repr__(self):
        return f'<Any List Of Matchers ({self.matcher}) '\
            f'of {self.size if self.size else "any number"} item(s)>'

    @staticmethod
    def assertrepr_compare(left, right):
        output = [
            "Comparing to List Of Matchers matcher:",
            f"{shorten_repr(left)} != {right}"
        ]

        output.extend(AnyListOfMatchers.assertrepr_compare_brief(left, right))

        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        output = []
        if right.size is not None:
            size_matches = False
            match (right.SIZE_COMPARE_OP):
                case "==":
                    size_matches = len(left) == right.size
                case "<":
                    size_matches = len(left) < right.size
                case ">":
                    size_matches = len(left) > right.size

            if not size_matches:
                output.append("Size mismatch:")
                output.append(
                    f" {len(left)} {right.SIZE_COMPARE_OP} {right.size} -- size mismatch!")

        elements_mismatch_detected = False
        match_output = [f'Elements that doesn\'t match to "{right.matcher}":']

        for idx, matches in enumerate([v == right.matcher for v in left]):
            if matches:
                continue

            match_output.append('')
            match_output.append(f'{idx}) {left[idx]}')
            if isinstance(right.matcher, BaseMatcher):
                reason = right.matcher.assertrepr_compare_brief(left[idx], right.matcher)
            else:
                reason = assertrepr_compare(pytest.current_config, '==', left[idx], right.matcher)
            match_output.extend([f'   {r}' for r in reason])
            elements_mismatch_detected = True

        if elements_mismatch_detected:
            output.extend(match_output)

        return output

@dataclass(frozen=True, eq=False, repr=False)
class AnyListOfMatchersLongerThan(AnyListOfMatchers):
    """Object that matches to any list with size
    greater than given 'size' and
    having elements that match to given matcher object
    (another AbstactMatcher or any other object)"""
    matcher: BaseMatcher | typing.Any
    size: int|None = None

    SIZE_COMPARE_OP = '>'

@dataclass(frozen=True, eq=False, repr=False)
class AnyListOfMatchersShorterThan(AnyListOfMatchers):
    """Object that matches to any list with size
    less than given 'size' and
    having elements that match to given matcher object
    (another AbstactMatcher or any other object)"""
    matcher: BaseMatcher | typing.Any
    size: int|None = None

    SIZE_COMPARE_OP = '<'


# --------
# Dicts
# --------
@dataclass(frozen=True, eq=False, repr=False)
class AnyDict(BaseMatcher):
    """Object that matches to any dict"""
    def __eq__(self, other):
        return isinstance(other, (dict, Anything))

    def __repr__(self):
        return '<Any Dict>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Dict matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyDict.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return [
            'Type mismatch:',
            f'Type {type(left)} doesn\'t match to expected {type({})} type.'
        ]

@dataclass(frozen=True, eq=False, repr=False)
class AnyNonEmptyDict(AnyDict):
    """Object that matches to any non-empty dict"""
    def __eq__(self, other) -> bool:
        return isinstance(other, (dict, Anything)) and other

    def __repr__(self):
        return '<Any Non-Empty Dict>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Non-empty Dict matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyDict.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        if not isinstance(left, (dict, Anything)):
            return [
                'Type mismatch:',
                f'Type {type(left)} doesn\'t match to expected {type({})} type.'
            ]

        return [
            "Dict is empty!"
        ]


# --------
# Date
# --------
DATE_OFFSET_PATTERN = re.compile(r'^(\+|-)(\d+\.?\d*)(y|w|d|h|m|s|ms|us)$')
OFFSET_UNITS = {
    'w': 'weeks', 'd': 'days',
    'h': 'hours', 'm': 'minutes', 's': 'seconds',
    'us': 'microseconds'
}

def get_offset_date(date_str: str) -> datetime.datetime:
    """Parses date and return parsed date, or date defined using
    offset expression (e.g. 'now', '+2d', etc.)"""
    utc = datetime.timezone.utc
    if date_str == 'now':
        return datetime.datetime.now(utc)

    re_result = DATE_OFFSET_PATTERN.match(date_str)
    if not re_result:
        # Date_str not in offset format - try parse from iso
        # If we fail - than user should see error and change input
        return datetime.datetime.fromisoformat(date_str).astimezone(utc)

    # Parse offset experession
    direction, amount, unit = re_result.groups()
    amount = float(amount)
    unit_name = OFFSET_UNITS.get(unit)
    if unit_name is None:
        if unit == 'y':
            # 'y' is not supported by datetime.timedelta, so manually convert
            unit_name = OFFSET_UNITS['d']
            amount *= 365
        elif unit == 'ms':
            unit_name = OFFSET_UNITS['us']
            amount *= 1000

    if direction == '-':
        amount *= -1

    # Return Now() with offset
    return datetime.datetime.now(utc) + datetime.timedelta(**{unit_name: amount})


@dataclass(frozen=True, eq=False, repr=False)
class AnyDate(BaseMatcher):
    """Object that matches to any date parsable by datetime module"""
    def __eq__(self, other) -> bool:
        if isinstance(other, Anything):
            return True

        if not isinstance(other, str):
            return False

        try:
            datetime.datetime.fromisoformat(other)
        except (ValueError, OverflowError):
            # Failed to parse means not equal
            return False

        return True

    def __repr__(self) -> str:
        return '<Any Date>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        """Return full list of string as explanation of why values are not equal"""
        output = [
            "Comparing to Any Date matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyDate.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        """Return shortened list of string as explanation of why values are not equal"""
        return [
            "Type mismatch:",
            f"Unexpected data type of {shorten_repr(left)} (type: {type(left)}). "
                "Only ISO formatted string is allowed."
        ]

@dataclass(frozen=True, eq=False, repr=False)
class AnyDateBefore(BaseMatcher):
    """Object that matches to any parsable date in the past
    relative to given date"""
    date: str = 'now'
    eq_cache = None

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, 'eq_cache', {})

    def __eq__(self, other) -> bool:
        self.eq_cache.clear()
        if isinstance(other, (Anything, AnyDate)):
            return True

        if not isinstance(other, str):
            return False

        try:
            other_date = datetime.datetime.fromisoformat(other)\
                            .astimezone(datetime.timezone.utc)
        except (ValueError, OverflowError):
            # Failed to parse means not equal
            return False

        self_date = get_offset_date(self.date)
        self.eq_cache.update({
            "self_date": self_date,
            "other_date": other_date
        })

        return other_date < self_date

    def __repr__(self) -> str:
        cur_date = self.date
        try:
            cur_date = datetime.datetime.fromisoformat(self.date)\
                .astimezone(datetime.timezone.utc).isoformat()
        except (ValueError, OverflowError):
            pass

        return f'<Any Date Before {cur_date}>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        """Return full list of string as explanation of why values are not equal"""
        output = [
            "Comparing to Date Before matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyDateBefore.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        """Return shortened list of string as explanation of why values are not equal"""
        eq_cache = right.eq_cache
        if not eq_cache:
            return [
                "Type mismatch:",
                f"Unexpected data type of {shorten_repr(left)} (type: {type(left)}). "
                    "Only ISO formatted string is allowed."
            ]

        diff = eq_cache['other_date'] - eq_cache['self_date']
        return [
            'Date mismatch:',
            f"{eq_cache['other_date']} is <{diff}> later than {eq_cache['self_date']} "
        ]

@dataclass(frozen=True, eq=False, repr=False)
class AnyDateAfter(BaseMatcher):
    """Object that matches to any parsable date in the future
    relative to given date"""
    date: str = 'now'
    eq_cache = None

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, 'eq_cache', {})

    def __eq__(self, other) -> bool:
        self.eq_cache.clear()
        if isinstance(other, (Anything, AnyDate)):
            return True

        if not isinstance(other, str):
            return False

        try:
            other_date = datetime.datetime.fromisoformat(other)\
                            .astimezone(datetime.timezone.utc)
        except (ValueError, OverflowError):
            # Failed to parse means not equal
            return False

        self_date = get_offset_date(self.date)

        self.eq_cache.update({
            "self_date": self_date,
            "other_date": other_date,
        })

        return other_date > self_date

    def __repr__(self) -> str:
        cur_date = self.date
        try:
            cur_date = datetime.datetime.fromisoformat(self.date)\
                .astimezone(datetime.timezone.utc).isoformat()
        except (ValueError, OverflowError):
            pass

        return f'<Any Date After {cur_date}>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        """Return full list of string as explanation of why values are not equal"""
        output = [
            "Comparing to Date After matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyDateAfter.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right: 'AnyDateAfter') -> list[str]:
        """Return shortened list of string as explanation of why values are not equal"""
        eq_cache = right.eq_cache
        if not eq_cache:
            return [
                "Type mismatch:",
                f"Unexpected data type of {shorten_repr(left)} (type: {type(left)}). "
                    "Only ISO formatted string is allowed."
            ]

        diff = eq_cache['self_date'] - eq_cache['other_date']
        return [
            'Date mismatch:',
            f"{eq_cache['other_date']} is <{diff}> earlier than {eq_cache['self_date']} "
        ]

@dataclass(frozen=True, eq=False, repr=False)
class AnyDateInRange(BaseMatcher):
    """Object that matches to any parsable date in given period"""
    date_from: str
    date_to: str
    eq_cache = None

    def __post_init__(self):
        super().__post_init__()

        left_limit = get_offset_date(self.date_from)
        right_limit = get_offset_date(self.date_to)
        if left_limit > right_limit:
            raise ValueError(
                'Invalid matcher range limits! '
                '"date_from" must be less than "date_to", '
                f'but given {self.date_from} > {self.date_to}!')

        object.__setattr__(self, 'eq_cache', {})

    def __eq__(self, other) -> bool:
        self.eq_cache.clear()
        if isinstance(other, (Anything, AnyDate)):
            return True

        if not isinstance(other, str):
            return False

        try:
            other_date = datetime.datetime.fromisoformat(other)\
                            .astimezone(datetime.timezone.utc)
        except (ValueError, OverflowError):
            # Failed to parse means not equal
            return False

        self_date_from = get_offset_date(self.date_from)
        self_date_to = get_offset_date(self.date_to)

        self.eq_cache.update({
            "self_date_from": self_date_from,
            "self_date_to": self_date_to,
            "other_date": other_date
        })
        return self_date_from <= other_date <= self_date_to

    def __repr__(self) -> str:
        date_from = self.date_from
        date_to = self.date_to
        try:
            date_from = datetime.datetime.fromisoformat(self.date_from)\
                .astimezone(datetime.timezone.utc).isoformat()
            date_to = datetime.datetime.fromisoformat(self.date_to)\
                .astimezone(datetime.timezone.utc).isoformat()
        except (ValueError, OverflowError):
            pass

        return f'<Any Date In Range between {date_from} and {date_to}>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        """Return full list of string as explanation of why values are not equal"""
        output = [
            "Comparing to Date In Range matcher:",
            f"{shorten_repr(left)} != {right}"
        ]
        output.extend(AnyDateInRange.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        """Return shortened list of string as explanation of why values are not equal"""
        eq_cache = right.eq_cache
        if not eq_cache:
            return [
                "Type mismatch:",
                f"Unexpected data type of {shorten_repr(left)} (type: {type(left)}). "
                    "Only ISO formatted string is allowed."
            ]

        output = ['Date mismatch:']
        if eq_cache['self_date_from'] > eq_cache['other_date']:
            diff = eq_cache['self_date_from'] - eq_cache['other_date']
            output.append(f"{eq_cache['other_date']} (UTC) is <{diff}> earlier than "
                          f"{eq_cache['self_date_from']} (UTC, left limit)")
        else:
            diff = eq_cache['other_date'] - eq_cache['self_date_to']
            output.append(f"{eq_cache['other_date']} (UTC) is <{diff}> later than "
                          f"{eq_cache['self_date_to']} (UTC, right limit)")

        return output
