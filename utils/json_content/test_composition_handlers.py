"""Unit tests for Composer class

pytest -s -vv ./utils/json_content/test_composition_handlers.py
"""

import random

import pytest
import utils.matchers.matcher as match
import utils.generators as gen

from .json_wrapper import JsonWrapper
from .composition_handlers import CompositionStatus, \
    ReferenceCompositionHandler, \
    FileReferenceCompositionHandler, \
    IncludeFileCompositionHandler, \
    GeneratorCompositionHandler, \
    MatcherCompositionHandler


# --- Fixtures
# ---
@pytest.fixture(name='ref_handler', scope='session')
def get_ref_handler() -> ReferenceCompositionHandler:
    return ReferenceCompositionHandler(JsonWrapper({
        "a": 100,
        "b": [1, 2, 3],
        "c": {
            "n1": True,
            "n2": {"!ref": "/a"}
        }
    }))

@pytest.fixture(name='file_ref_handler', scope='session')
def get_file_ref_handler() -> FileReferenceCompositionHandler:
    return FileReferenceCompositionHandler()

@pytest.fixture(name='include_file_handler', scope='session')
def get_include_file_handler() -> IncludeFileCompositionHandler:
    return IncludeFileCompositionHandler()

@pytest.fixture(name='generator_handler', scope='session')
def get_generator_handler() -> GeneratorCompositionHandler:
    manager = gen.GeneratorsManager(False)
    manager.add_all([
        (TestGeneratorCompositionHandler.gen_random_number, 'RandomNumber'),
        (TestGeneratorCompositionHandler.gen_random_in_range, "RandomInRange"),
        (TestGeneratorCompositionHandler.gen_random_name, "FirstName")
    ])
    return GeneratorCompositionHandler(manager)


# --- Tests
# ---
class TestReferenceCompositionHandler:
    """Tests for ReferenceCompositionHandler"""
    def test_create(self):
        """Ref composer creates with no error"""
        assert ReferenceCompositionHandler(content_context=JsonWrapper({"a": 1}))

    def test_matches(self, ref_handler: ReferenceCompositionHandler):
        """Ref composition matches to RefHandler expected syntax"""
        assert ref_handler.match({"!ref": "/a/b/c"})

    @pytest.mark.parametrize('input_value, expected_pointer', [
        ({"!ref": "/a"}, "/a"),
        ({"!ref": "/b/2"}, "/b/2"),
        ({"!ref": "/c"}, "/c"),
        ({"!ref": "/c/n1"}, "/c/n1"),
    ])
    def test_compose(self, input_value, expected_pointer,
                     ref_handler: ReferenceCompositionHandler):
        """Ref composition handled successfully - return value at
        given pointer"""
        result, value = ref_handler.compose(input_value)
        assert result == CompositionStatus.SUCCESS
        assert value == ref_handler.content_context.get(expected_pointer)

    def test_compose_with_unexpected_args(
        self, ref_handler: ReferenceCompositionHandler
    ):
        """Composition args are ignored"""
        result, value = ref_handler.compose({
            "!ref": "/a",
            "!args": [1, 2, 3],
            # "stuff": "kek"
        })
        assert result == CompositionStatus.SUCCESS
        assert value == ref_handler.content_context.get("/a")

    @pytest.mark.parametrize("content, ref_composition, expected", [
        (
            {"a": {"a1": 100, "a2": True}},
            {"!ref": "/a", "a1": 300, "a3": "string"},
            {"a1": 300, "a2": True, "a3": "string"}
        ),
        (
            {"a": {"a1": 100, "a2": {"b1": 300}}},
            {"!ref": "/a", "a1": 300, "a2": {"b1": 100}},
            {"a1": 300, "a2": {"b1": 100}}
        ),
        (
            {"a": {"a1": 100, "a2": {"b1": 300}}},
            {"!ref": "/a", "a2": {"b2": 100}},
            {"a1": 100, "a2": {"b1": 300, "b2": 100}}
        ),
        (
            {"a": {"a1": 100}},
            {"!ref": "/a", "a2": {"b2": 100}},
            {"a1": 100, "a2": {"b2": 100}}
        )
    ], ids=[
        "PlainDictAddUpdate",
        "NestedDictUpdate",
        "NestedDictAddUpdate",
        "AddDict"
    ])
    def test_compose_and_merge(self, content, ref_composition, expected):
        """Ref composition with kwargs update referenced dict value"""
        ref_handler = ReferenceCompositionHandler(JsonWrapper(content))
        result, value = ref_handler.compose(ref_composition)

        assert result == CompositionStatus.SUCCESS
        assert value == expected

    # --- Negative
    @pytest.mark.parametrize('input_value', [
        {"!ref": "/x"},
        {"!ref": "/b/6"},
        {"!ref": "/c/n1/3"},
        {"!ref": "/c/n1/x"}
    ])
    def test_compose_on_missing_pointer_quitely_fails(
        self, input_value, ref_handler: ReferenceCompositionHandler
    ):
        result, value = ref_handler.compose(input_value)
        assert result == CompositionStatus.RETRY
        assert value is None

    def test_compose_on_invalid_pointer_fails(self, ref_handler):
        with pytest.raises(ValueError, match='Invalid JSON Pointer .*'):
            ref_handler.compose({"!ref": "invalid one"})


class TestFileReferenceCompositionHandler:
    """Tests for FileReferenceCompositionHandler"""
    def test_create(self):
        assert FileReferenceCompositionHandler()

    def test_create_wtih_cache(self):
        assert FileReferenceCompositionHandler(use_cache=True)

    def test_matches(self, file_ref_handler):
        assert file_ref_handler.match({
            "!file": "foo.bar"
        })

    def test_compose(self, json_file, file_ref_handler):
        input_value = {"!file": str(json_file)}
        content = {"a": 100}
        json_file.write_as_json(content)

        composition_result, composed_value = file_ref_handler.compose(input_value)
        assert composition_result == CompositionStatus.SUCCESS
        assert composed_value == content

    def test_compose_and_cache(self, json_file):
        input_value = {"!file": str(json_file)}
        content = {"a": 100}
        json_file.append_as_json(content)

        handler = FileReferenceCompositionHandler(use_cache=True)

        result1, value1 = handler.compose(input_value)
        assert result1 == CompositionStatus.SUCCESS
        assert value1 == content

        # Change file and try to read composition again
        json_file.append_text("extra text")
        result2, value2 = handler.compose(input_value)
        assert result2 == CompositionStatus.SUCCESS
        assert value1 == value2

    def test_compose_with_unexpected_args(self, json_file, file_ref_handler):
        content = {"a": 100}
        json_file.append_as_json(content)
        result, value = file_ref_handler.compose({
            "!file": str(json_file),
            "!args": [1,2,3],
            "size": 100500
        })

        assert result == CompositionStatus.SUCCESS
        assert value == content

    # --- Negative
    @pytest.mark.parametrize('input_value', [
        {"!fil": "Anything"},
        {"!faile": "Anything"},
        {"file": "Anything"}
    ])
    def test_match_fails(self, input_value, file_ref_handler):
        assert not file_ref_handler.match(input_value)

    def test_compose_file_not_found_fails(self, file_ref_handler):
        with pytest.raises(FileNotFoundError, match='DataReader failed to find ".*" file'):
            file_ref_handler.compose({"!file": "Unknown"})


class TestIncludeFileCompositionHandler:
    """Tests IncludeFileCompositionHandler"""
    def test_create(self):
        assert IncludeFileCompositionHandler()

    def test_create_with_cache(self):
        assert IncludeFileCompositionHandler(use_cache=True)

    def test_matches(self, include_file_handler):
        assert include_file_handler.match({
            "!include": "foo.bar"
        })

    def test_compose(self, json_file, include_file_handler):
        input_value = {"!include": str(json_file)}
        content = {"a": 100}
        json_file.write_as_json(content)

        result, result_value = include_file_handler.compose(input_value)
        assert result == CompositionStatus.COMPLETED
        assert result_value == content

    def test_compose_and_cache(self, json_file):
        input_value = {"!include": str(json_file)}
        content = {"a": 100}
        json_file.write_as_json(content)

        handler = IncludeFileCompositionHandler(use_cache=True)

        result1, value1 = handler.compose(input_value)
        assert result1 == CompositionStatus.COMPLETED
        assert value1 == content

        # Change file and try to read composition again
        json_file.append_text("extra text")
        result2, value2 = handler.compose(input_value)
        assert result2 == CompositionStatus.COMPLETED
        assert value1 == value2

    def test_compose_with_unexpected_args(self, json_file, include_file_handler):
        content = {"a": 100}
        json_file.append_as_json(content)
        result, value = include_file_handler.compose({
            "!include": str(json_file),
            "!args": [1,2,3],
            "size": 100500
        })

        assert result == CompositionStatus.COMPLETED
        assert value == content

    def test_compose_by_explicit_json_format(self, include_file_handler, get_file):
        content = {"a": 100}
        file = get_file(ext='txt')
        file.write_as_json(content)

        result, value = include_file_handler.compose({
            "!include": str(file),
            "!format": "json"
        })
        assert result == CompositionStatus.COMPLETED
        assert value == content

    def test_compose_by_explicit_txt_format(self, include_file_handler, get_file):
        content = "Some text as content"
        file = get_file(ext='json')
        file.append_text(content)

        result, value = include_file_handler.compose({
            "!include": str(file),
            "!format": "txt"
        })
        assert result == CompositionStatus.COMPLETED
        assert value == content

    def test_compose_with_compose_flag(self, include_file_handler, json_file):
        content = {
            "a": 100,
            "b": {"!ref": "/a"}
        }
        json_file.write_as_json(content)

        result, value = include_file_handler.compose({
            "!include": str(json_file),
            "!compose": True
        })

        assert result == CompositionStatus.COMPOSE_IN_SEPARATE_CONTEXT
        assert value == content

    # --- Negative
    @pytest.mark.parametrize('input_value', [
        {"!incl": "Anything"},
        {"!includ": "Anything"},
        {"include": "Anything"}
    ])
    def test_match_fails(self, input_value, include_file_handler):
        assert not include_file_handler.match(input_value)

    def test_compose_file_not_found_fails(self, include_file_handler):
        with pytest.raises(FileNotFoundError, match='DataReader failed to find ".*" file'):
            include_file_handler.compose({"!include": "Unknown"})


class TestGeneratorCompositionHandler:
    """Tests for GeneratorCompositionHandler"""
    @staticmethod
    def gen_random_number():
        return random.randint(0, 100)

    @staticmethod
    def gen_random_in_range(minimum=0, maximum=100):
        return random.randrange(minimum, maximum)

    @staticmethod
    def gen_random_name(minimum=0, maximum=100):
        return random.choice(['Alex', 'John', 'Casey'])

    def test_create_no_manager(self):
        assert GeneratorCompositionHandler()

    def test_create_with_manager(self):
        assert GeneratorCompositionHandler(gen.GeneratorsManager())

    def test_matches(self, generator_handler):
        assert generator_handler.match({
            "!gen": "FirstName",
            "!args": [1,2,3],
            "kwarg1": 1
        })

    @pytest.mark.parametrize("input_value, expected", [
        ({"!gen": "RandomNumber"}, int),
        ({"!gen": "FirstName"}, str),
        ({"!gen": "RandomInRange", "!args": [50, 100]}, int),
        ({"!gen": "RandomInRange", "minimum": 50, "maximum": 55}, int)
    ])
    def test_compose(self, input_value, expected, generator_handler):
        composition_result, composed_value = generator_handler.compose(input_value)
        assert composition_result == CompositionStatus.SUCCESS
        assert isinstance(composed_value, expected)

    def test_compose_with_same_correlation_id_identical_result(self,
                                generator_handler: GeneratorCompositionHandler):
        cid = "FooBar"
        result, value1 = generator_handler.compose({
            "!gen": "RandomNumber",
            "!id": cid
        })
        assert result == CompositionStatus.SUCCESS

        result, value2 = generator_handler.compose({
            "!gen": "RandomNumber",
            "!id": cid
        })
        assert result == CompositionStatus.SUCCESS
        assert value1 == value2


    # --- Negative
    @pytest.mark.parametrize('input_value', [
        {"!genz": "Anything", "!args": [1,2,3], "kwarg1": 1},
        {"gen": "Anything"}
    ])
    def test_match_fails(self, input_value, generator_handler):
        assert not generator_handler.match(input_value)

    def test_compose_by_unknown_generator_fails(self, generator_handler):
        with pytest.raises(ValueError, match='Failed to find generator with name .*'):
            generator_handler.compose({
                "!gen": "Unknown",
                "!args": [1,2,3]
            })

    def test_compose_with_unexpected_args_fails(self, generator_handler):
        with pytest.raises(TypeError):
            generator_handler.compose({
                "!gen": "RandomNumber",
                "!args": [1,2,3],
                "size": 100500
            })


class TestMatcherCompositionHandler:
    """Tests for MatcherCompositionHandler"""
    manager = match.MatchersManager()

    def test_create(self):
        assert MatcherCompositionHandler(self.manager)

    def test_matches(self):
        handler = MatcherCompositionHandler(self.manager)
        assert handler.match({
            "!match": "Anything",
            "!args": [1,2,3],
            "kwarg1": 1
        })

    @pytest.mark.parametrize("input_value, expected", [
        ({"!match": "Anything"}, match.Anything()),
        ({"!match": "AnyText"}, match.AnyText()),
        ({"!match": "AnyTextLike", "!args": [".*"]}, match.AnyTextLike('.*')),
        ({"!match": "AnyNumberGreaterThan", "!args": [10]}, match.AnyNumberGreaterThan(10)),
        ({"!match": "AnyNumberGreaterThan", "number": 10}, match.AnyNumberGreaterThan(10)),
        ({"!match": "AnyListOf", "!args": [5, "str"]}, match.AnyListOf(5, '')),
        ({"!match": "AnyListOf", "size": 5, "item_type": 3},
         match.AnyListOf(size=5, item_type=3))
    ])
    def test_compose(self, input_value, expected):
        handler = MatcherCompositionHandler(self.manager)
        composition_result, composed_value = handler.compose(input_value)

        assert composition_result == CompositionStatus.SUCCESS
        assert composed_value == expected

    # --- Negative
    @pytest.mark.parametrize('input_value', [
        {"!matchx": "Anything", "!args": [1,2,3], "kwarg1": 1},
        {"match": "Anything"}
    ])
    def test_match_fails(self, input_value):
        handler = MatcherCompositionHandler(self.manager)
        assert not handler.match(input_value)

    def test_compose_by_unknown_matcher_fails(self):
        handler = MatcherCompositionHandler(self.manager)
        with pytest.raises(ValueError, match='Failed to find matcher with name .*'):
            handler.compose({
                "!match": "UnknownMatcher",
                "!args": [1,2,3]
            })
