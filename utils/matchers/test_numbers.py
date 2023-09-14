"""Tests for number matchers"""
import re

import pytest
import utils.matchers.matcher as match


class TestMatcherAnyNumber:
    """Tests for AnyNumber matchers"""
    @pytest.mark.parametrize("match_value",[
        0,
        12,
        -12,
        12.345,
        -12.345
    ])
    def test_any_number(self, match_value):
        matcher_instance = match.AnyNumber()
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value", (5, 5.0))
    @pytest.mark.parametrize("match_param", (4, 4.99))
    def test_any_number_greater_than(self, match_value, match_param):
        matcher_instance = match.AnyNumberGreaterThan(match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value", (5, 5.0))
    @pytest.mark.parametrize("match_param", (6, 5.01))
    def test_any_number_less_than(self, match_value, match_param):
        matcher_instance = match.AnyNumberLessThan(match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value", (5, 5.0))
    @pytest.mark.parametrize("match_param", (
        (-50, 50),
        (-50.0, 50.0),
        (4, 6),
        (4.99, 5.01),
        (5.0, 10),
        (-10, 5.0)
    ))
    def test_any_number_in_range(self, match_value, match_param):
        matcher_instance = match.AnyNumberInRange(*match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    # Negative tests
    # --------------
    @pytest.mark.parametrize('match_value', [
        "str", None, [], {}
    ])
    def test_any_number_fails(self, match_value):
        matcher_instance = match.AnyNumber()
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    @pytest.mark.parametrize("match_value, match_param", [
        (12, 50),
        (12, 12)
    ])
    def test_any_number_greater_than_fails(self, match_value, match_param):
        matcher_instance = match.AnyNumberGreaterThan(match_param)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    @pytest.mark.parametrize("match_value, match_param", [
        (50, 12),
        (12, 12),
        ('str', 12),
        ([1,2], 12),
    ])
    def test_any_number_less_than_fails(self, match_value, match_param):
        matcher_instance = match.AnyNumberLessThan(match_param)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    @pytest.mark.parametrize(
        "match_value, match_param, expected_exception, expected_message", (
        (
            50,
            (1, 5),
            AssertionError,
            r".*Number In Range.*Value is out of range.*greater.*right limit.*"
        ),
        (
            12,
            (120, 150),
            AssertionError,
            r".*Number In Range.*Value is out of range.*less.*left limit.*"
        ),
        (
            'str',
            (0, 1),
            AssertionError,
            r".*Number In Range.*Type mismatch.*"
        ),
        (
            [1,2],
            (0, 1),
            AssertionError,
            r".*Number In Range.*Type mismatch.*"
        ),
        (
            '',
            (100, 50),
            ValueError,
            r"Invalid matcher range limits!.*"
        )
    ))
    def test_any_number_in_range_fails(self, match_value, match_param,
                                       expected_exception, expected_message):
        with pytest.raises(expected_exception,
                           match=re.compile(expected_message, re.S)):
            matcher_instance = match.AnyNumberInRange(*match_param)
            assert matcher_instance == match_value

        with pytest.raises(expected_exception,
                           match=re.compile(expected_message, re.S)):
            matcher_instance = match.AnyNumberInRange(*match_param)
            assert match_value == matcher_instance

    # --- Negative on initialization
    @pytest.mark.parametrize("params", ('str', [], None, {}))
    def test_any_number_greater_than_init_fails(self, params):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*number.*',
            re.S
        )):
            match.AnyNumberGreaterThan(params)

    @pytest.mark.parametrize("params", ('str', [], None, {}))
    def test_any_number_less_than_init_fails(self, params):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*number.*',
            re.S
        )):
            match.AnyNumberLessThan(params)

    @pytest.mark.parametrize("params", ('str', [], None, {}))
    def test_any_number_in_range_init_fails(self, params):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*min_number.*max_number.*',
            re.S
        )):
            match.AnyNumberInRange(params, params)
