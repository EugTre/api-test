"""Module provides matche object of various kinds"""
import re
from dataclasses import dataclass
from abc import ABC

@dataclass(frozen=True, slots=True)
class AbstractMatcher(ABC):
    """Abstract Matcher to any value"""
    def __eq__(self, other):
        return True

    def __repr__(self):
        return ''

@dataclass(frozen=True, slots=True)
class Any(AbstractMatcher):
    """Matches to any value"""
    def __eq__(self, other):
        return True

    def __repr__(self):
        return '<Any>'


@dataclass(slots=True, frozen=True)
class AnyText(Any):
    """Matches to any text (string), including empty string"""
    def __eq__(self, other):
        return isinstance(other, str)

    def __repr__(self):
        return '<Any Text>'


@dataclass(slots=True, frozen=True)
class AnyTextLike(AnyText):
    """Matches to any text (string) that matches to given regex"""
    pattern: str

    def __eq__(self, other):
        return isinstance(other, str) and re.match(self.pattern, other)

    def __repr__(self):
        return f'<Any Text Like {self.pattern}>'


@dataclass(slots=True, frozen=True)
class AnyTextWith(AnyText):
    """Matches to any text (string) that contains given substring"""
    substring: str

    def __eq__(self, other):
        if isinstance(other, (Any, AnyText)):
            return True

        return isinstance(other, str) and self.substring in other

    def __repr__(self):
        return f'<Any Text With "{self.substring}">'


@dataclass(slots=True, frozen=True)
class AnyNumber(Any):
    def __eq__(self, other):
        return isinstance(other, (int, float))

    def __repr__(self):
        return '<Any Number>'

@dataclass(slots=True, frozen=True)
class AnyNumberGreaterThan(AnyNumber):
    def __init__(self, num):
        self.num = num

    def __eq__(self, other):
        if not isinstance(other, (int, float)):
            return False

        num = self.num
        if not isinstance(num, float) and isinstance(other, float):
            num = float(num)
        elif isinstance(num, float) and not isinstance(other, float):
            other = float(other)

        return other > num

    def __repr__(self):
        return f'<Any Number Greater Than ({self.num})>'

@dataclass(slots=True, frozen=True)
class AnyNumberLessThan(AnyNumber):
    def __init__(self, num):
        self.num = num

    def __eq__(self, other):
        if not isinstance(other, (int, float)):
            return False

        num = self.num
        if not isinstance(num, float) and isinstance(other, float):
            num = float(num)
        elif isinstance(num, float) and not isinstance(other, float):
            other = float(other)

        return other < num

    def __repr__(self):
        return f'<Any Number Less Than ({self.num})>'


@dataclass(slots=True, frozen=True)
class AnyBool(Any):
    def __eq__(self, other):
        return isinstance(other, bool)

    def __repr__(self):
        return '<Any Bool>'


@dataclass(slots=True, frozen=True)
class AnyList(Any):
    def __eq__(self, other):
        return isinstance(other, (list, Any, AnyList))

    def __repr__(self):
        return '<Any List>'

@dataclass(slots=True, frozen=True)
class AnyListOf(AnyList):
    REPR_MSG = '<Any List Of{size_desc}{type_desc}>'
    SIZE_COMPARE_OP = '=='

    def __init__(self, size = None, type = None):
        self.size = size
        self.type = type

    def __eq__(self, other) -> bool:
        if isinstance(other, (Any, AnyList)):
            return True

        if not isinstance(other, list):
            return False

        size_test = True
        if self.size is not None:
            match self.SIZE_COMPARE_OP:
                case '==': size_test = len(other) == self.size
                case '>': size_test = len(other) > self.size
                case '<': size_test = len(other) < self.size

        type_test = True if self.type is None else \
            all((isinstance(itm, self.type) for itm in other))

        return size_test and type_test

    def __repr__(self):
        size_desc = "" if self.size is None else f' {self.size} item(s)'
        type_desc = "" if self.type is None else f' of type "{self.type.__name__}"'
        return self.REPR_MSG.format(size_desc=size_desc, type_desc=type_desc)

    @staticmethod
    def assert_repr_compare(left, right):
        output = ["Comparing List matcher:", f" {left} != {right}"]

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

@dataclass(slots=True, frozen=True)
class AnyListLongerThan(AnyListOf):
    REPR_MSG = '<Any List Longer Than{size_desc}{type_desc}>'
    SIZE_COMPARE_OP = '>'

@dataclass(slots=True, frozen=True)
class AnyListShorterThan(AnyListOf):
    REPR_MSG = '<Any List Shorter Than{size_desc}{type_desc}>'
    SIZE_COMPARE_OP = '<'

@dataclass(slots=True, frozen=True)
class AnyDict(Any):
    def __eq__(self, other):
        return isinstance(other, dict)

    def __repr__(self):
        return '<Any Dict>'

@dataclass(slots=True, frozen=True)
class AnyNonEmptyDict(AnyDict):
    def __eq__(self, other) -> bool:
        return isinstance(other, dict) and other

    def __repr__(self):
        return '<Any Non-Empty Dict>'


class MatchersManager:
    """Class to register and provide access to matcher objects from various points
    in the framework (e.g. for compiler procedures).
    """
    def __init__(self):
        self.collection = {}

    def register(self, matcher: AbstractMatcher, name: str = None) -> None:
        """Registers given matcher under given name.

        Args:
            matcher (Any): matcher class.
            name (str, optional): registration name. Defaults to class.__name__.

        Raises:
            ValueError: when name already occupied.
        """
        if not name:
            name = matcher.__name__

        if name in self.collection:
            raise ValueError(f'"{name}" already registered!')

        self.collection[name] = matcher

    def bulk_register(self, matchers: list|tuple) -> None:
        """Registers given collection of matchers.

        Args:
            matchers (list | tuple): collection of matchers where each element is
            'class<cls>' or ('class<cls>', 'name<str>').
        """
        for matcher_data in matchers:
            if isinstance(matcher_data, (tuple, list)):
                self.register(*matcher_data)
            else:
                self.register(matcher_data)

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


manager = MatchersManager()
manager.bulk_register((
    Any,
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
