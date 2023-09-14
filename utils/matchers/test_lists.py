"""Tests for List matchers"""
import re

import pytest
import utils.matchers.matcher as match

def generate_test_id_for_any_list_of_range(val):
    if isinstance(val, tuple):
        return f'{val[0]}_{val[1]}'
    return str(val)


class TestMatcherAnyList:
    """Tests AnyListOf matchers"""
    @pytest.mark.parametrize("match_value",[
        [],
        [1,2,3],
        ['a', 'b'],
        [ [], [] ]
    ])
    def test_any_list(self, match_value):
        matcher_instance = match.AnyList()
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    # --- List negative tests
    @pytest.mark.parametrize("match_value",[
        123, 'str', None, {}, False
    ])
    def test_any_list_fails(self, match_value):
        matcher_instance = match.AnyList()
        assert matcher_instance != match_value
        assert match_value != matcher_instance


class TestMatcherAnyListOf:
    """Tests AnyListOf matchers"""
    # --- AnyListOf
    @pytest.mark.parametrize("match_value, match_param",[
        (
            [],
            {'size': 0}
        ),
        (
            [1,2,3],
            {'size': 3}
        ),
        (
            [ [], [] ],
            {'size': 2}
        )
    ])
    def test_any_list_of_size(self, match_value, match_param):
        matcher_instance = match.AnyListOf(**match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value, match_param",[
        (
            [],
            {'item_type': None}
        ),
        (
            [1,2,3],
            {'item_type': 1}
        ),
        (
            [ [], [] ],
            {'item_type': []}
        ),
        (
            [ 'a', 'b' ],
            {'item_type': 'str'}
        )
    ])
    def test_any_list_of_type(self, match_value, match_param):
        matcher_instance = match.AnyListOf(**match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value, match_param",[
        (
            [],
            {'size': 0, 'item_type': None}
        ),
        (
            [1,2,3],
            {'size': 3, 'item_type': 1}
        ),
        (
            [ [], [] ],
            {'size': 2, 'item_type': []}
        ),
        (
            [ 'a', 'b' ],
            {'size': 2, 'item_type': 'str'}
        )
    ])
    def test_any_list_of_size_and_type(self, match_value, match_param):
        matcher_instance = match.AnyListOf(**match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    # --- Negative tests ---
    # ----------------------
    @pytest.mark.parametrize("match_value", (12, True, 'str', None, {}))
    def test_any_list_of_type_mismatch_asserts(self, match_value):
        matcher_instance = match.AnyListOf(3)
        pattern = re.compile(
            'Comparing to List Of matcher.*Type mismatch:.*',
            re.S
        )
        with pytest.raises(AssertionError, match=pattern):
            assert match_value == matcher_instance

        with pytest.raises(AssertionError, match=pattern):
            assert matcher_instance == match_value

    @pytest.mark.parametrize("match_value, match_param",[
        (
            [],
            {'size': 3}
        ),
        (
            [1,2,3],
            {'size': 2}
        ),
        (
            [ [], [] ],
            {'size': 1}
        )
    ])
    def test_any_list_of_size_asserts(self, match_value, match_param):
        matcher_instance = match.AnyListOf(**match_param)
        pattern = re.compile(
            'Comparing to List Of matcher.*Size mismatch.*==.*',
            re.S
        )
        with pytest.raises(AssertionError, match=pattern):
            assert match_value == matcher_instance

        with pytest.raises(AssertionError, match=pattern):
            assert matcher_instance == match_value

    @pytest.mark.parametrize("match_value, match_param",[
        (
            [1,2,3],
            {'item_type': 'str'}
        ),
        (
            [ [], [] ],
            {'item_type': False}
        ),
        (
            [ 'a', 'b' ],
            {'item_type': []}
        )
    ])
    def test_any_list_of_type_asserts(self, match_value, match_param):
        matcher_instance = match.AnyListOf(**match_param)
        pattern = re.compile(
            'Comparing to List Of matcher.*Element type mismatch.*',
            re.S
        )
        with pytest.raises(AssertionError, match=pattern):
            assert match_value == matcher_instance

        with pytest.raises(AssertionError, match=pattern):
            assert matcher_instance == match_value

    @pytest.mark.parametrize("match_value, match_param, expected_msg",[
        (
            # Type mismatch
            [1,2,3],
            {'size': 3, 'item_type': 'str'},
            'Comparing to List Of matcher.*Element type mismatch.*'
        ),
        (
            # Size mismatch
            [ [], [] ],
            {'size': 5, 'item_type': []},
            'Comparing to List Of matcher.*Size mismatch.*==.*'
        ),
        (
            # Not matching size and type
            [ 'a', 'b' ],
            {'size': 55, 'item_type': 1},
            'Comparing to List Of matcher.*Size mismatch.*==.*Element type mismatch.*'
        )
    ])
    def test_any_list_of_size_and_type_asserts(self, match_value, match_param, expected_msg):
        matcher_instance = match.AnyListOf(**match_param)
        pattern = re.compile(expected_msg, re.S)
        with pytest.raises(AssertionError, match=pattern):
            assert match_value == matcher_instance

        with pytest.raises(AssertionError, match=pattern):
            assert matcher_instance == match_value

    # --- Negative on initialization
    @pytest.mark.parametrize("params", ('str', 2.23, [], {}, type))
    @pytest.mark.parametrize("kls", (
        match.AnyListOf,
        match.AnyListLongerThan,
        match.AnyListShorterThan
    ))
    def test_any_list_of_init_fails(self, params, kls):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*size.*item_type.*',
            re.S
        )):
            kls(params, type)


class TestMatcherAnyListOfLongerThan:
    """Tests AnyListOfLongerThan matchers"""
    # --- AnyListLongerThan(size, type)
    @pytest.mark.parametrize("match_value, match_param",[
        (
            [],
            {'size': -1}
        ),
        (
            [1,2,3],
            {'size': 2}
        ),
        (
            [ [], [] ],
            {'size': 1}
        ),
        (
            [ 'a', 'b' ],
            {'size': 0}
        )
    ])
    def test_any_list_longer_than(self, match_value, match_param):
        matcher_instance = match.AnyListLongerThan(**match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value, match_param",[
        (
            [],
            {'size': -1, 'item_type': None}
        ),
        (
            [1,2,3],
            {'size': 2, 'item_type': 1}
        ),
        (
            [ [], [] ],
            {'size': 1, 'item_type': []}
        ),
        (
            [ 'a', 'b' ],
            {'size': 1, 'item_type': 'str'}
        )
    ])
    def test_any_list_longer_than_size_and_type(self, match_value, match_param):
        matcher_instance = match.AnyListLongerThan(**match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    # --- Negative tests ---
    # ----------------------
    @pytest.mark.parametrize("match_value, match_param",[
        (123, {'size': 1}),
        ('str', {'size': 1}),
        ({}, {'size': 1}),
        (False, {'size': 1}),
    ])
    def test_any_list_longer_than_type_mismatch_asserts(self, match_value, match_param):
        matcher_instance = match.AnyListLongerThan(**match_param)
        pattern = re.compile('Comparing to List Of matcher.*Type mismatch:.*', re.S)
        with pytest.raises(AssertionError, match=pattern):
            assert match_value == matcher_instance

        with pytest.raises(AssertionError, match=pattern):
            assert matcher_instance == match_value

    @pytest.mark.parametrize("match_value, match_param, expected_msg",[
        (
            # Type mismatch
            [1,2,3],
            {'size': 3, 'item_type': 'str'},
            'Comparing to List Of matcher.*Element type mismatch.*'
        ),
        (
            # Size mismatch
            [ [], [] ],
            {'size': 5, 'item_type': []},
            'Comparing to List Of matcher.*Size mismatch.*>.*'
        ),
        (
            # Not matching size and type
            [ 'a', 'b' ],
            {'size': 55, 'item_type': 1},
            'Comparing to List Of matcher.*Size mismatch.*>.*Element type mismatch.*'
        )
    ])
    def test_any_list_longer_than_size_and_type_asserts(self, match_value, match_param,
                                                        expected_msg):
        matcher_instance = match.AnyListLongerThan(**match_param)
        pattern = re.compile(expected_msg, re.S)
        with pytest.raises(AssertionError, match=pattern):
            assert match_value == matcher_instance

        with pytest.raises(AssertionError, match=pattern):
            assert matcher_instance == match_value


class TestMatcherAnyListOfShorterThan:
    """Tests AnyListOfShorterThan matchers"""
    # --- AnyListShorterThan(size, type)
    @pytest.mark.parametrize("match_value, match_param",[
        (
            [],
            {'size': 1}
        ),
        (
            [1,2,3],
            {'size': 4}
        ),
        (
            [ [], [] ],
            {'size': 3}
        ),
        (
            [ 'a', 'b' ],
            {'size': 333}
        )
    ])
    def test_any_list_shorter_than(self, match_value, match_param):
        matcher_instance = match.AnyListShorterThan(**match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value, match_param",[
        (
            [],
            {'size': 1, 'item_type': None}
        ),
        (
            [1,2,3],
            {'size': 4, 'item_type': 1}
        ),
        (
            [ [], [] ],
            {'size': 3, 'item_type': []}
        ),
        (
            [ 'a', 'b' ],
            {'size': 143, 'item_type': 'str'}
        )
    ])
    def test_any_list_shorter_than_size_and_type(self, match_value, match_param):
        matcher_instance = match.AnyListShorterThan(**match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    # --- Negative tests ---
    # ----------------------
    @pytest.mark.parametrize("match_value, match_param",[
        (123, {'size': 1}),
        ('str', {'size': 1}),
        ({}, {'size': 1}),
        (False, {'size': 1}),
    ])
    def test_any_list_shorter_than_type_mismatch_asserts(self, match_value, match_param):
        matcher_instance = match.AnyListShorterThan(**match_param)
        pattern = re.compile('Comparing to List Of matcher.*Type mismatch:.*', re.S)
        with pytest.raises(AssertionError, match=pattern):
            assert match_value == matcher_instance

        with pytest.raises(AssertionError, match=pattern):
            assert matcher_instance == match_value

    @pytest.mark.parametrize("match_value, match_param, expected_msg",[
        (
            # Type mismatch
            [1,2,3],
            {'size': 5, 'item_type': 'str'},
            'Comparing to List Of matcher.*Element type mismatch.*'
        ),
        (
            # Size mismatch
            [ [], [] ],
            {'size': 1, 'item_type': []},
            'Comparing to List Of matcher.*Size mismatch.*<.*'
        ),
        (
            # Not matching size and type
            [ 'a', 'b' ],
            {'size': 1, 'item_type': 1},
            'Comparing to List Of matcher.*Size mismatch.*<.*Element type mismatch.*'
        )
    ])
    def test_any_list_shorter_than_size_and_type_asserts(self, match_value, match_param,
                                                        expected_msg):
        matcher_instance = match.AnyListShorterThan(**match_param)
        pattern = re.compile(expected_msg, re.S)
        with pytest.raises(AssertionError, match=pattern):
            assert match_value == matcher_instance

        with pytest.raises(AssertionError, match=pattern):
            assert matcher_instance == match_value


class TestMatcherAnyListOfRange:
    """Tests AnyListOfShorterThan matchers"""
    # --- AnyListOfRange(size, size, type)
    @pytest.mark.parametrize("size_range, value", (
        ((2, 4), list(range(3))),
        ((2, 4), list(range(4))),
        ((2, 4),  list(range(2)))
    ), ids=generate_test_id_for_any_list_of_range)
    def test_any_list_of_range(self, size_range, value):
        matcher_instance = match.AnyListOfRange(*size_range)
        assert value == matcher_instance
        assert matcher_instance == value

    @pytest.mark.parametrize("size_range, item_type, value", (
        ((0,3), 2, [1,2]),
        ((0,3), '', ['a','b']),
        ((0,3), [], [ [1,2], [3,4]])
    ))
    def test_any_list_of_range_and_type(self, size_range, item_type, value):
        matcher_instance = match.AnyListOfRange(*size_range, item_type=item_type)
        assert value == matcher_instance
        assert matcher_instance == value

    # --- Negative tests ---
    # ----------------------
    @pytest.mark.parametrize("params", ('str', 2.23, [], {}, type, None))
    def test_any_list_of_range_than_init_fails(self, params):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*min_size.*max_size.*item_type.*',
            re.S
        )):
            match.AnyListOfRange(params, params, type)

    @pytest.mark.parametrize("size_range, value, expected_error, expected_msg", (
        ((2, 4), list(range(1)),
         AssertionError,
         r'Comparing to List Of Range matcher.*Size mismatch.*size 1.*shorter.*2 el.*'),
        ((2, 4), list(range(8)),
         AssertionError,
         r'Comparing to List Of Range matcher.*Size mismatch.*size 8.*longer.*4 el.*'),
        ((2, 4), list(range(5)),
         AssertionError,
         r'Comparing to List Of Range matcher.*Size mismatch.*size 5.*longer.*4 el.*'),
        ((2, 4), [],
         AssertionError,
         r'Comparing to List Of Range matcher.*Size mismatch.*size 0.*shorter.*2 el.*'),
        ((2, 4), True,
         AssertionError, r'Comparing to List Of Range matcher.*Type mismatch.*'),
        ((2, 4), 'text',
         AssertionError, r'Comparing to List Of Range matcher.*Type mismatch.*'),
        ((2, 4), {'a': 3},
         AssertionError, r'Comparing to List Of Range matcher.*Type mismatch.*'),
        ((2, 4), 555,
         AssertionError, r'Comparing to List Of Range matcher.*Type mismatch.*'),
    ))
    def test_any_list_of_range_fails(self, size_range, value, expected_error, expected_msg):
        with pytest.raises(expected_error, match=re.compile(expected_msg, re.S)):
            matcher_instance = match.AnyListOfRange(*size_range)
            assert matcher_instance == value

        with pytest.raises(expected_error, match=re.compile(expected_msg, re.S)):
            matcher_instance = match.AnyListOfRange(*size_range)
            assert value == matcher_instance

    @pytest.mark.parametrize("size_range, item_type, value", (
        ((0,3), 1, [1, 2, 'str']),
        ((0,3), False, [1, 2]),
        ((0,3), 'str', [1, 2]),
    ))
    def test_any_list_of_range_invalid_elements_type_asserts(self, size_range,
                                                             item_type, value):
        matcher_instance = match.AnyListOfRange(*size_range, item_type=item_type)
        pattern = re.compile(
            'Element type mismatch.*',
            re.S
        )
        with pytest.raises(AssertionError, match=pattern):
            assert value == matcher_instance

        with pytest.raises(AssertionError, match=pattern):
            assert matcher_instance == value

    @pytest.mark.parametrize("size_range, expected_error, expected_msg", (
        ((4, 2), ValueError, 'Invalid matcher range limits!.*'),
        ((2, 2), ValueError, 'Invalid matcher range limits!.*'),
    ))
    def test_any_list_of_range_incorrect_params_fails(self, size_range, expected_error,
                                                      expected_msg):
        with pytest.raises(expected_error, match=re.compile(expected_msg, re.S)):
            match.AnyListOfRange(*size_range)


class TestMatcherAnyListOfMatchers:
    """Tests AnyListOfMatchers matcher"""
    @pytest.mark.parametrize("matcher_item, size, compare_to", (
        pytest.param(match.AnyNumber(), 3, [1,2,3], id='AnyNumber-3'),
        pytest.param(match.AnyNumberGreaterThan(5), 3, [8,12,33], id='AnyNumberGreaterThan5-3'),
        pytest.param(match.AnyNumberLessThan(5), 3, [1,2,3], id='AnyNumberLessThan5-3'),
        pytest.param(match.AnyText(), 2, ["str", "another_str"], id='AnyText-2'),
        pytest.param(match.AnyTextLike(r'\d+'), 2, ["34", "4242"], id='AnyTextLike-2'),
        pytest.param(match.AnyListOf(2, 1), 2, [ [1,2], [0,4] ], id='AnyListOfIntsOfSize-2'),
        pytest.param(match.Anything(), 2, [4, ['str', True]], id='Anything-2'),
        pytest.param(match.AnyListOfMatchers(match.AnyList()), 2, [ [[1,2], [3,4]], [[5, 2]] ],
                     id='AnyListOfMatchers-2')
    ))
    def test_basic(self, matcher_item, size, compare_to):
        matcher_instance = match.AnyListOfMatchers(
            matcher_item, size
        )

        assert matcher_instance == compare_to
        assert compare_to == matcher_instance

    # --- Negative tests
    # ------------------

    # --- Negative on initialization
    @pytest.mark.parametrize("params", ('str', 2.23, [], {}, type))
    @pytest.mark.parametrize("kls", (
        match.AnyListOfMatchers,
        match.AnyListOfMatchersLongerThan,
        match.AnyListOfMatchersShorterThan
    ))
    def test_any_list_of_matchers_init_fails(self, params, kls):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*size.*',
            re.S
        )):
            kls(5, params)
