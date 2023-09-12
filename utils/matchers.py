"""Module provides matche object of various kinds"""
import re
import typing
from dataclasses import dataclass
from abc import ABC, abstractmethod
import pytest
from _pytest.assertion.util import assertrepr_compare

from utils.basic_manager import BasicManager


def shorten_repr(list_or_dict):
    """Helper method to shorten object repr in
    assertrepr_compare_brief method output"""
    repr_str = repr(list_or_dict)
    if isinstance(list_or_dict, (list, dict)) and len(repr_str) > 55:
        repr_str = f'{repr_str[:35]} ...{repr_str[-20:]}'
    return repr_str


@dataclass(frozen=True, slots=True, eq=False)
class AbstractMatcher(ABC):
    """Abstract Matcher to any value"""
    def __eq__(self, other):
        return True

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


@dataclass(frozen=True, slots=True, eq=False)
class Anything(AbstractMatcher):
    """Matches to any value"""
    def __eq__(self, other):
        return other is not None

    def __repr__(self):
        return '<Any>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Anything Matcher:",
            f"{left} != {right}"
        ]
        output.extend(Anything.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return ['Value is None, but expecte to be anything']


# --------
# Text
# --------
@dataclass(slots=True, frozen=True, eq=False)
class AnyText(AbstractMatcher):
    """Matches to any text (string), including empty string"""
    def __eq__(self, other):
        return isinstance(other, (str, Anything, AnyText))

    def __repr__(self):
        return '<Any Text>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Text Matcher:",
            f" {left} != {right}"
        ]
        output.extend(AnyText.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return [
            'Type mismatch:',
            f'{type(left)} != {type("")}'
        ]

@dataclass(slots=True, frozen=True, eq=False)
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
            "Comparing to Text Like Matcher:",
            f'{left} != {right}'
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
            f'"{left}" doesn\'t match case '
            f'{"" if right.case_sensitive else "in"}sensitive pattern "{right.pattern}"'
        ]

@dataclass(slots=True, frozen=True, eq=False)
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
            "Comparing to Text Contains Matcher:",
            f"{left} != {right}"
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
            f'"{left}" doesn\'t contain case '
            f'{"" if right.case_sensitive else "in"}sensitive substring "{right.substring}"'
        ]


# --------
# Number
# --------
@dataclass(slots=True, frozen=True, eq=False)
class AnyNumber(AbstractMatcher):
    """Object that matches to any number (int or float)"""
    def __eq__(self, other):
        return isinstance(other, (int, float, Anything, AnyNumber))

    def __repr__(self):
        return '<Any Number>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        left_repr = shorten_repr(left)
        output = [
            "Comparing to Number Matcher:",
            f"{left_repr} != {right}"
        ]
        output.extend(AnyNumber.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return [
            'Type mismatch:',
            f'Type {type(left)} doesn\'t match to expected {type(1)} or {type(1.1)} types.'
        ]

@dataclass(slots=True, frozen=True, eq=False)
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
            # Chompare with given int/float
            num = self.number
            if not isinstance(num, float) and isinstance(other, float):
                num = float(num)
            elif isinstance(num, float) and not isinstance(other, float):
                other = float(other)

            result = other > num

        return result

    def __repr__(self):
        return f'<Any Number Greater Than ({self.number})>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Number Greater Than Matcher:",
            f"{left} != {right}"
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

@dataclass(slots=True, frozen=True, eq=False)
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
            # Chompare with given int/float
            num = self.number
            if not isinstance(num, float) and isinstance(other, float):
                num = float(num)
            elif isinstance(num, float) and not isinstance(other, float):
                other = float(other)

            result = other < num

        return result

    def __repr__(self):
        return f'<Any Number Less Than ({self.number})>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Number Less Than Matcher:",
            f"{left} != {right}"
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


# --------
# Bool
# --------
@dataclass(slots=True, frozen=True, eq=False)
class AnyBool(AbstractMatcher):
    """Object that matches to any bool"""
    def __eq__(self, other):
        return isinstance(other, (bool, Anything))

    def __repr__(self):
        return '<Any Bool>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        left_repr = repr(left)
        if isinstance(left, (list, dict)) and len(left_repr) > 30:
            left_repr = f'{left_repr[:10]} ...{left_repr[-10:]}'

        output = [
            "Comparing to Bool Matcher:",
            f"{left_repr} != {right}"
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
@dataclass(slots=True, frozen=True, eq=False)
class AnyList(AbstractMatcher):
    """Object that matches to any list"""
    def __eq__(self, other):
        return isinstance(other, (list, Anything, AnyList))

    def __repr__(self):
        return '<Any List>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to List Matcher:",
            f"{left} != {right}"
        ]
        output.extend(AnyList.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return [
            'Type mismatch:',
            f'Type {type(left)} doesn\'t match to expected {type([])} type.'
        ]

@dataclass(slots=True, frozen=True, eq=False)
class AnyListOf(AnyList):
    """Object that matches to any list of given size and/or
    having elements of given type"""
    size: int = None
    item_type: str|int|float|bool|dict|list = None

    REPR_MSG = '<Any List Of{size_desc}{type_desc}>'
    SIZE_COMPARE_OP = '=='

    def __post_init__(self):
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
            "Comparing List Of matcher:",
            f" {left} != {right}"
        ]

        output.extend(AnyListOf.assertrepr_compare_brief(left, right))
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
                output.append("Size comparison:")
                output.append(
                    f" {len(left)} {right.SIZE_COMPARE_OP} {right.size} -- size mismatch!")

        type_mismatch_detected = False
        if right.type is not None:
            type_output = ["Type comparison:"]
            type_output.append(f'Expected type of elements is "{right.type.__name__}":')
            for idx, type_matches in enumerate([isinstance(v, right.type) for v in left]):
                if type_matches:
                    continue
                type_output.append(
                    f'   {idx}) {left[idx]} (of unexpected type "{type(left[idx]).__name__}")')
                type_mismatch_detected = True

        if type_mismatch_detected:
            output.extend(type_output)

        return output

@dataclass(slots=True, frozen=True, eq=False)
class AnyListLongerThan(AnyListOf):
    """Object that matches to any list with size
    greater than given 'size' and, optionally,
    having elements of given type"""
    size: int
    REPR_MSG = '<Any List Longer Than{size_desc}{type_desc}>'
    SIZE_COMPARE_OP = '>'

@dataclass(slots=True, frozen=True, eq=False)
class AnyListShorterThan(AnyListOf):
    """Object that matches to any list with size
    less than given 'size' and, optionally,
    having elements of given type"""
    size: int
    REPR_MSG = '<Any List Shorter Than{size_desc}{type_desc}>'
    SIZE_COMPARE_OP = '<'

@dataclass(slots=True, frozen=True, eq=False)
class AnyListOfMatchers(AbstractMatcher):
    """Object that matches to any list of given size and
    having elements that match to given matcher object
    (another AbstactMatcher or any other object)"""
    matcher: AbstractMatcher | typing.Any
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
            f" {left} != {right}"
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
                output.append("Size comparison:")
                output.append(
                    f" {len(left)} {right.SIZE_COMPARE_OP} {right.size} -- size mismatch!")

        elements_mismatch_detected = False
        match_output = [f'Elements that doesn\'t match to "{right.matcher}":']

        for idx, matches in enumerate([v == right.matcher for v in left]):
            if matches:
                continue

            match_output.append('')
            match_output.append(f'{idx}) {left[idx]}')
            match_output.append('   Reason:')
            if isinstance(right.matcher, AbstractMatcher):
                reason = right.matcher.assertrepr_compare_brief(left[idx], right.matcher)
            else:
                reason = assertrepr_compare(pytest.current_config, '==', left[idx], right.matcher)
            match_output.extend([f'   {r}' for r in reason])
            elements_mismatch_detected = True

        if elements_mismatch_detected:
            output.extend(match_output)

        return output

@dataclass(slots=True, frozen=True, eq=False)
class AnyListOfMatchersLongerThan(AnyListOfMatchers):
    """Object that matches to any list with size
    greater than given 'size' and
    having elements that match to given matcher object
    (another AbstactMatcher or any other object)"""
    matcher: AbstractMatcher
    size: int|None = None

    SIZE_COMPARE_OP = '>'

@dataclass(slots=True, frozen=True, eq=False)
class AnyListOfMatchersShorterThan(AnyListOfMatchers):
    """Object that matches to any list with size
    less than given 'size' and
    having elements that match to given matcher object
    (another AbstactMatcher or any other object)"""
    matcher: AbstractMatcher
    size: int|None = None

    SIZE_COMPARE_OP = '<'


# --------
# Dicts
# --------
@dataclass(slots=True, frozen=True, eq=False)
class AnyDict(AbstractMatcher):
    """Object that matches to any dict"""
    def __eq__(self, other):
        return isinstance(other, (dict, Anything))

    def __repr__(self):
        return '<Any Dict>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        output = [
            "Comparing to Dict matcher:",
            f"{left} != {right}"
        ]
        output.extend(AnyDict.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return [
            'Type mismatch:',
            f'Type {type(left)} doesn\'t match to expected {type({})} type.'
        ]

@dataclass(slots=True, frozen=True, eq=False)
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
            f"{left} != {right}"
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


class MatchersManager(BasicManager):
    """Class to register and provide access to matcher objects from various points
    in the framework (e.g. for compiler procedures).
    """
    def add(self, item: AbstractMatcher, name: str | None = None, override: bool = False):
        """Registers given matcher under given name.

        Args:
            matcher (AbstractMatcher): matcher class.
            name (str, optional): registration name. Defaults to class.__name__.

        Raises:
            ValueError: when name already occupied.
        """
        return super().add(item, name, override)

    def add_all(self, items: tuple[AbstractMatcher, str] | list[AbstractMatcher],
                override: bool = False):
        """Registers given collection of matchers.

        Args:
            matchers (list | tuple): collection of matchers where each element is
            'class<cls>' or ('class<cls>', 'name<str>').
        """
        return super().add_all(items, override)

    def get(self, name: str, args:tuple=(), kwargs:dict=None) -> AbstractMatcher:
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
        if issubclass(item, AbstractMatcher):
            return

        raise ValueError(f'Registraion failed for item "{item}" at {self.__class__.__name__}. '
                         f'Only subclass items of class "{AbstractMatcher.__name__}" '
                         f'are allowed!')


# Default collection of matchers.
matchers_manager = MatchersManager()
matchers_manager.add_all((
    Anything,
    AnyText,
    AnyTextLike,
    AnyTextWith,
    AnyNumber,
    AnyNumberGreaterThan,
    AnyNumberLessThan,
    AnyBool,
    AnyList,
    AnyListOf,
    AnyListLongerThan,
    AnyListShorterThan,
    AnyDict,
    AnyNonEmptyDict
))
