"""Tests for matchers and matcher manager

pytest -s -vv ./utils/matchers/
"""
import re

import pytest
import utils.matchers.matcher as match

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
