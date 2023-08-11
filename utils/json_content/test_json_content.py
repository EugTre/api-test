"""Unit tests for JsonContent

pytest -s -vv ./utils/json_content/test_json_content.py
"""
import copy
import json
from typing import Any

import pytest
from utils.json_content.json_content import JsonContentBuilder,\
    AbstractContentWrapper, AbstractReferenceResolver


CONTENT = {
    'a': 1,
    'b': {
        'c': 3,
        'd': [1,2,3]
    }
}

CONTENT_WITH_REFS = {
    'defs': {
        'int': 100,
        'values': [1, 2, 1337]
    },
    'a': "!ref /defs/int",
    'b': {
        'c': '!ref /defs/int',
        'd': '!ref /defs/values',
    },
    'e': '!ref /defs/values/-1'
}

class MockWrapper(AbstractContentWrapper):
    """Mocked ContentWrapper"""
    def __init__(self, content: dict):
        self.__content = content

    def has(self, pointer: str) -> bool:
        return True

    def get(self, pointer):
        """Returns value at given pointer from the content
        or return entire content."""
        return self.__content

    def get_or_default(self, pointer: str, default_value: Any) -> Any:
        return self.__content

    def update(self, pointer, value) -> bool:
        """Updates value at given pointer in the content."""
        return True

    def delete(self, pointer) -> bool:
        """Removes value at given pointer from the content
        or clears entire content."""
        return True

    def __eq__(self, other) -> bool:
        return True

    def __contains__(self, pointer) -> bool:
        return True

class MockResolver(AbstractReferenceResolver):
    """Mocked ReferenceResolver"""
    def __init__(self, content_context: AbstractContentWrapper,
                       enable_cache: bool):
        self.content = content_context

    def resolve_all(self):
        """Scans entire content and resolves all references"""
        return

    def resolve(self, value, node_context):
        """Resolves reference of given value and return new value to assign"""
        return value


    def invalidate_cache(self):
        """Clears referece/file cache."""
        return


class TestJsonContent:
    """Tests for JsonContent object based on JSON object"""

    # --- Init
    def test_json_content_build_from_data_copy(self):
        """Build with data copy is successful"""
        cnt = JsonContentBuilder().from_data(CONTENT, make_copy=True).build()
        raw_content = cnt.get('')

        assert raw_content == CONTENT
        assert raw_content is not CONTENT
        assert raw_content['b'] is not CONTENT['b']
        assert raw_content['b']['d'] is not CONTENT['b']['d']

    def test_json_content_build_from_data_nocopy(self):
        """Build without data copy is successful"""
        content = copy.deepcopy(CONTENT)
        cnt = JsonContentBuilder().from_data(content).build()
        raw_content = cnt.get('')

        assert raw_content == content
        assert raw_content is content
        assert raw_content['b'] is content['b']
        assert raw_content['b']['d'] is content['b']['d']

    @pytest.mark.parametrize("content, expected_type", [
        ({}, dict),
        ([], list),
        (None, dict)
    ])
    def test_json_content_build_from_empty(self, content, expected_type):
        """Build JsonContent object from empty list or dict is successful"""
        cnt = JsonContentBuilder().from_data(content).build()
        assert not cnt.get('')
        assert isinstance(cnt.get(''), expected_type)

    def test_json_content_build_from_file(self, json_file):
        """JsonContent object may be build from JSON file content."""
        json_file.write_text(json.dumps(CONTENT))

        cnt = JsonContentBuilder().from_file(str(json_file)).build()
        assert cnt.get('') == CONTENT

    def test_json_content_no_ref_resolultion_on_creation(self):
        """Referecnces not resolved on creation of JsonContent when
        reference resolution is disabled"""
        cnt = JsonContentBuilder().from_data(CONTENT_WITH_REFS, True)\
            .set_reference_policy(False, False).build()

        raw_content = cnt.get('')
        assert raw_content == CONTENT_WITH_REFS

    def test_json_content_ref_resolultion_on_creation(self):
        """Referecnces resolved on creation of JsonContent when
        reference resolution is enabled"""
        cnt = JsonContentBuilder().from_data(CONTENT_WITH_REFS, True)\
            .set_reference_policy(True, True).build()

        raw_content = cnt.get('')
        assert raw_content['a'] == CONTENT_WITH_REFS['defs']['int']
        assert raw_content['b']['c'] == CONTENT_WITH_REFS['defs']['int']
        assert raw_content['b']['d'] == CONTENT_WITH_REFS['defs']['values']
        assert raw_content['e'] == CONTENT_WITH_REFS['defs']['values'][-1]

        assert raw_content['b']['d'] is not CONTENT_WITH_REFS['defs']['values']

    def test_json_content_build_fully_specified(self):
        """Build with fully specified params"""
        cnt = JsonContentBuilder().from_data(CONTENT_WITH_REFS, True)\
            .set_wrapper(MockWrapper) \
            .set_resolver(MockResolver) \
            .set_reference_policy(True, True).build()

        assert cnt.content is not None
        assert isinstance(cnt.content, MockWrapper)
        assert cnt.resolver is not None
        assert isinstance(cnt.resolver, MockResolver)

    def test_json_content_get_return_copy(self):
        """Get returns a copy of mutable if flag is set to True"""
        cnt = JsonContentBuilder().from_data(CONTENT).build()

        assert cnt.get('/b') is CONTENT['b']
        assert cnt.get('/b', True) is not  CONTENT['b']
        assert cnt.get('/b/d') is CONTENT['b']['d']
        assert cnt.get('/b/d', True) is not CONTENT['b']['d']

    def test_json_content_update_without_ref_resolution(self):
        """Update with ref-value when reference resolution is disabled
        will resolve reference and updates successful"""
        cnt = JsonContentBuilder().from_data(CONTENT, True).build()

        cnt.update('/e', '!ref /b/c').update('/a', '!ref /b/d/-1')

        raw_content = cnt.get('')
        assert raw_content['e'] == '!ref /b/c'
        assert raw_content['a'] == '!ref /b/d/-1'

    def test_json_content_update_with_ref_resolution(self):
        """Update with ref-value when reference resolution is eabled
        will resolve reference and updates successful"""
        content = copy.deepcopy(CONTENT)
        cnt = JsonContentBuilder().from_data(CONTENT, True)\
                                .set_reference_policy(True, False)\
                                .build()

        cnt.update('/e', '!ref /b/c').update('/a', '!ref /b/d/-1')
        content['e'] = content['b']['c']
        content['a'] = content['b']['d'][-1]

        assert cnt.get('') == content

    def test_json_content_update_ref_resolultion_cache_usage(self):
        """Update resolves refs using cache when reference resolution and
        cache are enabled"""
        cnt = JsonContentBuilder().from_data(CONTENT_WITH_REFS, True)\
            .set_reference_policy(True, True).build()

        # Change referenced value, but do not invalidate cache - old value
        # should be used
        cnt.update('/defs/int', 50)
        cnt.update('/f', '!ref /defs/int')

        raw_content = cnt.get('')
        assert raw_content['defs']['int'] == 50
        # Both old and new keys are using same old value (new key is using cached value)
        assert raw_content['a'] == CONTENT_WITH_REFS['defs']['int']
        assert raw_content['f'] == CONTENT_WITH_REFS['defs']['int']

    def test_json_content_update_ref_resolultion_cache_invalidated(self):
        """Update resolves refs using empty cache when reference resolution and
        cache are enabled, and cache was invalidated"""
        cnt = JsonContentBuilder().from_data(CONTENT_WITH_REFS, True)\
            .set_reference_policy(True, True).build()

        # Update value, drop cache and add new ref to content
        cnt.update('/defs/int', 50)
        cnt.invalidate_cache()
        cnt.update('/f', '!ref /defs/int')

        raw_content = cnt.get('')
        assert raw_content['defs']['int'] == 50
        assert raw_content['f'] == raw_content['defs']['int']

    def test_json_content_update_ref_resolultion_cache_disabled(self):
        """Update resolves refs without using of cache when reference
        resolution is enabled, but cache is not cache are enabled"""
        cnt = JsonContentBuilder().from_data(CONTENT_WITH_REFS, True)\
            .set_reference_policy(True, False).build()

        # Change referenced value and add a new reference to it
        cnt.update('/defs/int', 50)
        cnt.update('/f', '!ref /defs/int')

        raw_content = cnt.get('')
        assert raw_content['defs']['int'] == 50
        assert raw_content['f'] == raw_content['defs']['int']

    def test_json_content_delete(self):
        """Delete single valid key is successful"""
        cnt = JsonContentBuilder().from_data(CONTENT, True).build()
        cnt.delete('/a')

        raw_content = cnt.get('')
        assert raw_content != CONTENT
        assert raw_content.get('a') is None

    def test_json_content_bulk_delete(self):
        """Delete several keys including is successful"""
        cnt = JsonContentBuilder().from_data(CONTENT, True).build()
        cnt.delete('/b/d/-1', '/a')

        raw_content = cnt.get('')
        assert raw_content != CONTENT
        assert raw_content.get('a') is None
        assert len(raw_content['b']['d']) == (len(CONTENT['b']['d']) - 1)

    def test_json_content_bulk_delete_with_missing_key(self):
        """Delete several keys including missing is successful"""
        cnt = JsonContentBuilder().from_data(CONTENT, True).build()
        cnt.delete('/b/d/-1', '/b/x', '/x', '/a')

        raw_content = cnt.get('')
        assert raw_content != CONTENT
        assert raw_content.get('a') is None
        assert len(raw_content['b']['d']) == (len(CONTENT['b']['d']) - 1)

    def test_json_content_has_key(self):
        """Has method returns True on existend node or false on non-existent"""
        cnt = JsonContentBuilder().from_data(CONTENT).build()

        assert cnt.has('/a')
        assert not cnt.has('/xxx')

    @pytest.mark.parametrize("pointer, default_value, expected_value", [
        ('/a', 333, CONTENT['a']),
        ('/xxx', 333, 333),
    ])
    def test_json_content_get_or_default(self, pointer, default_value, expected_value):
        """Get or default returns property's data or default"""
        cnt = JsonContentBuilder().from_data(CONTENT).build()

        assert cnt.get_or_default(pointer, default_value) == expected_value

    def test_json_content_get_or_default_makes_copy(self):
        """Get or default can retur copy of property's data"""
        cnt = JsonContentBuilder().from_data(CONTENT).build()

        default_value = [99, 100]
        value = cnt.get_or_default('/b/d', default_value, make_copy=True)
        assert value == CONTENT['b']['d']
        assert value is not CONTENT['b']['d']

        non_existent_prop_value = cnt.get_or_default('/b/x', [99, 100], make_copy=True)
        assert non_existent_prop_value == default_value
        assert non_existent_prop_value is not default_value

    def test_json_content_equals(self):
        """JsonContent with same contents equals"""
        cnt1 = JsonContentBuilder().from_data(CONTENT, True).build()
        cnt2 = JsonContentBuilder().from_data(CONTENT, True).build()

        cnt1.update('/b/c', 333)
        cnt2.update('/b/c', 333)

        assert cnt1 is not cnt2
        assert cnt1 == cnt2

    def test_json_content_not_equals(self):
        """JsonContent with different contents not equals"""
        cnt1 = JsonContentBuilder().from_data(CONTENT, True).build()
        cnt2 = JsonContentBuilder().from_data(CONTENT, True).build()

        # Only one content is updated
        cnt1.update('/b/c', 333)

        assert cnt1 is not cnt2
        assert cnt1 != cnt2

    @pytest.mark.parametrize("pointer", [
        '/a',
        '/b/c',
        '/b/d/0',
        '/b/d/-1'
    ])
    def test_json_content_check_key_exists_by_in(self, pointer):
        """Check for pointer presenets by in operator"""
        cnt = JsonContentBuilder().from_data(CONTENT).build()
        assert pointer in cnt

    @pytest.mark.parametrize("pointer", [
        '/x',
        '/a/x',
        '/b/x',
        '/b/d/-5',
        '/b/d/5'
    ])
    def test_json_content_check_key_not_exists_by_in(self, pointer):
        """Check for pointer not presenets by in operator"""
        cnt = JsonContentBuilder().from_data(CONTENT).build()
        assert pointer not in cnt

    # --- Negative
    @pytest.mark.parametrize("content", [
        "string",
        1234,
        ('foo', 'bar'),
        False
    ])
    def test_json_content_build_from_not_supported_content_fails(self, content):
        """Build JsonContent object from non list/dict should fail"""
        with pytest.raises(ValueError, match='Content must be JSON-like of type dict or list!.*'):
            JsonContentBuilder().from_data(content).build()

    def test_json_content_build_from_non_exists_file_fails(self):
        """Build JsonContent object from non existisng file should fail"""
        with pytest.raises(FileNotFoundError):
            JsonContentBuilder().from_file("non-exists.json").build()

    def test_json_content_build_from_malformed_json_file_fails(self, json_file):
        """Build JsonContent object from malformed JSON should fail"""
        json_file.write_text("{a: 100, b: 200}")

        with pytest.raises(json.decoder.JSONDecodeError):
            JsonContentBuilder().from_file(str(json_file)).build()
