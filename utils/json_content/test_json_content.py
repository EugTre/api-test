"""Unit tests for JsonContent

pytest -s -vv ./utils/json_content/test_json_content.py
"""
import pytest

from utils.json_content.json_content import JsonContent, JsonContentBuilder

class TestJsonContent:
    """Tests for JsonContent object based on JSON object"""

    # --- Init
    def test_json_content_build_from_data_copy(self):
        """Build with data copy is successful"""
        content = {
            'a': 1,
            'b': {
                'c': 3,
                'd': [1,2,3]
            }
        }
        cnt = JsonContentBuilder().from_data(content, make_copy=True).build()
        raw_content = cnt.get('')

        assert raw_content == content
        assert raw_content is not content
        assert raw_content['b'] is not content['b']
        assert raw_content['b']['d'] is not content['b']['d']

    def test_json_content_build_from_data_nocopy(self):
        """Build without data copy is successful"""
        content = {
            'a': 1,
            'b': {
                'c': 3,
                'd': [1,2,3]
            }
        }
        cnt = JsonContentBuilder().from_data(content).build()
        raw_content = cnt.get('')

        assert raw_content == content
        assert raw_content is content
        assert raw_content['b'] is content['b']
        assert raw_content['b']['d'] is content['b']['d']




#     def test_json_content_wrapper_delete_bulk(self):
#         """Tests delete method for bulk delete"""
#         content = copy.deepcopy(self.CONTENT)
#         cnt = JsonContentWrapper(copy.deepcopy(self.CONTENT))

#         cnt.delete((
#             '/a/b1',
#             '/c/1',
#             '/d/0/arr/0/obj/2',
#             '/d/0/arr/0/obj/1'
#         ))
#         del content['a']['b1']
#         del content['c'][1]
#         del content['d'][0]['arr'][0]['obj'][2]
#         del content['d'][0]['arr'][0]['obj'][1]

#         assert cnt.get('') == content



#     def test_json_content_wrapper_delete_bulk_with_missing_pointrs(self):
#         """Tests delete method for bulk delete, but some
#         of the pointers missing"""
#         content = copy.deepcopy(self.CONTENT)
#         cnt = JsonContentWrapper(copy.deepcopy(self.CONTENT))

#         cnt.delete((
#             '/a/b4',
#             '/a/b3/4',
#             '/c/1',
#             '/d/0/arr/0/obj/4',
#             '/d/0/arr/0/obj/2'
#         ))

#         del content['c'][1]
#         del content['d'][0]['arr'][0]['obj'][2]

#         assert cnt.get('') == content
