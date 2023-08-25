"""Unit tests for Composer class

pytest -s -vv ./utils/json_content/test_composition_handlers.py
"""

import random

import pytest
from utils.json_content.composition_handlers import ReferenceCompositionHandler, \
    FileReferenceCompositionHandler, GeneratorCompositionHandler, \
    MatcherCompositionHandler
from utils.json_content.json_wrapper import JsonWrapper
from utils import matchers
import utils.generators as gen


# --- Fixtures
# ---
@pytest.fixture(name='ref_handler', scope='session')
def get_ref_handler() -> ReferenceCompositionHandler:
    return ReferenceCompositionHandler(JsonWrapper({
        "a": 100,
        "b": [1,2,3],
        "c": {
            "n1": True,
            "n2": {"!ref": "/a"}
        }
    }))

@pytest.fixture(name='file_ref_handler', scope='session')
def get_file_ref_handler() -> FileReferenceCompositionHandler:
    return FileReferenceCompositionHandler()

@pytest.fixture(name='generator_handler', scope='session')
def get_generator_handler() -> GeneratorCompositionHandler:
    manager = gen.GeneratorsManager()
    manager.add_all([
        (TestGeneratorCompositionHandler.gen_random_number, 'RandomNumber'),
        (TestGeneratorCompositionHandler.gen_random_in_range, "RandomInRange"),
        (gen.NamesGenerator.generate_first_name, "FirstName")
    ])
    return GeneratorCompositionHandler(manager)

# --- Tests
# ---
class TestReferenceCompositionHandler:
    """Tests for ReferenceCompositionHandler"""
    def test_create(self):
        assert ReferenceCompositionHandler(content_context=JsonWrapper({"a": 1}))

    def test_matches(self, ref_handler: ReferenceCompositionHandler):
        assert ref_handler.match({"!ref": "/a/b/c"})

    @pytest.mark.parametrize('input_value, expected_pointer', [
        ({"!ref": "/a"}, "/a"),
        ({"!ref": "/b/2"}, "/b/2"),
        ({"!ref": "/c"}, "/c"),
        ({"!ref": "/c/n1"}, "/c/n1"),
    ])
    def test_compose(self, input_value, expected_pointer, ref_handler: ReferenceCompositionHandler):
        result, value = ref_handler.compose(input_value)
        assert result
        assert value == ref_handler.content_context.get(expected_pointer)

    def test_compose_with_unexpected_args(self, ref_handler: ReferenceCompositionHandler):
        result, value = ref_handler.compose({"!ref": "/a", "!args": [1,2,3], "stuff": "kek"})
        assert result
        assert value == ref_handler.content_context.get("/a")

    # --- Negative
    @pytest.mark.parametrize('input_value', [
        {"!ref": "/x"},
        {"!ref": "/b/6"},
        {"!ref": "/c/n1/3"},
        {"!ref": "/c/n1/x"}
    ])
    def test_compose_on_missing_pointer_quitely_fails(self, input_value,
                                                      ref_handler: ReferenceCompositionHandler):
        result, value = ref_handler.compose(input_value)
        assert not result
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
        json_file.append_as_json(content)

        composition_result, composed_value = file_ref_handler.compose(input_value)
        assert composition_result
        assert composed_value == content

    def test_compose_and_cache(self, json_file):
        input_value = {"!file": str(json_file)}
        content = {"a": 100}
        json_file.append_as_json(content)

        handler = FileReferenceCompositionHandler(use_cache=True)

        result1, value1 = handler.compose(input_value)
        assert result1
        assert value1 == content

        # Change file and try to read composition again
        json_file.append_text("extra text")
        result2, value2 = handler.compose(input_value)
        assert result2
        assert value1 == value2

    def test_compose_with_unexpected_args(self, json_file, file_ref_handler):
        content = {"a": 100}
        json_file.append_as_json(content)
        result, value = file_ref_handler.compose({
            "!file": str(json_file),
            "!args": [1,2,3],
            "size": 100500
        })

        assert result
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
        with pytest.raises(FileNotFoundError, match='Failed to find .* file'):
            file_ref_handler.compose({"!file": "Unknown"})


class TestGeneratorCompositionHandler:
    """Tests for GeneratorCompositionHandler"""
    @staticmethod
    def gen_random_number():
        return random.randint(0, 100)

    @staticmethod
    def gen_random_in_range(min=0, max=100):
        return random.randrange(min, max)

    def test_create(self):
        assert GeneratorCompositionHandler(gen.generators_manager)

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
        ({"!gen": "RandomInRange", "min": 50, "max": 55}, int)
    ])
    def test_compose(self, input_value, expected, generator_handler):
        composition_result, composed_value = generator_handler.compose(input_value)
        assert composition_result
        assert isinstance(composed_value, expected)

    def test_compose_with_same_correlation_id_identical_result(self,
                                generator_handler: GeneratorCompositionHandler):
        cid = "FooBar"
        result, value1 = generator_handler.compose({
            "!gen": "RandomNumber",
            "!id": cid
        })
        assert result

        result, value2 = generator_handler.compose({
            "!gen": "RandomNumber",
            "!id": cid
        })
        assert result
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
    def test_create(self):
        assert MatcherCompositionHandler(matchers.matchers_manager)

    def test_matches(self):
        handler = MatcherCompositionHandler(matchers.matchers_manager)
        assert handler.match({
            "!match": "Anything",
            "!args": [1,2,3],
            "kwarg1": 1
        })

    @pytest.mark.parametrize("input_value, expected", [
        ({"!match": "Anything"}, matchers.Anything()),
        ({"!match": "AnyText"}, matchers.AnyText()),
        ({"!match": "AnyTextLike", "!args": [".*"]}, matchers.AnyTextLike('.*')),
        ({"!match": "AnyNumberGreaterThan", "!args": [10]}, matchers.AnyNumberGreaterThan(10)),
        ({"!match": "AnyNumberGreaterThan", "number": 10}, matchers.AnyNumberGreaterThan(10)),
        ({"!match": "AnyListOf", "!args": [5, "str"]}, matchers.AnyListOf(5, '')),
        ({"!match": "AnyListOf", "size": 5, "item_type": 3},
         matchers.AnyListOf(size=5, item_type=3))
    ])
    def test_compose(self, input_value, expected):
        handler = MatcherCompositionHandler(matchers.matchers_manager)
        composition_result, composed_value = handler.compose(input_value)

        assert composition_result
        assert composed_value == expected

    # --- Negative
    @pytest.mark.parametrize('input_value', [
        {"!matchx": "Anything", "!args": [1,2,3], "kwarg1": 1},
        {"match": "Anything"}
    ])
    def test_match_fails(self, input_value):
        handler = MatcherCompositionHandler(matchers.matchers_manager)
        assert not handler.match(input_value)

    def test_compose_by_unknown_matcher_fails(self):
        handler = MatcherCompositionHandler(matchers.matchers_manager)
        with pytest.raises(ValueError, match='Failed to find matcher with name .*'):
            handler.compose({
                "!match": "UnknownMatcher",
                "!args": [1,2,3]
            })
