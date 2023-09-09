import pytest
import utils.matchers as match

def pytest_configure(config):
    # Store ref to Pytest config object.
    # It is used in Matchers module to call assertrepr_compare() with
    # valid setup to provide detailed assertions for matchers.
    pytest.current_config = config


def pytest_assertrepr_compare(op, left, right):
    if op != "==" and (
        not isinstance(right, match.AbstractMatcher) \
        and not isinstance(left, match.AbstractMatcher)
    ):
        return None

    if isinstance(right, match.AbstractMatcher):
        return right.assertrepr_compare(left, right)

    if isinstance(left, match.AbstractMatcher):
        return left.assertrepr_compare(right, left)
