"""Matchers to string values"""
import re
from dataclasses import dataclass

from .base_matcher import BaseMatcher, Anything

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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
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
            f'{BaseMatcher.shorten_repr(left)} != {right}'
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
            f'"{BaseMatcher.shorten_repr(left)}" doesn\'t match case '
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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
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
            f'"{BaseMatcher.shorten_repr(left)}" doesn\'t contain case '
            f'{"" if right.case_sensitive else "in"}sensitive substring "{right.substring}"'
        ]
