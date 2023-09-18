import pytest
from utils.matchers.matcher import BaseMatcher

def pytest_configure(config):
    # Store ref to Pytest config object.
    # It is used in Matchers module to call assertrepr_compare() with
    # valid setup to provide detailed assertions for matchers.
    pytest.current_config = config

def pytest_assertrepr_compare(op, left, right):
    if op != "==" and (
        not isinstance(right, BaseMatcher) \
        and not isinstance(left, BaseMatcher)
    ):
        return None

    if isinstance(right, BaseMatcher):
        return right.assertrepr_compare(left, right)

    # Flip to place matcher on right part for proper details reporting
    if isinstance(left, BaseMatcher):
        return left.assertrepr_compare(right, left)
