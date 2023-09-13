import pytest
import utils.matchers as match

def pytest_configure(config):
    # Store ref to Pytest config object.
    # It is used in Matchers module to call assertrepr_compare() with
    # valid setup to provide detailed assertions for matchers.
    pytest.current_config = config


def pytest_assertrepr_compare(op, left, right):
    if op != "==" and (
        not isinstance(right, match.BaseMatcher) \
        and not isinstance(left, match.BaseMatcher)
    ):
        return None

    if isinstance(right, match.BaseMatcher):
        return right.assertrepr_compare(left, right)

    if isinstance(left, match.BaseMatcher):
        return left.assertrepr_compare(right, left)
