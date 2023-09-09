"""Unit tests for JsonContent

pytest -s -vv ./utils/json_content/test_json_content.py
"""
import copy
import json

import pytest
from utils.json_content.json_content import JsonContentBuilder
from utils.json_content.composition_handlers import DEFAULT_COMPOSITION_HANDLERS_COLLECTION
from utils.json_content.pointer import Pointer

CONTENT = {
    'a': 1,
    'b': {
        'c': 3,
        'd': [1,2,3]
    }
}

CONTENT_WITH_REFS = {
    '$defs': {
        'int': 100,
        'values': [1, 2, 1337]
    },
    'a': {"!ref": "/$defs/int"},
    'b': {
        'c': {"!ref": "/$defs/int"},
        'd': {"!ref": "/$defs/values"},
    },
    'e': {"!ref": "/$defs/values/1"}
}

class TestJsonContent:
    """Tests for JsonContent object based on JSON object"""

    # --- Init
    def test_build_from_data_copy(self):
        """Build with data copy is successful"""
        cnt = JsonContentBuilder().from_data(CONTENT, make_copy=True).build()
        raw_content = cnt.get('')

        assert raw_content == CONTENT
        assert raw_content is not CONTENT
        assert raw_content['b'] is not CONTENT['b']
        assert raw_content['b']['d'] is not CONTENT['b']['d']

    def test_build_from_data_nocopy(self):
        """Build without data copy is successful"""
        content = copy.deepcopy(CONTENT)
        cnt = JsonContentBuilder().from_data(content, make_copy=False).build()
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
    def test_build_from_empty(self, content, expected_type):
        """Build JsonContent object from empty list or dict is successful"""
        cnt = JsonContentBuilder().from_data(content, make_copy=True).build()
        assert not cnt.get('')
        assert isinstance(cnt.get(''), expected_type)

    def test_build_from_file(self, json_file):
        """JsonContent object may be build from JSON file content."""
        json_file.write_text(json.dumps(CONTENT))

        cnt = JsonContentBuilder().from_file(str(json_file)).build()
        assert cnt.get('') == CONTENT

    def test_no_ref_resolultion_on_creation(self):
        """Referecnces not resolved on creation of JsonContent when
        reference resolution is disabled"""
        cnt = JsonContentBuilder().from_data(CONTENT_WITH_REFS, True)\
            .use_composer(False, None).build()

        raw_content = cnt.get('')
        assert raw_content == CONTENT_WITH_REFS

    def test_ref_resolultion_on_creation(self):
        """Referecnces resolved on creation of JsonContent when
        reference resolution is enabled"""
        cnt = JsonContentBuilder().from_data(CONTENT_WITH_REFS, True)\
            .use_composer(True).build()

        raw_content = cnt.get('')
        assert raw_content['a'] == CONTENT_WITH_REFS['$defs']['int']
        assert raw_content['b']['c'] == CONTENT_WITH_REFS['$defs']['int']
        assert raw_content['b']['d'] == CONTENT_WITH_REFS['$defs']['values']
        assert raw_content['e'] == CONTENT_WITH_REFS['$defs']['values'][1]

        assert raw_content['b']['d'] is not CONTENT_WITH_REFS['$defs']['values']
        assert '$defs' not in raw_content

    def test_build_fully_specified(self):
        """Build with fully specified params"""
        cnt = JsonContentBuilder().from_data(CONTENT_WITH_REFS, True)\
            .use_composer(use=True, handlers=DEFAULT_COMPOSITION_HANDLERS_COLLECTION)\
            .build()

        assert cnt.content is not None
        assert cnt.composer is not None

    def test_get_return_copy(self):
        """Get returns a copy of mutable if flag is set to True"""
        cnt = JsonContentBuilder().from_data(CONTENT).build()

        assert cnt.get('/b') is CONTENT['b']
        assert cnt.get('/b/d') is CONTENT['b']['d']

        assert cnt.get('/b', True) is not  CONTENT['b']
        assert cnt.get('/b/d', True) is not CONTENT['b']['d']

    def test_update_without_ref_resolution(self):
        """Update with ref-value when reference resolution is disabled
        will resolve reference and updates successful"""
        cnt = JsonContentBuilder().from_data(CONTENT, True).build()

        cnt.update('/e', {"!ref": "/b/c"}) \
            .update('/a', {"!ref": "/b/d/2"})

        raw_content = cnt.get('')
        assert raw_content['e'] == {"!ref": "/b/c"}
        assert raw_content['a'] == {"!ref": "/b/d/2"}

    def test_update_with_ref_resolution(self):
        """Update with ref-value when reference resolution is enabled
        in composer - will updates successful and resolve reference"""
        content = copy.deepcopy(CONTENT)
        cnt = JsonContentBuilder().from_data(CONTENT, True)\
                                .use_composer(True)\
                                .build()
        cnt.update('/e', {"!ref": "/b/c"}) \
            .update('/a', {"!ref": "/b/d/2"})

        content['e'] = content['b']['c']
        content['a'] = content['b']['d'][2]

        assert cnt.get('') == content

    def test_delete(self):
        """Delete single valid key is successful"""
        cnt = JsonContentBuilder().from_data(CONTENT, True).build()
        cnt.delete('/a')

        raw_content: dict = cnt.get('')
        assert raw_content != CONTENT
        assert raw_content.get('a') is None

    def test_bulk_delete(self):
        """Delete several existing keys is successful"""
        cnt = JsonContentBuilder().from_data(CONTENT, True).build()
        cnt.delete('/b/d/1', '/a')

        raw_content = cnt.get('')
        assert raw_content != CONTENT
        assert raw_content.get('a') is None
        assert len(raw_content['b']['d']) == (len(CONTENT['b']['d']) - 1)

    def test_bulk_delete_with_missing_key(self):
        """Delete several keys including missing is successful"""
        cnt = JsonContentBuilder().from_data(CONTENT, True).build()
        cnt.delete('/b/d/1', '/b/x', '/x', '/a')

        raw_content: dict = cnt.get('')
        assert raw_content != CONTENT
        assert raw_content.get('a') is None
        assert len(raw_content['b']['d']) == (len(CONTENT['b']['d']) - 1)

    def test_has_key(self):
        """Has method returns True on existend node or false on non-existent"""
        cnt = JsonContentBuilder().from_data(CONTENT).build()

        assert '/a' in cnt
        assert Pointer.from_string('/a') in cnt
        assert '/xxx' not in cnt
        assert Pointer.from_string('/xxx') not in cnt

    @pytest.mark.parametrize("pointer, default_value, expected_value", [
        ('/a', 333, CONTENT['a']),
        ('/xxx', 333, 333),
    ])
    def test_get_or_default(self, pointer, default_value, expected_value):
        """Get or default returns property's data or default"""
        cnt = JsonContentBuilder().from_data(CONTENT).build()
        pointer_instance = Pointer.from_string(pointer)

        assert cnt.get_or_default(pointer, default_value) == expected_value
        assert cnt.get_or_default(pointer_instance, default_value) == expected_value

    def test_get_or_default_makes_copy(self):
        """Get or default can retur copy of property's data"""
        cnt = JsonContentBuilder().from_data(CONTENT).build()

        default_value = [99, 100]
        value = cnt.get_or_default('/b/d', default_value, make_copy=True)
        assert value == CONTENT['b']['d']
        assert value is not CONTENT['b']['d']

        non_existent_prop_value = cnt.get_or_default('/b/x', [99, 100], make_copy=True)
        assert non_existent_prop_value == default_value
        assert non_existent_prop_value is not default_value

    def test_equals(self):
        """JsonContent with same contents equals"""
        cnt1 = JsonContentBuilder().from_data(CONTENT, True).build()
        cnt2 = JsonContentBuilder().from_data(CONTENT, True).build()

        cnt1.update('/b/c', 333)
        cnt2.update('/b/c', 333)

        assert cnt1 is not cnt2
        assert cnt1 == cnt2

    def test_not_equals(self):
        """JsonContent with different contents not equals"""
        cnt1 = JsonContentBuilder().from_data(CONTENT, True).build()
        cnt2 = JsonContentBuilder().from_data(CONTENT, True).build()

        # Only one content is updated
        cnt1.update('/b/c', 333)

        assert cnt1 is not cnt2
        assert cnt1 != cnt2

    # --- Negative
    @pytest.mark.parametrize("content", [
        "string",
        1234,
        ('foo', 'bar'),
        False
    ])
    def test_build_from_not_supported_content_fails(self, content):
        """Build JsonContent object from non list/dict should fail"""
        with pytest.raises(ValueError, match='Content must be JSON-like of type dict or list!.*'):
            JsonContentBuilder().from_data(content)\
                .build()

    def test_build_from_non_exists_file_fails(self):
        """Build JsonContent object from non existisng file should fail"""
        with pytest.raises(FileNotFoundError):
            JsonContentBuilder().from_file("non-exists.json")\
                .build()

    def test_build_from_malformed_json_file_fails(self, json_file):
        """Build JsonContent object from malformed JSON should fail"""
        json_file.write_text("{a: 100, b: 200}")

        with pytest.raises(json.decoder.JSONDecodeError):
            JsonContentBuilder().from_file(str(json_file))\
                .build()
