import pytest
import utils.matchers as match

def pytest_assertrepr_compare(op, left, right):
    if not isinstance(right, match.Anything) or op != "==":
        return None

    if isinstance(right, match.AnyListOf):
        return match.AnyListOf.assert_repr_compare(left, right)
