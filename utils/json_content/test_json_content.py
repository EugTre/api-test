"""Unit tests for JsonContent

pytest -s -vv ./utils/json_content/test_json_content.py
"""
from utils.json_content.json_content import JsonContent

class TestJsonContentWrapper:
    """Tests for JsonContent object based on JSON object"""

    # --- Init
    def test_json_content_wrapper_init(self):
        """Basic test of initialization method"""
        content = {
            'a': 1,
            'b': {
                'c': 3,
                'd': [1,2,3]
            }
        }
        cnt = JsonContent(content)
        cnt_copy = JsonContent(content, make_copy=True)

        assert cnt.get() == content
        assert cnt_copy.get() == content

        content['c'] = 100
        assert cnt.get() == content
        assert cnt_copy.get() != content


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
