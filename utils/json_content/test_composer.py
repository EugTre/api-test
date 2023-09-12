"""Unit tests for Composer class

pytest -s -vv ./utils/json_content/test_composer.py
"""

import copy
import re

import pytest
from utils.generators import GeneratorsManager
from utils.matchers import MatchersManager, AnyText, AnyListOf

from .composer import Composer
from .json_wrapper import JsonWrapper
from .composition_handlers import ReferenceCompositionHandler, \
    FileReferenceCompositionHandler, \
    IncludeFileCompositionHandler, \
    GeneratorCompositionHandler, \
    MatcherCompositionHandler


@pytest.fixture(name='handlers', scope='session')
def get_handlers():
    """Returns handlers config for tests"""
    matcher_manager = MatchersManager()
    matcher_manager.add(AnyText)
    matcher_manager.add(AnyListOf)

    generator_manager = GeneratorsManager()
    generator_manager.add(gen_number, "Number")

    return {
        MatcherCompositionHandler: {"manager": matcher_manager},
        GeneratorCompositionHandler: {"manager": generator_manager},
        FileReferenceCompositionHandler: {"use_cache": True},
        ReferenceCompositionHandler: {"content_context": None},
    }

def gen_number():
    """Generates a number"""
    return 42


class TestComposerCreation:
    """Instance creation related tests"""
    def test_composer_create_with_defaults(self):
        """Composer creates with defaults without errors"""
        assert Composer(JsonWrapper({"a": 100}))

    def test_composer_create_with_custom_handlers(self, handlers):
        """Composer creates with custom set of handlers"""
        assert Composer(JsonWrapper({"a": 100}), handlers=handlers)

    def test_composer_create_with_incorrect_params(self, handlers):
        """Error handling on creation of composer with incorrect
        handlers parameters"""

        invalid_handlers_config = copy.deepcopy(handlers)
        invalid_handlers_config[MatcherCompositionHandler]['some_args'] = [1,2,3]
        invalid_handlers_config[GeneratorCompositionHandler]['some_args'] = "FooBar"
        invalid_handlers_config[FileReferenceCompositionHandler]['some_args'] = 123
        invalid_handlers_config[ReferenceCompositionHandler]['some_args'] = False
        with pytest.raises(Exception) as err:
            Composer(JsonWrapper({"a": 100}), handlers=invalid_handlers_config)

        assert re.search('.*Error occured on Json Content Composer.*', err.exconly())


class TestComposer:
    """Tests related to actual composition handling"""
    def test_compose_no_composition(self):
        """Content without composition don't cause errors"""
        content = {
            "a": 100,
            "b": 200
        }
        content_wrapper = JsonWrapper(copy.deepcopy(content))
        composer = Composer(content_wrapper)
        composer.compose_content()

        assert content_wrapper.get('') == content

    def test_compose_with_ref(self):
        """Compose reference composition"""
        content = {
            "a": 100,
            "b": {"!ref": "/a"}
        }
        content_wrapper = JsonWrapper(copy.deepcopy(content))
        composer = Composer(content_wrapper, handlers={
            ReferenceCompositionHandler: {"content_context": None}
        })
        composer.compose_content()

        expected_content = content
        expected_content['b'] = expected_content['a']

        assert content_wrapper.get('') == expected_content
        assert content_wrapper.get('/b') == content_wrapper.get('/a')
        assert content_wrapper.get('/b') == expected_content['b']

    def test_compose_with_file_ref(self, json_file):
        """Compose file reference composition"""
        file_content = {"x": 100}
        json_file.write_as_json(file_content)
        content = {
            "a": {"!file": str(json_file)}
        }
        content_wrapper = JsonWrapper(content)
        composer = Composer(content_wrapper, handlers={
            FileReferenceCompositionHandler: {"use_cache": False}
        })
        composer.compose_content()

        assert content_wrapper.get('') == {"a": file_content}
        assert content_wrapper.get('/a') == file_content
        assert content_wrapper.get('/a/x') == file_content['x']

    def test_compose_with_include_file(self, json_file):
        """Compose include file composition"""
        file_content = {
            "x": 100,
            "y": {"!ref": "/x"}
        }
        expected_content = {
            "x": file_content['x'],
            "y": file_content['x']
        }
        json_file.write_as_json(file_content)
        content = {
            "a": {
                "!include": str(json_file),
                "!compose": True
            }
        }
        content_wrapper = JsonWrapper(content)
        composer = Composer(content_wrapper, handlers={
            IncludeFileCompositionHandler: {"use_cache": False}
        })
        composer.compose_content()

        assert content_wrapper.get('') == {"a": expected_content}
        assert content_wrapper.get('/a') == expected_content
        assert content_wrapper.get('/a/x') == expected_content['x']
        assert content_wrapper.get('/a/y') == expected_content['y']

    def test_compose_with_generator(self):
        """Compose generation composition"""
        content = {
            "a": 100,
            "b": {"!gen": "Number"}
        }
        content_wrapper = JsonWrapper(copy.deepcopy(content))

        gen_manager = GeneratorsManager()
        gen_manager.add(gen_number, name="Number")

        composer = Composer(content_wrapper, handlers={
            GeneratorCompositionHandler: {"manager": gen_manager}
        })

        composer.compose_content()

        expected_content = content
        expected_content['b'] = gen_number()

        assert content_wrapper.get('/b') == 42
        assert content_wrapper == expected_content

    def test_compose_with_matcher(self):
        """Compose matcher composition"""
        content = {
            "a": {"!match": "AnyText"}
        }
        content_wrapper = JsonWrapper(copy.deepcopy(content))

        matcher_manager = MatchersManager()
        matcher_manager.add(AnyText)

        composer = Composer(content_wrapper, handlers={
            MatcherCompositionHandler: {"manager": matcher_manager}
        })
        composer.compose_content()

        expected_content = copy.deepcopy(content)
        expected_content['a'] = AnyText()

        assert isinstance(content_wrapper.get('/a'), AnyText)
        assert content_wrapper == expected_content

    def test_compose_mixed_simple(self, json_file):
        """Several types of compositions in single document"""
        file_content = {"x": 300}
        json_file.write_as_json(file_content)

        content = {
            "a": 100,
            "b": {"!ref": "/a"},
            "c": {"!file": str(json_file)},
            "d": {"!gen": "Number"},
            "e": {"!match": "AnyText"}
        }
        expected_content = {
            "a": 100,
            "b": 100,
            "c": file_content,
            "d": gen_number(),
            "e": AnyText()
        }

        wrapper = JsonWrapper(content)

        matcher_manager = MatchersManager()
        matcher_manager.add(AnyText)

        generator_manager = GeneratorsManager()
        generator_manager.add(gen_number, "Number")

        composer = Composer(wrapper, handlers={
            MatcherCompositionHandler: {"manager": matcher_manager},
            GeneratorCompositionHandler: {"manager": generator_manager},
            FileReferenceCompositionHandler: {},
            ReferenceCompositionHandler: {"content_context": None},
        })
        composer.compose_content()

        assert wrapper.get('') == expected_content

    def test_compose_mixed_complex(self, handlers, json_file):
        """Complex mixing of compositions and references. Should be resolved
        in several passes."""
        file_content = [
            {"!gen": "Number"},
            {"!ref": "/a"}
        ]
        json_file.write_as_json(file_content)

        content = {
            "a": {"!match": "AnyListOf", "item_type": 1, "size": 4},
            "b": {"!file": str(json_file)},
            "c": {
                "n1": {"!ref": "/a"},
                "n2": {"!file": str(json_file)}
            }
        }
        expected_any = AnyListOf(4, item_type=1)
        expected_content = {
            "a": expected_any,
            "b": [gen_number(), expected_any],
            "c": {
                "n1": expected_any,
                "n2": [gen_number(), expected_any]
            }
        }

        wrapper = JsonWrapper(content)
        composer = Composer(content_context=wrapper, handlers=handlers)

        composer.compose_content()

        assert wrapper.get('') == expected_content

    def test_compose_mixed_ref_to_implied_node(self, handlers, json_file):
        """References are in such order, that it won't be resolved in one pass.
        Test will expect Composer to revisit nodes few times to complete composition process"""
        file_content = [
            1,
            {"!gen": "Number"}
        ]
        json_file.write_as_json(file_content)

        content = {
            "a": {"!ref": "/b/1"},
            "b": {"!ref": '/c/n1'},
            "c": {
                "n1": {"!file": str(json_file)}
            }
        }
        expected_content = {
            "a": gen_number(),
            "b": [1, gen_number()],
            "c": {
                "n1": [1, gen_number()]
            }
        }

        wrapper = JsonWrapper(content)
        composer = Composer(content_context=wrapper, handlers=handlers)

        composer.compose_content()

        assert wrapper.get('') == expected_content

    def test_compose_with_nested_compositions(self, handlers):
        """When value of composition is also composition composer
        should resolve from bottom to top."""

        content = {
            "a": 100,
            "b": "/a",
            # Ref to value referenced by /b:
            # ref /b => /a
            # ref /a => 100
            "c": {"!ref": {"!ref": "/b"}}
        }
        expected_content = {
            "a": 100,
            "b": "/a",
            "c": 100
        }
        wrapper = JsonWrapper(content)
        composer = Composer(content_context=wrapper, handlers=handlers)
        composer.compose_content()

        assert wrapper.get('') == expected_content





    # --- Ref Resolution tests
    @pytest.mark.parametrize("content, expected_content", [
        ({
            "a": 100,
            "b": {
                "c": 200
            },
            "e-from-bc": {"!ref": "/b/c"},
            "e": {
                "e-from-a": {"!ref": "/a"},
                "e-from-bc": {"!ref": "/b/c"}
            }
        }, {
            "a": 100,
            "b": {
                "c": 200
            },
            "e-from-bc": 200,
            "e": {
                "e-from-a": 100,
                "e-from-bc": 200
            }
        }),
        ({
            "a": [1,2,3],
            "b": {"enabled": True},
            "e-from-a": {"!ref": "/a"},
            "e-from-b": {"!ref": "/b"},
            "e-from-e": {"!ref": "/e-from-b"},
            "e-from-a2": {"!ref": "/a"}
        }, {
            "a": [1,2,3],
            "b": {"enabled": True},
            "e-from-a": [1,2,3],
            "e-from-b": {"enabled": True},
            "e-from-e": {"enabled": True},
            "e-from-a2": [1,2,3]
        }),
        ([
            {"id": 1, "posts": [1,2,44,55]},
            {"id": 2, "posts": []},
            {"id": 30, "posts": {"!ref":"/0/posts"}},
            {"id": 31, "posts": [{"!ref":"/0/posts/0"}, {"!ref":"/0/posts/1"}]},
            {"id": 32, "posts": [{"!ref":"/0/posts/0"}, {"!ref":"/0/posts/2"}]},
            {"!ref":"/1"}
        ], [
            {"id": 1, "posts": [1,2,44,55]},
            {"id": 2, "posts": []},
            {"id": 30, "posts": [1,2,44,55]},
            {"id": 31, "posts": [1, 2]},
            {"id": 32, "posts": [1, 44]},
             {"id": 2, "posts": []},
        ]),
        ({
            "a": None,
            "b": {"!ref":"/a"}
        }, {
            "a": None,
            "b": None
        })
    ])
    def test_compose_references(self, handlers, content, expected_content):
        """Complex reference composition"""
        wrapper = JsonWrapper(content)
        composer = Composer(content_context=wrapper, handlers=handlers)

        composer.compose_content()

        assert wrapper.get('') == expected_content

    # --- Negative
    @pytest.mark.parametrize("content", [
        # Missing node
        {
            "a": {"!ref": "/b"}
        },
        # Cyclic ref
        {
            "a": {"!ref": "/b"},
            "b": {"!ref": "/c"},
            "c": {"!ref": "/a"}
        },
        # Ref to self
        {
            "a": {"!ref": "/a"}
        },
    ])
    def test_compose_mixed_ref_recursion(self, content, handlers):
        """Recursion referencing should raise an exception"""
        wrapper = JsonWrapper(content)
        composer = Composer(content_context=wrapper, handlers=handlers)

        with pytest.raises(RuntimeError,
                           match='Unresolved errors occured during content composition.*'):
            composer.compose_content()

    @pytest.mark.parametrize("content, expected_error, expected_msg", [
        # Missing file
        ({"a": {"!file": "b.json"}}, FileNotFoundError, 'DataReader failed to find.*file'),
        # Unknown generator
        ({"a": {"!gen": "FooBar"}}, ValueError, 'Failed to find generator.*'),
        # Unknown matcher
        ({ "a": {"!match": "FooBar"}}, ValueError, 'Failed to find matcher.*'),
        # Generator with invalid params
        ({
            "a": {"!gen": "Number", "!args": [1,2,3], "Foo": "Bar"}
        }, TypeError, '.*'),
        ([{"!ref": ""}], ValueError, 'Referencing to document root is not allowed!.*')
    ])
    def test_compose_invalid_data(self, content, expected_error, expected_msg, handlers):
        """Recursion referencing should raise an exception"""
        wrapper = JsonWrapper(content)
        composer = Composer(content_context=wrapper, handlers=handlers)
        with pytest.raises(expected_error, match=expected_msg) as err:
            composer.compose_content()

        assert re.search('.*Error occured on composing value at.*', err.exconly())


class TestComposerForSpecificNode:
    """Tests related to scan & compose data at specific node"""
    def test_composer_compose_specific_node(self, handlers):
        """Composition added with .update() may be composed correctly"""
        content = {
            "a": 100,
            "b": 200
        }
        wrapper = JsonWrapper(content)
        composer = Composer(wrapper, handlers)

        wrapper.update("/b", {
            "n1": {"!ref": "/a"},
            "n2": {"!gen": "Number"}
        })
        composer.compose_content("/b")

        assert wrapper.get('') == {
            "a": 100,
            "b": {
                "n1": content['a'],
                "n2": gen_number()
            }
        }

    def test_composer_compose_specific_nested_node(self, handlers):
        """Update with complex compositions succeeds"""
        content = {
            "a": 100,
            "b": None
        }
        wrapper = JsonWrapper(content)
        composer = Composer(wrapper, handlers)

        wrapper.update("/b", {
            "n1": {"!ref": "/b/n2"},
            "n2": {"!ref": "/a"},
            "n3": {"!gen": "Number"}
        })
        composer.compose_content("/b")

        assert wrapper.get('') == {
            "a": 100,
            "b": {
                "n1": content['a'],
                "n2": content['a'],
                "n3": gen_number()
            }
        }
