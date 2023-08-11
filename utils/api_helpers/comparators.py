"""Data comparators, than provides specific compare methods."""

class Data:
    """Basic data comparator"""
    @staticmethod
    def is_type(value, is_type):
        """Verifies that value has given type."""
        assert isinstance(value, is_type), \
            f'[{value}] of type "{type(value)}" is not the same '\
            f'as given type "{is_type}".'

    @staticmethod
    def is_same_type(val1, val2):
        """Verifies that values are the same type."""
        assert isinstance(val1, type(val2)), \
            f'Value [{val1}] of type "{type(val1)}" is not the same '\
            f'as given value [{val2}] type "{type(val2)}".'

class Number(Data):
    """Numbers comparator"""
    @staticmethod
    def is_less_than(val1: int|float, val2: int|float,
                     assert_msg: str = "Number {val1} is greater or equal to {val2}"):
        """Verifies that val1 is less than val2."""
        Number.is_same_type(val1, val2)
        assert val1 < val2, assert_msg.format(val1=val1, val2=val2)

    @staticmethod
    def is_greater_than(val1: int|float, val2: int|float,
                        assert_msg: str = "Number {val1} is less or equal to {val2}"):
        """Verifies that val1 is greater than val2."""
        Number.is_same_type(val1, val2)
        assert val1 > val2, assert_msg.format(val1=val1, val2=val2)

class String(Data):
    """Strings omparator"""
    @staticmethod
    def contains(val1: str, val2: str):
        """Verifies that string contains given substring."""
        Data.is_same_type(val1, val2)
        assert val2 in val1, f'Given string "{val1}" doesn\'t contain substring "{val2}"'

class Array(Data):
    """List comparator"""
    @staticmethod
    def count_is_greater_than(val1: list, val2: int):
        """Verifies that list size is greater than given value"""
        Data.is_type(val1, list)
        count = len(val1)
        Number.is_greater_than(count, val2,
                               f"List size {count} is less or equal to {val2}.")

    @staticmethod
    def count_is_less_than(val1: list, val2: int):
        """Verifies that list size is less than given value"""
        Data.is_type(val1, list)
        count = len(val1)
        Number.is_greater_than(count, val2,
                               f"List size {count} is greater or equal to {val2}.")

class Date(Data):
    """Comparators for date.
    Parses input string to date object and compare."""

    @staticmethod
    def equals():
        """Date (Year, Monthd and Day) equals"""
        pass

    @staticmethod
    def is_after():
        """Date (Year, Monthd and Day) is after the given"""
        pass

    @staticmethod
    def is_before():
        """Date (Year, Monthd and Day) is before the given"""
        pass


    @staticmethod
    def time_equals():
        """Date & time (Year, Monthd, Day and time) equals"""
        pass

    @staticmethod
    def time_is_before():
        """Date & time (Year, Monthd, Day and time) is after the given"""
        pass

    @staticmethod
    def time_is_after():
        """Date & time (Year, Monthd, Day and time) is before the given"""
        pass
