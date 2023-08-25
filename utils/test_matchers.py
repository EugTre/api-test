"""Tests for matchers and matcher manager

pytest -s -vv ./utils/test_matchers.py

"""
import pytest
import utils.matchers as matcher

class TestMatcherManager:
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


class TestMatchers:
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
    def test_any(self, match_value):
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

    # TODO:
    # AnyTextWith(contains)
    # AnyNumber
    # AnyNumberGreaterThan(size)
    # AnyNumberLessThan(size)
    # AnyBool
    # AnyList
    # AnyListOf(size, type)
    # AnyListLongerThan(size, type)
    # AnyListShorterThan(size, type)
    # AnyDict
    # AnyNonEmptyDict


    # --- Negative tests
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
        ('text', '[0-9]+')
    ])
    def test_any_text_like_not_match(self, match_value, matcher_pattern):
        matcher_instance = matcher.AnyTextLike(matcher_pattern)
        assert matcher_instance != match_value
        assert match_value != matcher_instance
