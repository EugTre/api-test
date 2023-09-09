"""Tests for matchers and matcher manager

pytest -s -vv ./utils/test_matchers.py
"""
import pytest
import utils.matchers as matcher

class TestMatcherManager:
    """Tests for matcher manager"""
    def test_manager_register(self):
        manager = matcher.MatchersManager()
        manager.add(matcher.Anything)

        assert manager.collection
        assert len(manager.collection) == 1

        manager.add(matcher.AnyText)
        assert len(manager.collection) == 2

    def test_manager_register_with_name(self):
        reg_name = "FooBar"
        manager = matcher.MatchersManager()
        manager.add(matcher.Anything, name=reg_name)

        assert manager.collection
        assert len(manager.collection) == 1
        assert reg_name in manager

    def test_manager_register_override(self):
        manager = matcher.MatchersManager()
        manager.add(matcher.Anything)

        assert manager.collection
        assert len(manager.collection) == 1

        manager.add(matcher.Anything, override=True)
        assert len(manager.collection) == 1

    def test_manager_bulk_registration(self):
        manager = matcher.MatchersManager()
        manager.add_all([
            matcher.Anything,
            matcher.AnyNumber,
            matcher.AnyText
        ])

        print(manager.collection)

        assert manager.collection
        assert len(manager.collection) == 3
        assert manager.get(matcher.Anything.__name__)
        assert manager.get(matcher.AnyNumber.__name__)
        assert manager.get(matcher.AnyText.__name__)

    def test_manager_bulk_registration_with_name(self):
        collection = [
            (matcher.Anything, 'Foo1'),
            (matcher.AnyNumber, 'Foo2'),
            (matcher.AnyText, 'Foo3')
        ]
        manager = matcher.MatchersManager()
        manager.add_all(collection)

        assert manager.collection
        assert len(manager.collection) == 3
        assert isinstance(manager.get(collection[0][1]), collection[0][0])
        assert isinstance(manager.get(collection[1][1]), collection[1][0])
        assert isinstance(manager.get(collection[2][1]), collection[2][0])

    def test_manager_unregister(self):
        reg_name = "FooBar"
        manager = matcher.MatchersManager()
        manager.add(matcher.Anything, name=reg_name)

        assert manager.collection
        assert reg_name in manager

        op_result = manager.remove(reg_name)
        assert op_result
        assert not manager.collection
        assert reg_name not in manager

    def test_manager_get_registered_by_name(self):
        reg_name = "FooBar"
        manager = matcher.MatchersManager()
        manager.add(matcher.Anything, name=reg_name)

        assert manager.get(reg_name)
        assert isinstance(manager.get(reg_name), matcher.Anything)

    def test_manager_get_registered_by_autoname(self):
        matcher_kls = matcher.Anything
        kls_name = matcher_kls.__name__

        manager = matcher.MatchersManager()
        manager.add(matcher_kls)

        assert manager.get(kls_name)
        assert isinstance(manager.get(kls_name), matcher.Anything)

    def test_manager_contains(self):
        collection = [
            (matcher.Anything, 'Foo1'),
            (matcher.AnyNumber, 'Foo2'),
            (matcher.AnyText, 'Foo3')
        ]
        manager = matcher.MatchersManager()
        manager.add_all(collection)

        assert collection[0][1] in manager
        assert collection[1][1] in manager
        assert collection[2][1] in manager

    # --- Negative
    def test_manager_get_by_invalid_name_fails(self):
        manager = matcher.MatchersManager()
        manager.add(matcher.AnyText)
        assert manager.collection

        with pytest.raises(ValueError, match='Failed to find matcher with name.*'):
            manager.get("FooBar")

    def test_manager_unregister_by_invalid_name_quietly_fails(self):
        reg_name = "FooBar"
        invalid_name = "BazBar"

        manager = matcher.MatchersManager()
        manager.add(item=matcher.Anything, name=reg_name)
        assert reg_name in manager

        op_result = not manager.remove(invalid_name)
        assert op_result
        assert reg_name in manager
        assert len(manager.collection) == 1

    def test_manager_register_duplicate_fails(self):
        manager = matcher.MatchersManager()
        manager.add(matcher.Anything)

        assert manager.collection
        assert len(manager.collection) == 1

        with pytest.raises(ValueError, match=".* already registered!"):
            manager.add(matcher.Anything)

    def test_manager_register_duplicate_name_fails(self):
        manager = matcher.MatchersManager()
        manager.add(matcher.Anything, "FooBar")

        assert manager.collection
        assert len(manager.collection) == 1

        with pytest.raises(ValueError, match=".* already registered!"):
            manager.add(matcher.AnyText, "FooBar")

    def test_manager_register_non_compatible_type_fails(self):
        manager = matcher.MatchersManager()
        with pytest.raises(ValueError, match="Registraion failed for item.*"):
            manager.add([].__class__, "Foo")

    def test_manager_contains_fails(self):
        collection = [
            (matcher.Anything, 'Foo1'),
            (matcher.AnyNumber, 'Foo2'),
            (matcher.AnyText, 'Foo3')
        ]
        manager = matcher.MatchersManager()
        manager.add_all(collection)

        assert 'Foo' not in manager
        assert 'Foo33' not in manager
        assert 'Bar1' not in manager


class TestMatchersBasic:
    """Positive tests for matchers"""
    @pytest.mark.parametrize("match_value",[
        None,
        "text",
        123,
        123.33,
        [],
        [1,2,3],
        ['a','b'],
        {},
        {"a": 10},
        matcher.Anything()
    ])
    def test_anything(self, match_value):
        matcher_instance = matcher.Anything()
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value",[
        "text", "", "23"
    ])
    def test_any_text(self, match_value):
        matcher_instance = matcher.AnyText()
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
        matcher_instance = matcher.AnyTextLike(matcher_pattern)
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
        matcher_instance = matcher.AnyTextWith(matcher_pattern)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value",[
        0,
        12,
        -12,
        12.345,
        -12.345
    ])
    def test_any_number(self, match_value):
        matcher_instance = matcher.AnyNumber()
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value", [12, 12.22])
    @pytest.mark.parametrize("match_param", [5, 5.22])
    def test_any_number_greater_than(self, match_value, match_param):
        matcher_instance = matcher.AnyNumberGreaterThan(match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value", [5, 5.11])
    @pytest.mark.parametrize("match_param", [12, 12.22])
    def test_any_number_less_than(self, match_value, match_param):
        matcher_instance = matcher.AnyNumberLessThan(match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value",[
        True,
        False
    ])
    def test_any_bool(self, match_value):
        matcher_instance = matcher.AnyBool()
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    @pytest.mark.parametrize("match_value",[
        [],
        [1,2,3],
        ['a', 'b'],
        [ [], [] ]
    ])
    def test_any_list(self, match_value):
        matcher_instance = matcher.AnyList()
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    # --- AnyDict
    @pytest.mark.parametrize("match_value",[
        {},
        {"a": 1, "b": 2}
    ])
    def test_any_dict(self, match_value):
        matcher_instance = matcher.AnyDict()
        assert matcher_instance == match_value
        assert match_value == matcher_instance

    def test_any_non_empty_dict(self):
        matcher_instance = matcher.AnyNonEmptyDict()
        assert matcher_instance == {'a': 1}
        assert {'a': 1} == matcher_instance


class TestMatcherAnyListOf:
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
        matcher_instance = matcher.AnyListOf(**match_param)
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
        matcher_instance = matcher.AnyListOf(**match_param)
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
        matcher_instance = matcher.AnyListOf(**match_param)
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
        matcher_instance = matcher.AnyListLongerThan(**match_param)
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
        matcher_instance = matcher.AnyListLongerThan(**match_param)
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
        matcher_instance = matcher.AnyListShorterThan(**match_param)
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
        matcher_instance = matcher.AnyListShorterThan(**match_param)
        assert matcher_instance == match_value
        assert match_value == matcher_instance


class TestMatcherAnyListOfMatchers:
    @pytest.mark.parametrize("matcher_item, size, compare_to", (
        pytest.param(matcher.AnyNumber(), 3, [1,2,3], id='AnyNumber-3'),
        pytest.param(matcher.AnyNumberGreaterThan(5), 3, [8,12,33], id='AnyNumberGreaterThan5-3'),
        pytest.param(matcher.AnyNumberLessThan(5), 3, [1,2,3], id='AnyNumberLessThan5-3'),
        pytest.param(matcher.AnyText(), 2, ["str", "another_str"], id='AnyText-2'),
        pytest.param(matcher.AnyTextLike(r'\d+'), 2, ["34", "4242"], id='AnyTextLike-2'),
        pytest.param(matcher.AnyListOf(2, 1), 2, [ [1,2], [0,4] ], id='AnyListOfIntsOfSize-2'),
        pytest.param(matcher.Anything(), 2, [4, ['str', True]], id='Anything-2'),
        pytest.param(matcher.AnyListOfMatchers(matcher.AnyList()), 2, [ [[1,2], [3,4]], [[5, 2]] ], id='AnyListOfMatchers-2')
    ))
    def test_basic(self, matcher_item, size, compare_to):
        matcher_instance = matcher.AnyListOfMatchers(
            matcher_item, size
        )

        assert matcher_instance == compare_to
        assert compare_to == matcher_instance


class TestMatcherAnyDictLike:
    def test_basic(self):

        assert [1,2,3] == matcher.AnyListOfMatchers(
            matcher=matcher.AnyText()
        )

        list_to_compare = [
            {"id": 3, "user": 15125, "comments": [1,4,545, 5533]},
            {"id": 5, "user": 'ds', "comments": [524, 1024]},
            {"id": 13, "user": 2442, "comments": [102, 632]}
        ]
        assert list_to_compare == matcher.AnyListOfMatchers(
            matcher={
                "id": matcher.AnyNumber(),
                "user": matcher.AnyNumber(),
                "comments": matcher.AnyListOf(item_type=1)
            },
            size=3
        ), 'Все пропало!'

class TestMatchersNegative:
    """Negative tests for matchers"""

    @pytest.mark.parametrize("match_value",[
        12, 12.33, [], {}, None
    ])
    def test_any_text_not_match(self, match_value):
        matcher_instance = matcher.AnyText()
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
        matcher_instance = matcher.AnyTextLike(matcher_pattern)
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
        matcher_instance = matcher.AnyTextWith(matcher_pattern)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    # Number negative tests
    @pytest.mark.parametrize('match_value', [
        "str", None, [], {}
    ])
    def test_any_number_fails(self, match_value):
        matcher_instance = matcher.AnyNumber()
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    @pytest.mark.parametrize("match_value, match_param", [
        (12, 50),
        (12, 12)
    ])
    def test_any_number_greater_than_fails(self, match_value, match_param):
        matcher_instance = matcher.AnyNumberGreaterThan(match_param)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    @pytest.mark.parametrize("match_value, match_param", [
        (50, 12),
        (12, 12),
        ('str', 12),
        ([1,2], 12),
    ])
    def test_any_number_less_than_fails(self, match_value, match_param):
        matcher_instance = matcher.AnyNumberLessThan(match_param)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    @pytest.mark.parametrize("match_value", [
        0, 1, 123, 'str', '', None, [], {}, [1,2], {'a': 1}
    ])
    def test_any_bool_fails(self, match_value):
        matcher_instance = matcher.AnyBool()
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    # List negative tests
    @pytest.mark.parametrize("match_value",[
        123, 'str', None, {}, False
    ])
    def test_any_list_fails(self, match_value):
        matcher_instance = matcher.AnyList()
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    # --- AnyListOf
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
    def test_any_list_of_size_fails(self, match_value, match_param):
        matcher_instance = matcher.AnyListOf(**match_param)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

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
    def test_any_list_of_type_fails(self, match_value, match_param):
        matcher_instance = matcher.AnyListOf(**match_param)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    @pytest.mark.parametrize("match_value, match_param",[
        (
            # Type mismatch
            [1,2,3],
            {'size': 3, 'item_type': 'str'}
        ),
        (
            # Size mismatch
            [ [], [] ],
            {'size': 5, 'item_type': []}
        ),
        (
            # Not matching size and type
            [ 'a', 'b' ],
            {'size': 55, 'item_type': 1}
        )
    ])
    def test_any_list_of_size_and_type_fails(self, match_value, match_param):
        matcher_instance = matcher.AnyListOf(**match_param)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    # --- AnyListLongerThan(size, type)
    @pytest.mark.parametrize("match_value, match_param",[
        (
            [1,2,3],
            {'size': 3}
        ),
        # Value is not a list:
        (123, {'size': 1}),
        ('str', {'size': 1}),
        ({}, {'size': 1}),
        (False, {'size': 1}),
    ])
    def test_any_list_longer_than_fails(self, match_value, match_param):
        matcher_instance = matcher.AnyListLongerThan(**match_param)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    @pytest.mark.parametrize("match_value, match_param",[
        (
            # Size mismatch
            [1,2,3],
            {'size': 22, 'item_type': 1}
        ),
        (
            # Type mismatch
            [ [], [] ],
            {'size': 1, 'item_type': 1}
        ),
        (
            # Size and type mismatch
            [ 'a', 'b' ],
            {'size': 10, 'item_type': False}
        )
    ])
    def test_any_list_longer_than_size_and_type_fails(self, match_value, match_param):
        matcher_instance = matcher.AnyListLongerThan(**match_param)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    # --- AnyListShorterThan(size, type)
    @pytest.mark.parametrize("match_value, match_param",[
        (
            [1,2,3],
            {'size': 1}
        ),
        # Value is not a list:
        (123, {'size': 1}),
        ('str', {'size': 1}),
        ({}, {'size': 1}),
        (False, {'size': 1}),
    ])
    def test_any_list_shorter_than_fails(self, match_value, match_param):
        matcher_instance = matcher.AnyListShorterThan(**match_param)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    @pytest.mark.parametrize("match_value, match_param",[
         (
            # Size mismatch
            [1,2,3],
            {'size': 1, 'item_type': 1}
        ),
        (
            # Type mismatch
            [ [], [] ],
            {'size': 1, 'item_type': 1}
        ),
        (
            # Size and type mismatch
            [ 'a', 'b' ],
            {'size': 2, 'item_type': False}
        )
    ])
    def test_any_list_shorter_than_size_and_type_fails(self, match_value, match_param):
        matcher_instance = matcher.AnyListShorterThan(**match_param)
        assert matcher_instance != match_value
        assert match_value != matcher_instance

    # Dict negative tests
    def test_any_dict_fails(self):
        matcher_instance = matcher.AnyDict()
        assert matcher_instance != 123
        assert 123 != matcher_instance
        assert matcher_instance != 'asfs'
        assert matcher_instance != [1,2,3]

    def test_any_non_empty_dict_fails(self):
        matcher_instance = matcher.AnyNonEmptyDict()
        assert matcher_instance != {}
        assert {} != matcher_instance
        assert matcher_instance != 'asfs'
        assert matcher_instance != [1,2,3]
