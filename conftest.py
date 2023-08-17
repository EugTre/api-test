import pytest
import utils.api_helpers.match_objects as match

def pytest_assertrepr_compare(op, left, right):
    if not isinstance(right, match.Any) or op != "==":
        return None

    if isinstance(right, match.AnyListOf):
        return match.AnyListOf.assert_repr_compare(left, right)
