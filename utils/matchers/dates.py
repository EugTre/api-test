"""Matchers to dates (as strings)"""
import re
import datetime
from dataclasses import dataclass

from .base_matcher import BaseMatcher, Anything

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
    return datetime.datetime.now(utc) + datetime.timedelta(
        **{unit_name: amount}
    )


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
        """Return full list of string as explanation of why values are not
        equal"""
        output = [
            "Comparing to Any Date matcher:",
            f"{BaseMatcher.shorten_repr(left)} != {right}"
        ]
        output.extend(AnyDate.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        """Return shortened list of string as explanation of why values are
        not equal"""
        return [
            "Type mismatch:",
            f"Unexpected data type of {BaseMatcher.shorten_repr(left)} "
            f"(type: {type(left)}). Only ISO formatted string is allowed."
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
        """Return full list of string as explanation of why values are
        not equal"""
        output = [
            "Comparing to Date Before matcher:",
            f"{BaseMatcher.shorten_repr(left)} != {right}"
        ]
        output.extend(AnyDateBefore.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        """Return shortened list of string as explanation of why values are
        not equal"""
        eq_cache = right.eq_cache
        if not eq_cache:
            return [
                "Type mismatch:",
                f"Unexpected data type of {BaseMatcher.shorten_repr(left)} "
                f"(type: {type(left)}). Only ISO formatted string is allowed."
            ]

        diff = eq_cache['other_date'] - eq_cache['self_date']
        return [
            'Date mismatch:',
            f"{eq_cache['other_date']} is <{diff}> later than "
            f"{eq_cache['self_date']}"
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
        """Return full list of string as explanation of why values are
        not equal"""
        output = [
            "Comparing to Date After matcher:",
            f"{BaseMatcher.shorten_repr(left)} != {right}"
        ]
        output.extend(AnyDateAfter.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right: 'AnyDateAfter') -> list[str]:
        """Return shortened list of string as explanation of why values are
        not equal"""
        eq_cache = right.eq_cache
        if not eq_cache:
            return [
                "Type mismatch:",
                f"Unexpected data type of {BaseMatcher.shorten_repr(left)} "
                f"(type: {type(left)}). Only ISO formatted string is allowed."
            ]

        diff = eq_cache['self_date'] - eq_cache['other_date']
        return [
            'Date mismatch:',
            f"{eq_cache['other_date']} is "
            f"<{diff}> earlier than {eq_cache['self_date']} "
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
        offset = True
        try:
            date_from = datetime.datetime.fromisoformat(self.date_from)\
                .astimezone(datetime.timezone.utc).isoformat()
            date_to = datetime.datetime.fromisoformat(self.date_to)\
                .astimezone(datetime.timezone.utc).isoformat()
            offset = False
        except (ValueError, OverflowError):
            pass

        if not offset:
            return f'<Any Date In Range between {date_from} and {date_to}>'

        return f'<Any Date In Range between {date_from} and {date_to} of' \
            f'{datetime.datetime.now(datetime.timezone.utc).isoformat()}>'

    @staticmethod
    def assertrepr_compare(left, right) -> list[str]:
        """Return full list of string as explanation of why values are not
        equal"""
        output = [
            "Comparing to Date In Range matcher:",
            f"{BaseMatcher.shorten_repr(left)} != {right}"
        ]
        output.extend(AnyDateInRange.assertrepr_compare_brief(left, right))
        return output

    @staticmethod
    def assertrepr_compare_brief(left, right) -> list[str]:
        """Return shortened list of string as explanation of why values are
        not equal"""
        eq_cache = right.eq_cache
        if not eq_cache:
            return [
                "Type mismatch:",
                f"Unexpected data type of {BaseMatcher.shorten_repr(left)} "
                "(type: {type(left)}). Only ISO formatted string is allowed."
            ]

        output = ['Date mismatch:']
        if eq_cache['self_date_from'] > eq_cache['other_date']:
            diff = eq_cache['self_date_from'] - eq_cache['other_date']
            output.append(f"{eq_cache['other_date']} (UTC) is "
                          f"<{diff}> earlier than "
                          f"{eq_cache['self_date_from']} (UTC, left limit)")
        else:
            diff = eq_cache['other_date'] - eq_cache['self_date_to']
            output.append(f"{eq_cache['other_date']} (UTC) is "
                          f"<{diff}> later than "
                          f"{eq_cache['self_date_to']} (UTC, right limit)")

        return output
