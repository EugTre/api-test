"""Unit tests for Reference Resolver class

pytest -s -vv ./utils/json_content/test_reference_resolver.py
"""
import copy
import pathlib
import json
import pytest

from utils.json_content.json_wrapper import JsonWrapper, FastJsonWrapper
from utils.json_content.reference_resolver import ReferenceResolver


@pytest.mark.parametrize("wrapper_cls", [
    JsonWrapper,
    FastJsonWrapper
])
class TestReferenceResolver:
    """Tests ReferenceResolver class"""
    # --- Positive tests
    @pytest.mark.parametrize("cache_enabled", [False, True])
    @pytest.mark.parametrize("raw_content", [
        {},
        [],
        {"a":1, "b":2},
        [1,2,3],
        {"a":1, "b":[1,2,3]},
        [{"id":1}, {"id":2}]
    ])
    def test_no_refs_to_resolve(self, raw_content: list|dict,
                                   cache_enabled: bool, wrapper_cls):
        """No error on resolve_all() for content without references."""
        content = wrapper_cls(copy.deepcopy(raw_content))
        ReferenceResolver(content, cache_enabled).resolve_all()
        # Check that content after resolution is the very same as original
        assert content.get('') == raw_content

    @pytest.mark.parametrize("cache_enabled", [False, True])
    def test_resolve_reference_flat_dict(self, cache_enabled, wrapper_cls):
        """Reference resolution is successful for flat references"""
        content = wrapper_cls({
            "a": 100,
            "b": "!ref /a",
            "c": "!ref /a"
        })
        ReferenceResolver(content, cache_enabled).resolve_all()

        raw_content = content.get('')
        assert raw_content['b'] == raw_content['a']
        assert raw_content['c'] == raw_content['a']

    @pytest.mark.parametrize("cache_enabled", [False, True])
    def test_resolve_reference_nested_dict(self, cache_enabled, wrapper_cls):
        """Reference resolution is successful in nested references in dict"""
        content = wrapper_cls({
            "a": 100,
            "b": {
                "c": 200
            },
            "e-from-bc": "!ref /b/c",
            "e": {
                "e-from-a": "!ref /a",
                "e-from-bc": "!ref /b/c"
            }
        })
        ReferenceResolver(content, cache_enabled).resolve_all()

        raw_content = content.get('')
        assert raw_content['e-from-bc'] == raw_content['b']['c']
        assert raw_content['e']['e-from-a'] == raw_content['a']
        assert raw_content['e']['e-from-bc'] == raw_content['b']['c']

    @pytest.mark.parametrize("cache_enabled", [False, True])
    def test_resolve_reference_value_is_mutable(self, cache_enabled, wrapper_cls):
        """Reference resolution create copy of mutable values."""
        content = wrapper_cls({
            "a": [1,2,3],
            "b": {
                "enabled": True
            },
            "e-from-a": "!ref /a",
            "e-from-b": "!ref /b",
            "e-from-e": "!ref /e-from-b",
            "e-from-a2": "!ref /a"
        })
        ReferenceResolver(content, cache_enabled).resolve_all()

        raw_content = content.get('')
        # Validate that references was resolved
        assert raw_content['e-from-a'] == raw_content['a']
        assert raw_content['e-from-a2'] == raw_content['a']
        assert raw_content['e-from-b'] == raw_content['b']
        assert raw_content['e-from-e'] == raw_content['e-from-b']

        # Validate that values objects are not the same object
        assert raw_content['e-from-a'] is not raw_content['a']
        assert raw_content['e-from-a2'] is not raw_content['a']
        assert raw_content['e-from-a'] is not raw_content['e-from-a2']

        assert raw_content['e-from-b'] is not raw_content['b']
        assert raw_content['e-from-e'] is not raw_content['e-from-b']
        assert raw_content['e-from-e'] is not raw_content['b']

    @pytest.mark.parametrize("cache_enabled", [False, True])
    def test_resolve_reference_in_array(self, cache_enabled, wrapper_cls):
        """References in and to array elements resolves successfully,
        including root content array."""
        content = wrapper_cls([
            {"id": 1, "posts": [1,2,44,55]},
            {"id": 2, "posts": []},
            {"id": 30, "posts": "!ref /0/posts"},
            {"id": 31, "posts": ["!ref /0/posts/0", "!ref /0/posts/1"]},
            {"id": 32, "posts": ["!ref /0/posts/0", "!ref /0/posts/2"]},
            "!ref /1"
        ])
        ReferenceResolver(content, cache_enabled).resolve_all()
        raw_content = content.get('')

        assert raw_content[2]['posts'] == raw_content[0]['posts']
        assert raw_content[2]['posts'] is not raw_content[0]['posts']

        assert raw_content[3]['posts'][0] == raw_content[0]['posts'][0]
        assert raw_content[3]['posts'][1] == raw_content[0]['posts'][1]

        assert raw_content[4]['posts'][0] == raw_content[0]['posts'][0]
        assert raw_content[4]['posts'][1] == raw_content[0]['posts'][2]

        assert raw_content[-1] == raw_content[1]
        assert raw_content[-1] is not raw_content[1]

    @pytest.mark.parametrize("cache_enabled", [False, True])
    def test_resolve_ref_to_none(self, cache_enabled, wrapper_cls):
        """It's possible to resolve reference to None type"""
        content = wrapper_cls({
            "a": None,
            "b": "!ref /a",
            "c": "!ref /a"
        })
        ReferenceResolver(content, cache_enabled).resolve_all()
        raw_content = content.get('')
        assert raw_content['b'] == raw_content['a']
        assert raw_content['c'] == raw_content['a']

    def test_cache_may_be_invalidated(self, wrapper_cls):
        """Cache may be invalidated and new references will be
        correctly resolved"""
        original_value = 10
        new_value = 300

        content = wrapper_cls({
            "a": original_value,
            "b": "!ref /a"
        })
        resolver = ReferenceResolver(content, True)
        resolver.resolve_all()

        # If cache is clean - /c will refer to new value of /a
        resolver.invalidate_cache()
        content.update('/a', new_value)
        content.update('/c', '!ref /a')
        resolver.resolve_all()

        raw_content = content.get('')
        assert raw_content['b'] != raw_content['c']
        assert raw_content['b'] == original_value
        assert raw_content['c'] == new_value

    # --- Negative tests
    @pytest.mark.parametrize("raw_content", [
        {
            # Ref to self
            "a": "!ref /a"
        },
        {
            # Cyclic ref
            "a": "!ref /b",
            "b": "!ref /a"
        },
        {
            # Cyclic ref with several steps
            "a": "!ref /b",
            "b": "!ref /c",
            "c": "!ref /d",
            "d": "!ref /e",
            "e": "!ref /f",
            "f": "!ref /g",
            "g": "!ref /a",
        },
        {
            # Nested cyclic ref
            "a": {
                "nested": "!ref /b"
            },
            "b": "!ref /a/nested"
        }
    ])
    def test_recursive_ref_fails(self, raw_content: dict|list, wrapper_cls):
        """Recursive references couldn't be resolved and exception should be raised"""
        content = wrapper_cls(raw_content)
        with pytest.raises(RecursionError, match='Recursion detected!.*'):
            ReferenceResolver(content).resolve_all()

    @pytest.mark.parametrize("pointer, exc_msg", [
        (r'!ref b/c',  r'Invalid JSON Reference Pointer syntax.*'),
        ('!ref -3', r'Invalid JSON Reference Pointer syntax.*'),
        ('!ref ', r'.*Refering to entire document is not allowed.')
    ])
    def test_recursive_ref_by_invalid_pointer_fails(self, pointer: str,
                                                    exc_msg: str, wrapper_cls):
        """References that use invalid pointer couldn't be resolved and exception
        should be raised"""
        content = wrapper_cls({
            "a": 10,
            "e": pointer
        })

        with pytest.raises(ValueError, match=exc_msg):
            ReferenceResolver(content).resolve_all()

    @pytest.mark.parametrize("pointer", [
        r'!ref /b/d',
        r'!ref /',
        r'!ref /a/y',
        r'!ref /d/5',
        r'!ref /d/zzz/3',
    ])
    def test_recursive_ref_by_incorrect_pointer_fails(self, pointer: str,
                                                      wrapper_cls):
        """References that use of incorrect pointer (target key or node is missing)
        couldn't be resolved and exception should be raised"""
        content = wrapper_cls({
            "a": 10,
            "b": {
                "c": 20
            },
            "d": [40, 50, 60],
            "e": pointer
        })

        with pytest.raises(ValueError, match='Failed to resolve reference.*'):
            ReferenceResolver(content).resolve_all()


@pytest.mark.parametrize("wrapper_cls", [
    JsonWrapper,
    FastJsonWrapper
])
class TestReferenceResolverFileRef:
    """Tests how Reference Resolver resolves file references."""

    # --- Positive tests
    @pytest.mark.parametrize("cache_enabled", [False, True])
    def test_file_no_refs(self, cache_enabled: bool, json_file: pathlib.Path,
                          wrapper_cls):
        """Resolving file reference with ref-less content should be successful"""
        file_content = [1, 2, 3]
        json_file.write_text(json.dumps(file_content))

        content = wrapper_cls({
            "a": f"!file {json_file}",
            "b": f"!file {json_file}"
        })
        ReferenceResolver(content, cache_enabled).resolve_all()

        raw_content = content.get('')
        assert raw_content['a'] == file_content
        assert raw_content['b'] == file_content

    @pytest.mark.parametrize("cache_enabled", [False, True])
    def test_file_with_refs(self, cache_enabled: bool, json_file: pathlib.Path,
                            wrapper_cls):
        """Resolving file reference with content with references should be successful"""
        file_content = {"id": 2, "posts": "!ref /0/posts" }
        json_file.write_text(json.dumps(file_content))

        content = wrapper_cls([
            {"id": 1, "posts": [12, 23, 75]},
            f"!file {json_file}",
            f"!file {json_file}",
        ])
        ReferenceResolver(content, cache_enabled).resolve_all()

        raw_content = content.get('')
        # Validate references parsed
        assert raw_content[1]['id'] == file_content['id']
        assert raw_content[1]['posts'] == raw_content[0]['posts']
        assert raw_content[2]['id'] == file_content['id']
        assert raw_content[2]['posts'] == raw_content[0]['posts']

        # Validate that content read from file is equal, but not the same object
        assert raw_content[1] == raw_content[2]
        assert raw_content[1] is not raw_content[2]

        # Validate that referenced values are copies, not the same object
        assert raw_content[1]['posts'] is not raw_content[0]['posts']
        assert raw_content[2]['posts'] is not raw_content[0]['posts']
        assert raw_content[1]['posts'] is not raw_content[2]['posts']

    def test_file_cache_may_be_invalidated(self, json_file: pathlib.Path, wrapper_cls):
        """Cache may be invalidated and new file references will be
        correctly resolved"""
        original_posts = [12, 23, 75]
        new_posts = [98, 99, 100]
        original_value = 2
        new_value = 10

        # Initializ content and resolve ref for the first time to cache data
        file_content = {"id": original_value, "posts": "!ref /0/posts" }
        json_file.write_text(json.dumps(file_content))
        content = wrapper_cls([
            {"id": 1, "posts": original_posts},
            f"!file {json_file}"
        ])
        resolver = ReferenceResolver(content, True)
        resolver.resolve_all()

        # Update referenced content and file's content
        file_content['id'] = new_value
        json_file.write_text(json.dumps(file_content))
        content.update('/0/posts', new_posts)

        # Add new file reference to content, drop cache and resolve again
        content.update('/-', f"!file {json_file}")
        resolver.invalidate_cache()
        resolver.resolve_all()

        raw_content = content.get('')

        # Validate first time parsed references
        assert raw_content[1]['id'] == original_value
        assert raw_content[1]['posts'] == original_posts

        # Validate later parsed refs
        assert raw_content[2]['id'] == file_content['id']
        assert raw_content[2]['posts'] == raw_content[0]['posts']

    @pytest.mark.parametrize("file_content", [
        {"posts": "!ref 0/posts" },
        {"posts": "!ref "},
        {"posts": "!ref /-5"},
        {"posts": "!ref /0/enabled"},
    ])
    def test_file_invalid_pointer_in_file_ref_fails(self,
            json_file: pathlib.Path, file_content: dict, wrapper_cls):
        """Exception raised on parsing in-file reference if ref pointer is invalid"""
        json_file.write_text(json.dumps(file_content))

        content = wrapper_cls([
            {"id": 1, "posts": [12, 23, 75]},
            f"!file {json_file}"
        ])

        with pytest.raises(ValueError):
            ReferenceResolver(content).resolve_all()

    def test_file_ref_file_not_found_fails(self, wrapper_cls):
        """Exception raised on parsing file reference to non existing file."""
        content = wrapper_cls([
            {"id": 1, "posts": "!file non_existing_file.json"}
        ])

        with pytest.raises(ValueError):
            ReferenceResolver(content).resolve_all()

    def test_file_json_malformed_fails(self, json_file: pathlib.Path, wrapper_cls):
        """Exception raised on parsing file reference to file with malformed
        JSON content."""
        json_file.write_text("{a: 100, b: 200}")
        content = wrapper_cls([
            {"id": 1, "posts": f"!file {json_file}"}
        ])

        with pytest.raises(ValueError):
            ReferenceResolver(content).resolve_all()
