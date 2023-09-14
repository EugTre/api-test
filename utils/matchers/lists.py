"""Matchers to lists"""
import typing
from dataclasses import dataclass

import pytest
from _pytest.assertion.util import assertrepr_compare

from .base_matcher import BaseMatcher, Anything


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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
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
                    f'   {idx}) {BaseMatcher.shorten_repr(left[idx])} '
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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
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
                    f'   {idx}) {BaseMatcher.shorten_repr(left[idx])} '
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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
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
