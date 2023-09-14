"""Tests for matchers and matcher manager

pytest -s -vv ./utils/test_matchers.py
"""
import datetime
import re

import pytest
import utils.matchers as match

class TestMatcherManager:
    """Tests for matcher manager"""
    def test_manager_create_with_defaults(self):
        manager = match.MatchersManager()
        assert hasattr(manager, 'collection')
        assert manager.collection is not None
        assert len(manager.collection) > 0

    def test_manager_create_with_no_defaults(self):
        manager = match.MatchersManager(False)
        assert hasattr(manager, 'collection')
        assert manager.collection is not None
        assert len(manager.collection) == 0

    def test_manager_register(self):
        manager = match.MatchersManager(False)
        manager.add(match.Anything)

        assert manager.collection
        assert len(manager.collection) == 1

        manager.add(match.AnyText)
        assert len(manager.collection) == 2

    def test_manager_register_with_name(self):
        reg_name = "FooBar"
        manager = match.MatchersManager(False)
        manager.add(match.Anything, name=reg_name)

        assert manager.collection
        assert len(manager.collection) == 1
        assert reg_name in manager

    def test_manager_register_override(self):
        manager = match.MatchersManager(False)
        manager.add(match.Anything)

        assert manager.collection
        assert len(manager.collection) == 1

        manager.add(match.Anything, override=True)
        assert len(manager.collection) == 1

    def test_manager_bulk_registration(self):
        manager = match.MatchersManager(False)
        manager.add_all([
            match.Anything,
            match.AnyNumber,
            match.AnyText
        ])

        print(manager.collection)

        assert manager.collection
        assert len(manager.collection) == 3
        assert manager.get(match.Anything.__name__)
        assert manager.get(match.AnyNumber.__name__)
        assert manager.get(match.AnyText.__name__)

    def test_manager_bulk_registration_with_name(self):
        collection = [
            (match.Anything, 'Foo1'),
            (match.AnyNumber, 'Foo2'),
            (match.AnyText, 'Foo3')
        ]
        manager = match.MatchersManager(False)
        manager.add_all(collection)

        assert manager.collection
        assert len(manager.collection) == 3
        assert isinstance(manager.get(collection[0][1]), collection[0][0])
        assert isinstance(manager.get(collection[1][1]), collection[1][0])
        assert isinstance(manager.get(collection[2][1]), collection[2][0])

    def test_manager_unregister(self):
        reg_name = "FooBar"
        manager = match.MatchersManager(False)
        manager.add(match.Anything, name=reg_name)

        assert manager.collection
        assert reg_name in manager

        op_result = manager.remove(reg_name)
        assert op_result
        assert not manager.collection
        assert reg_name not in manager

    def test_manager_get_registered_by_name(self):
        reg_name = "FooBar"
        manager = match.MatchersManager(False)
        manager.add(match.Anything, name=reg_name)

        assert manager.get(reg_name)
        assert isinstance(manager.get(reg_name), match.Anything)

    def test_manager_get_registered_by_autoname(self):
        matcher_kls = match.Anything
        kls_name = matcher_kls.__name__

        manager = match.MatchersManager(False)
        manager.add(matcher_kls)

        assert manager.get(kls_name)
        assert isinstance(manager.get(kls_name), match.Anything)

    def test_manager_contains(self):
        collection = [
            (match.Anything, 'Foo1'),
            (match.AnyNumber, 'Foo2'),
            (match.AnyText, 'Foo3')
        ]
        manager = match.MatchersManager(False)
        manager.add_all(collection)

        assert collection[0][1] in manager
        assert collection[1][1] in manager
        assert collection[2][1] in manager

    # --- Negative
    def test_manager_get_by_invalid_name_fails(self):
        manager = match.MatchersManager(False)
        manager.add(match.AnyText)
        assert manager.collection

        with pytest.raises(ValueError, match='Failed to find matcher with name.*'):
            manager.get("FooBar")

    def test_manager_unregister_by_invalid_name_quietly_fails(self):
        reg_name = "FooBar"
        invalid_name = "BazBar"

        manager = match.MatchersManager(False)
        manager.add(item=match.Anything, name=reg_name)
        assert reg_name in manager

        op_result = not manager.remove(invalid_name)
        assert op_result
        assert reg_name in manager
        assert len(manager.collection) == 1

    def test_manager_register_duplicate_fails(self):
        manager = match.MatchersManager(False)
        manager.add(match.Anything)

        assert manager.collection
        assert len(manager.collection) == 1

        with pytest.raises(ValueError, match=".* already registered!"):
            manager.add(match.Anything)

    def test_manager_register_duplicate_name_fails(self):
        manager = match.MatchersManager(False)
        manager.add(match.Anything, "FooBar")

        assert manager.collection
        assert len(manager.collection) == 1

        with pytest.raises(ValueError, match=".* already registered!"):
            manager.add(match.AnyText, "FooBar")

    def test_manager_register_non_compatible_type_fails(self):
        manager = match.MatchersManager(False)
        with pytest.raises(ValueError, match="Registraion failed for item.*"):
            manager.add([].__class__, "Foo")

    def test_manager_contains_fails(self):
        collection = [
            (match.Anything, 'Foo1'),
            (match.AnyNumber, 'Foo2'),
            (match.AnyText, 'Foo3')
        ]
        manager = match.MatchersManager(False)
        manager.add_all(collection)

        assert 'Foo' not in manager
        assert 'Foo33' not in manager
        assert 'Bar1' not in manager


class TestSimpleMatchers:
    """Positive tests for matchers"""
    @pytest.mark.parametrize("match_value",[
        "text",
        False,
        123,
        123.33,
        [],
        [1,2,3],
        ['a','b'],
        {},
        {"a": 10},
        match.Anything()
    ])
    def test_anything(self, match_value):
        """Anything matches to any non-None value"""
        matcher_instance = match.Anything()
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value",[
        True,
        False
    ])
    def test_any_bool(self, match_value):
        matcher_instance = match.AnyBool()
        assert matcher_instance == match_value
        assert match_value == matcher_instance

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

    # --- AnyDict
    @pytest.mark.parametrize("match_value",[
        {},
        {"a": 1, "b": 2}
    ])
    def test_any_dict(self, match_value):
        matcher_instance = match.AnyDict()
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    def test_any_non_empty_dict(self):
        matcher_instance = match.AnyNonEmptyDict()
        assert matcher_instance == {'a': 1}
        assert {'a': 1} == matcher_instance

    # Negative test
    # -------------
    def test_anything_fails(self):
        """Anything fails to match None"""
        compare_to = None
        matcher_instance = match.Anything()
        pattern = re.compile(r'Comparing to Anything matcher:.*', re.S)
        with pytest.raises(AssertionError, match=pattern):
            assert matcher_instance == compare_to

        with pytest.raises(AssertionError, match=pattern):
            assert compare_to == matcher_instance

    @pytest.mark.parametrize("match_value", [
        0, 1, 123, 'str', '', None, [], {}, [1,2], {'a': 1}
    ])
    def test_any_bool_fails(self, match_value):
        matcher_instance = match.AnyBool()
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    # List negative tests
    @pytest.mark.parametrize("match_value",[
        123, 'str', None, {}, False
    ])
    def test_any_list_fails(self, match_value):
        matcher_instance = match.AnyList()
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    # Dict negative tests
    @pytest.mark.parametrize("compare_to", (
        123,
        [1,2,3],
        False,
        "Str"
    ))
    def test_any_dict_fails(self, compare_to):
        matcher_instance = match.AnyDict()
        with pytest.raises(AssertionError):
            assert matcher_instance == compare_to

        with pytest.raises(AssertionError):
            assert compare_to == matcher_instance

    @pytest.mark.parametrize("compare_to", (
        {},
        123,
        [1,2,3],
        False,
        "Str"
    ))
    def test_any_non_empty_dict_fails(self, compare_to):
        matcher_instance = match.AnyNonEmptyDict()
        with pytest.raises(AssertionError):
            assert matcher_instance == compare_to

        with pytest.raises(AssertionError):
            assert compare_to == matcher_instance


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

def generate_test_id_for_any_list_of_range(val):
    if isinstance(val, tuple):
        return f'{val[0]}_{val[1]}'
    return str(val)

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

    # --- Negative tests
    # --- AnyListOf
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

    # --- AnyListLongerThan(size, type)
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

    # --- AnyListShorterThan(size, type)
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

    @pytest.mark.parametrize("params", ('str', 2.23, [], {}, type, None))
    def test_any_list_longer_than_init_fails(self, params):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*min_size.*max_size.*item_type.*',
            re.S
        )):
            match.AnyListOfRange(params, params, type)

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

class TestMatcherDate:
    """Test for Date Matchers"""
    PAST_DATES = (
        '2020-03-04',
        '20111104',
        '2011-11-04T00:05:23',
        '2011-11-04T00:05:23Z',
        '20111104T000523',
        '2011-11-04 00:05:23.283',
        '2011-11-04 00:05:23.283+00:00',
        '2011-11-04T00:05:23+04:00'
    )
    FUTURE_DATES = (
        '2040-03-04',
        '20411104',
        '2041-11-04T00:05:23',
        '2041-11-04T00:05:23Z',
        '20411104T000523',
        '2040-11-04 00:05:23.283',
        '2040-11-04 00:05:23.283+00:00',
        '2040-11-04T00:05:23+04:00'
    )

    """Tests date matchers"""
    @pytest.mark.parametrize("compare_to", PAST_DATES)
    def test_any_date(self, compare_to):
        matcher_instance = match.AnyDate()
        assert matcher_instance == compare_to
        assert compare_to == matcher_instance

    # Any Date Before
    @pytest.mark.parametrize('date', (
        'now',
        '+5s', '-5s',
        '+5m', '-5m',
        '+5h', '-5h',
        '+1d', '-1d',
        '+1y', '-1y',
        "2022-01-01T00:40:00Z"
    ))
    @pytest.mark.parametrize("compare_to", PAST_DATES)
    def test_any_date_before(self, date, compare_to):
        matcher_instance = match.AnyDateBefore(date)
        assert matcher_instance == compare_to
        assert compare_to == matcher_instance

    @pytest.mark.parametrize("before_date, compare_to", (
        (
            datetime.datetime(2023, 10, 15, 12, 30, 55, 556124).isoformat(),
            datetime.datetime(2023, 10, 15, 12, 30, 55, 556123).isoformat()
        ),
        (
            datetime.datetime(2023, 10, 15, 12, 30, 55, 556123).isoformat(),
            datetime.datetime(2023, 10, 15, 12, 30, 54, 556123).isoformat()
        ),
    ), ids=["milliseconds", "seconds"])
    def test_any_date_before_precise(self, before_date, compare_to):
        matcher_instance = match.AnyDateBefore(before_date)
        assert matcher_instance == compare_to
        assert compare_to == matcher_instance

    @pytest.mark.parametrize("offset", (
        '+500ms',
        '+1s',
        '+1.5s',
        '+1m',
        '+1.5m',
        '+1.23h',
        '+2d',
        '+1y',
    ))
    def test_any_date_before_by_offset_to_now(self, offset):
        utc = datetime.timezone.utc
        matcher_instance = match.AnyDateBefore(offset)
        assert matcher_instance == datetime.datetime.now(utc).isoformat()
        assert datetime.datetime.now(utc).isoformat() == matcher_instance

    # Any Date After
    @pytest.mark.parametrize('date', (
        'now',
        '+5s', '-5s',
        '+5m', '-5m',
        '+5h', '-5h',
        '+1d', '-1d',
        '+1y', '-1y',
        "2023-01-01T00:40:00Z"
    ))
    @pytest.mark.parametrize("compare_to", FUTURE_DATES)
    def test_any_date_after(self, date, compare_to):
        matcher_instance = match.AnyDateAfter(date)
        assert matcher_instance == compare_to
        assert compare_to == matcher_instance

    @pytest.mark.parametrize("after_date, compare_to", (
        (
            datetime.datetime(2023, 10, 15, 12, 30, 55, 556123).isoformat(),
            datetime.datetime(2023, 10, 15, 12, 30, 55, 556124).isoformat()
        ),
        (
            datetime.datetime(2023, 10, 15, 12, 30, 54, 556123).isoformat(),
            datetime.datetime(2023, 10, 15, 12, 30, 55, 556123).isoformat()
        ),
    ), ids=["milliseconds", "seconds"])
    def test_any_date_after_precise(self, after_date, compare_to):
        matcher_instance = match.AnyDateAfter(after_date)
        assert matcher_instance == compare_to
        assert compare_to == matcher_instance

    @pytest.mark.parametrize("offset", (
        '-500ms',
        '-1s',
        '-1.5s',
        '-1m',
        '-1.5m',
        '-1.23h',
        '-2d',
        '-1y',
    ))
    def test_any_date_after_by_offset_to_now(self, offset):
        utc = datetime.timezone.utc
        matcher_instance = match.AnyDateAfter(offset)
        assert matcher_instance == datetime.datetime.now(utc).isoformat()
        assert datetime.datetime.now(utc).isoformat() == matcher_instance

    # Any Date In Range
    @pytest.mark.parametrize("left, right", (
        ('-1d', '+1d'),
        ('-1y', '+1y'),
        ('-1s', '+1s'),
        ('now', '+1d'),
        ('-1d', 'now')
    ))
    def test_any_date_in_range(self, left, right):
        matcher_instance = match.AnyDateInRange(left, right)
        assert matcher_instance == datetime.datetime.now().isoformat()

    @pytest.mark.parametrize("left, right, exception, match_pattern", (
        ('+1d', '+2d', AssertionError, r'.*Date In Range.*earlier than.*left limit'),
        ('+100ms', '+500ms', AssertionError, r'.*Date In Range.*earlier than.*left limit'),
        ('-2d', '-1d', AssertionError,r'.*Date In Range.*later than.*right limit'),
        ('-500ms', '-100ms', AssertionError,r'.*Date In Range.*later than.*right limit'),
        ('+100ms', '-100ms', ValueError,
            r'Invalid matcher range limits!.*')
    ))
    def test_any_date_in_range_fails(self, left, right, exception, match_pattern):
        with pytest.raises(exception, match=re.compile(match_pattern, re.S)):
            matcher_instance = match.AnyDateInRange(left, right)
            assert matcher_instance == datetime.datetime.now().isoformat()

    # --- Negative tests
    # ------------------
    @pytest.mark.parametrize("compare_to", (
        12412,
        [1,2,3],
        'kkk',
        -414.424,
        True
    ))
    def test_any_date_fails(self, compare_to):
        matcher_instance = match.AnyDate()
        with pytest.raises(AssertionError):
            assert matcher_instance == compare_to

        with pytest.raises(AssertionError):
            assert compare_to == matcher_instance

    @pytest.mark.parametrize('date', (
        'now',
        '+5s', '-5s',
        '+5m', '-5m',
        '+5h', '-5h',
        '+1d', '-1d',
        '+1y', '-1y',
        "2022-01-01T00:40:00Z"
    ))
    @pytest.mark.parametrize("compare_to", FUTURE_DATES)
    def test_any_date_before_fails(self, date, compare_to):
        matcher_instance = match.AnyDateBefore(date)
        with pytest.raises(AssertionError):
            assert matcher_instance == compare_to

        with pytest.raises(AssertionError):
            assert compare_to == matcher_instance

    @pytest.mark.parametrize('date', (
        'now',
        '+5s', '-5s',
        '+5m', '-5m',
        '+5h', '-5h',
        '+1d', '-1d',
        '+1y', '-1y',
        "2023-01-01T00:40:00Z"
    ))
    @pytest.mark.parametrize("compare_to", PAST_DATES)
    def test_any_date_after_fails(self, date, compare_to):
        matcher_instance = match.AnyDateAfter(date)
        with pytest.raises(AssertionError):
            assert matcher_instance == compare_to

        with pytest.raises(AssertionError):
            assert compare_to == matcher_instance

    # --- Negative on initialization
    @pytest.mark.parametrize("params", (12, 2.23, [], {}, type, False, None))
    @pytest.mark.parametrize("kls", (
        match.AnyDateAfter,
        match.AnyDateBefore
    ))
    def test_any_date_before_after_init_fails(self, params, kls):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*date.*',
            re.S
        )):
            kls(params)

    @pytest.mark.parametrize("params", (12, 2.23, [], {}, type, False, None))
    def test_any_date_in_range_init_fails(self, params):
        with pytest.raises(TypeError, match=re.compile(
            'Matcher initialized with invalid types of parameters.*date_from.*date_to.*',
            re.S
        )):
            match.AnyDateInRange(params, params)
