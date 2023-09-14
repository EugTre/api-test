"""Matcher to dicts"""
from dataclasses import dataclass
from .base_matcher import BaseMatcher, Anything

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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
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
