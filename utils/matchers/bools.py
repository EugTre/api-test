"""Matcher to bool"""
from dataclasses import dataclass
from .base_matcher import BaseMatcher, Anything

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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
        ]
        output.extend(AnyBool.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        return [
            'Type mismatch:',
            f'Type {type(left)} doesn\'t match to expected {type(True)} type.'
        ]
