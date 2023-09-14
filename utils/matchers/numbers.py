"""Matchers to numbers (int/float)"""
from dataclasses import dataclass
from .base_matcher import BaseMatcher, Anything


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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
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
            f"{BaseMatcher.shorten_repr(left)} != {right}"
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
