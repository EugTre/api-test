"""Tests for text matchers"""
import re

import pytest
import utils.matchers.matcher as match


class TestMatcherAnyText:
    """Tests for AnyText matchers"""
    @pytest.mark.parametrize("match_value",[
        "text", "", "23"
    ])
    def test_any_text(self, match_value):
        matcher_instance = match.AnyText()
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value, matcher_pattern",[
        ("", ".*"),
        ("text", ".*e.*"),
        ("text", "^te.*"),
        ("text", ".*xt$"),
        ('24', '[0-9]+')
    ])
    def test_any_text_like(self, match_value, matcher_pattern):
        matcher_instance = match.AnyTextLike(matcher_pattern)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value, matcher_pattern",[
        ("", ""),
        ("text info", "info"),
        ("text info", "text"),
        ("text info", " "),
        ("text", "x"),
        ('24', '2')
    ])
    def test_any_text_with(self, match_value, matcher_pattern):
        matcher_instance = match.AnyTextWith(matcher_pattern)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    # --- Negative
    # ----------------
    @pytest.mark.parametrize("match_value",[
        12, 12.33, [], {}, None
    ])
    def test_any_text_not_match(self, match_value):
        matcher_instance = match.AnyText()
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    @pytest.mark.parametrize("match_value, matcher_pattern",[
        ("", ".*e.*"),
        ("call text", "^te.*"),
        ("text info", ".*xt$"),
        ('text', '[0-9]+'),
        (1234, '[0-9]+'),
        ([1,2,3], '[0-9]+')
    ])
    def test_any_text_like_not_match(self, match_value, matcher_pattern):
        matcher_instance = match.AnyTextLike(matcher_pattern)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    @pytest.mark.parametrize("match_value, matcher_pattern",[
        ("", "word"),
        ("text info", "word"),
        ('text', 'w'),
        (1234, '4'),
        ([1,2,3], '4')
    ])
    def test_any_text_with_not_match(self, match_value, matcher_pattern):
        matcher_instance = match.AnyTextWith(matcher_pattern)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    # --- Negative on initialization
    @pytest.mark.parametrize("params", (
        (123, 123),
        ([], 'str'),
        (None, None),
        (False, []),
    ))
    def test_any_text_like_init_fails(self, params):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*pattern.*case_sensitive.*',
            re.S
        )):
            match.AnyTextLike(*params)

    @pytest.mark.parametrize("params", (
        (123, 123),
        ([], 'str'),
        (None, None),
        (False, []),
    ))
    def test_any_text_with_init_fails(self, params):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*substring.*case_sensitive.*',
            re.S
        )):
            match.AnyTextWith(*params)
