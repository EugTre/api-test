"""Unit tests for FlatJsonWrapper

pytest -s -vv ./utils/json_content/test_flat_json_wrapper.py
"""
import copy
from typing import Any

import pytest
from utils.json_content.json_wrapper import FlatJsonWrapper
from utils.json_content.pointer import Pointer

KEY_ERROR_MSG_ON_FAIL_TO_FIND = 'Failed to find value by ".*" JSON Pointer in the document.*'
INVALID_INDEX_MSG_ON_POINTER_FAIL = 'Invalid list index .*'

# --- Pytest fixtures
@pytest.fixture(name='wrapper')
def get_wrapper() -> FlatJsonWrapper:
    """Returns instance of FlatJsonWrapper class with copied content"""
    return FlatJsonWrapper(copy.deepcopy(TestData.CONTENT))

@pytest.fixture(name='content')
def get_copy_of_content() -> dict:
    """Returns deep copy of the test data content"""
    return copy.deepcopy(TestData.CONTENT)

@pytest.fixture(name='array_wrapper')
def get_array_wrapper() -> FlatJsonWrapper:
    """Returns instance of FlatJsonWrapper class with copied content"""
    return FlatJsonWrapper(copy.deepcopy(ArrayTestData.CONTENT))

@pytest.fixture(name='array_content')
def get_copy_of_array_content() -> list:
    """Returns deep copy of the test data content"""
    return copy.deepcopy(ArrayTestData.CONTENT)

# --- Test data
class TestData:
    """Test data for FlatJsonWrapper (dict) tests"""
    CONTENT = {
            "a": {
                "b1": 100,
                "b2": [1,2,3],
                "b3": "string"
            },
            "c": [
                [3,4,5],
                {"enabled": True}
            ],
            "d": [
                {
                    "arr": [
                        {
                            "obj": [300, 400 ,500]
                        }
                    ]
                }
            ],
            "": True,
            "  ": {
                "   a": 333
            },
            "foo/bar": False,
            "foo~bar": False,
            "foo~/bar": {
                "a/~b": "foo"
            },
            "xil": None
        }

    # Strings that can't be parsed to valid pointer
    INVALID_POINTERS = (
        None,
        'a',
        'a/b/c',
        '!ref /a/b1',
        '!file foo.json'
    )
    # Pointers to valid dict node, but key is missing
    MISSING_KEY_POINTERS = (
        '/missing-key',
        '/a/missing-key',
        '/c/1/missing-key'
    )
    # Pointers that have some missing node in the middle
    MISSING_NODE_POINTERS = (
        '/missing-node/a',
        '/missing-node/0',
        '/d/0/missing-node/0/obj',
        '/d/0/missing-node/0/obj/0',
        '/xil/a/b'
    )
    # Pointers to valid list node, but index is out of bounds
    OUT_OF_BOUNDS_INDEX_POINTERS = (
        '/a/b2/3',
        '/c/5/0',
        '/c/5/enabled',
    )
    # Pointers that have out of bounds index of list node in the middle
    OUT_OF_BOUNDS_NODE_INDEX_POINTER = (
        '/c/2/0',
        '/d/0/arr/5/obj/0',
    )
    # Pointer to valid list node, but index is not integer
    INVALID_INDEX_POINTER = (
        '/a/b2/key-as-index',
        '/c/0/key-as-index'
    )
    # Pointer that have not-integer index of list node in the middle
    INVALID_INDEX_OF_NODE_POINTER = (
        '/c/key-as-index/0',
        '/d/key-as-index/arr/0/obj/0'
    )
    # Pointer that tries to pick key/index from not a dict/list
    INVALID_STORAGE_POINTERS = (
        '/a/b1/key-from-int',
        '/a/b3/key-from-string',
        '//key-from-bool',
        '/xil/a',

        '/a/b1/1',
        '/a/b3/1',
        '//1'
    )
    # Pointer that have not a dict/list node in the middle
    NODE_INVALID_STORAGE_POINTERS = {
        '/a/b1/key-from-int/tgt',
        '/a/b3/key-from-string/tgt',
        '//key-from-bool/tgt',

        '/a/b1/1/tgt',
        '/a/b3/1/tgt',
        '//1/tgt'
    }

class ArrayTestData:
    """Test data for array-based FlatJsonWrapper"""
    CONTENT = [
        {'id': 1, 'enabled': True},
        {'id': 2, 'enabled': True, "posts": [1,2,3,55]},
        {'id': 3, 'enabled': True, "posts": []},
    ]

# --- Tests (dict content)
class TestFlatJsonWrapperGet:
    """Tests FlatJsonWrapper .get() method using JSON dict object"""
    # --- Positive tests
    def test_get_entire_content(self, wrapper):
        """Get entire content by root selector is successful"""
        assert wrapper.get('') == TestData.CONTENT

    @pytest.mark.parametrize('pointer, expected', (
        ('/a/b1', TestData.CONTENT['a']['b1']),
        ('/', TestData.CONTENT['']),
        ('/c/1/enabled', TestData.CONTENT['c'][1]['enabled']),
        ('/  /   a', TestData.CONTENT['  ']['   a']),
        ('/foo~1bar', TestData.CONTENT['foo/bar']),
        ('/foo~0bar', TestData.CONTENT['foo~bar']),
        ('/foo~0~1bar/a~1~0b', TestData.CONTENT['foo~/bar']['a/~b'])
    ))
    def test_get_by_key_pointer(
        self, wrapper: FlatJsonWrapper, pointer: str, expected: Any):
        """Get by key pointer from dict node is successful"""
        assert wrapper.get(pointer) == expected

    @pytest.mark.parametrize('pointer, expected', (
        ('/a/b2/0', TestData.CONTENT['a']['b2'][0]),
        ('/a/b2/2', TestData.CONTENT['a']['b2'][2]),
        ('/c/0/1', TestData.CONTENT['c'][0][1]),
    ))
    def test_get_by_index_pointer(
        self, wrapper: FlatJsonWrapper, pointer: str, expected: Any):
        """Get by index pointer from list node is successful"""
        assert wrapper.get(pointer) == expected

    @pytest.mark.parametrize('pointer', [
        "/a",
        "/a/b1",
        "/a/b2/0",
        "/c/1/enabled"
    ])
    def test_has_on_existing_key(self,
        wrapper: FlatJsonWrapper, pointer: str):
        """Has method returns True if pointer is valid"""
        assert wrapper.has(pointer)

    @pytest.mark.parametrize('pointer', [
        "/x",
        "/a/b2/5",
        "/a/b5/3",
        "/c/5/enabled",
        "/d/b2/0/3",
        "/a/b1/key",
        "/a/b1/5"
    ])
    def test_has_on_non_existing_key(self,
        wrapper: FlatJsonWrapper, pointer: str):
        """Has method returns False if pointer is not exists"""
        assert not wrapper.has(pointer)

    @pytest.mark.parametrize('pointer', [
        "/a",
        "/a/b1",
        "/a/b2/0",
        "/c/1/enabled",
    ])
    def test_get_or_default_exists_returns_value(
        self, wrapper: FlatJsonWrapper, pointer: str):
        """Get or default method for existend key return actual value"""
        assert wrapper.get_or_default(pointer, False) == wrapper.get(pointer)

    @pytest.mark.parametrize('pointer', [
        "/x",
        "/a/b2/5",
        "/a/b5/3",
        "/c/5/enabled",
        "/d/b2/0/3",
    ])
    def test_get_or_default_non_existent_returns_default(
        self, wrapper: FlatJsonWrapper, pointer: str):
        """Get or default method for non-existend key return default value"""
        assert wrapper.get_or_default(pointer, 333) == 333

    def test_equals(self):
        """Wrappers with same contents equals"""
        wrapper1 = FlatJsonWrapper(copy.deepcopy(TestData.CONTENT))
        wrapper2 = FlatJsonWrapper(copy.deepcopy(TestData.CONTENT))

        assert wrapper1.get('') == wrapper2.get('')
        assert wrapper1.get('') is not wrapper2.get('')

        wrapper1.update('/a/b1', 333)
        wrapper2.update('/a/b1', 333)

        assert wrapper1 is not wrapper2
        assert wrapper1 == wrapper2

    def test_not_equals(self):
        """Wrappers with different contents not equals"""
        wrapper1 = FlatJsonWrapper(copy.deepcopy(TestData.CONTENT))
        wrapper2 = FlatJsonWrapper(copy.deepcopy(TestData.CONTENT))

        assert wrapper1.get('') == wrapper2.get('')
        assert wrapper1.get('') is not wrapper2.get('')

        # Only one content is updated
        wrapper1.update('/a/b1', 333)

        assert wrapper1 is not wrapper2
        assert wrapper1 != wrapper2

    @pytest.mark.parametrize('pointer', [
        "/a",
        "/a/b1",
        "/a/b2/0",
        "/c/1/enabled"
    ])
    def test_check_exists_by_in(self, pointer: str):
        """Wrappers with different contents not equals"""
        wrapper = FlatJsonWrapper(copy.deepcopy(TestData.CONTENT))
        assert pointer in wrapper

    @pytest.mark.parametrize('pointer', [
        "/x",
        "//x",
        "/a/b2/5",
        "/a/b5/3",
        "/c/5/enabled",
        "/d/b2/0/3",
        "/a/b1/key",
        "/a/b1/5"
    ])
    def test_check_not_exists_by_in(self, pointer: str):
        """Wrappers with different contents not equals"""
        wrapper = FlatJsonWrapper(copy.deepcopy(TestData.CONTENT))
        assert pointer not in wrapper

    # --- Negative tests
    @pytest.mark.parametrize('ptr', TestData.INVALID_POINTERS)
    def test_get_by_invalid_pointer_fails(
        self, wrapper: FlatJsonWrapper, ptr: str):
        """Get using strings that can't be parsed to valid pointer
        should fail with exception"""
        with pytest.raises(ValueError,
                           match='Invalid JSON Pointer syntax.*'):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.MISSING_KEY_POINTERS)
    def test_get_by_missing_key_fails(
        self, wrapper: FlatJsonWrapper, ptr: str):
        """Get using pointer to valid dict node, but key is missing
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.MISSING_NODE_POINTERS)
    def test_get_by_missing_node_fails(
        self, wrapper: FlatJsonWrapper, ptr: str):
        """Get using pointer that have some missing node in the middle
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.OUT_OF_BOUNDS_INDEX_POINTERS)
    def test_get_by_oob_index_fails(
        self, wrapper: FlatJsonWrapper, ptr: str):
        """Get using pointer to valid list node, but index is out of bounds
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.OUT_OF_BOUNDS_NODE_INDEX_POINTER)
    def test_get_by_oob_index_of_node_fails(
        self, wrapper: FlatJsonWrapper, ptr: str):
        """Get using pointer that have out of bounds index of list node in the middle
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.INVALID_INDEX_POINTER)
    def test_get_by_invalid_index_fails(
        self, wrapper: FlatJsonWrapper, ptr: str):
        """Get using pointer to valid list node, but index is not integer
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.INVALID_INDEX_OF_NODE_POINTER)
    def test_get_by_invalid_index_of_node_fails(
        self, wrapper: FlatJsonWrapper, ptr: str):
        """Get using pointer that have not-integer index of list node in the middle
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.INVALID_STORAGE_POINTERS)
    def test_get_from_ivalid_storage_fails(
        self, wrapper: FlatJsonWrapper, ptr: str):
        """Get using pointer that tries to pick key/index from not a dict/list
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

class TestFlatJsonWrapperUpdate:
    """Tests FlatJsonWrapper .update() method using JSON dict object"""

    # --- Positive tests
    @pytest.mark.parametrize('ptr, value, update_path', [
        ('/a/b1', 1, "['a']['b1']"),
        ('/', 2, "['']"),
        ('/c/1/enabled', 3, "['c'][1]['enabled']"),
        ('/  /   a', 5, "['  ']['   a']"),
        ('/foo~1bar', 6, "['foo/bar']"),
        ('/foo~0bar', 7, "['foo~bar']"),
        ('/foo~0~1bar/a~1~0b', 8, "['foo~/bar']['a/~b']"),
    ])
    def test_update_by_key_pointer(
        self, wrapper: FlatJsonWrapper, content: dict,
        ptr: str, value: Any, update_path: str
    ):
        """Update by key pointer from dict node is successful"""
        exec_modification(content, update_path, value)
        assert wrapper.update(ptr, value)
        assert wrapper.get('') == content
        assert wrapper.get(ptr) == value

    @pytest.mark.parametrize('ptr, value, update_path', [
        ('/a/b2/0', 1, "['a']['b2'][0]"),
        ('/a/b2/2', 2, "['a']['b2'][2]"),
        ('/c/0/1', 5, "['c'][0][1]"),
    ])
    def test_update_by_index_pointer(
        self, wrapper: FlatJsonWrapper, content: dict,
        ptr: str, value: Any, update_path: str
    ):
        """Update by index pointer from list node is successful"""

        exec_modification(content, update_path, value)
        assert wrapper.update(ptr, value)
        assert wrapper.get('') == content
        assert wrapper.get(ptr) == value

    @pytest.mark.parametrize('ptr, value, update_path', [
        ('/x', 1, "['x']"),
        ('/c/1/allow', 2, "['c'][1]['allow']"),
        ('/a/b3', [3, 33], "['a']['b3']")
    ])
    def test_update_add_new_key(
        self, wrapper: FlatJsonWrapper, content: dict,
        ptr: str, value: Any, update_path: str
    ):
        """Update by missing key will add new key-value pair."""

        exec_modification(content, update_path, value)
        assert wrapper.update(ptr, value)
        assert wrapper.get('') == content
        assert wrapper.get(ptr) == value

    def test_update_append_index_pointer(self):
        """Update by append will add new element to list."""
        content = {
            'arr': [1,2],
            'arr_obj': [
                {'enabled': True, 'allow': False}
            ]
        }
        wrapper = FlatJsonWrapper(copy.deepcopy(content))

        value = 4
        assert wrapper.update('/arr/-', value)
        content['arr'].append(value)

        append_obj = {'enabled': False, 'allow': False}
        assert wrapper.update('/arr_obj/-', append_obj)
        content['arr_obj'].append(append_obj)

        assert wrapper.get('') == content
        assert wrapper.get('/arr/2') == value
        assert wrapper.get('/arr_obj/1') == append_obj

    def test_update_with_container_recalculates_structure(self):
        """Update by adding container will cause recalculation
        of the nodes structure"""
        content = {
            'a': 100
        }
        wrapper = FlatJsonWrapper(content)
        wrapper.update('/a', [1,2,3])
        wrapper.update('/b', {'id': 1, 'guid': 333})

        assert wrapper.get('/a/0') == 1
        assert wrapper.get('/a/1') == 2
        assert wrapper.get('/a/2') == 3
        assert wrapper.get('/b/id') == 1
        assert wrapper.get('/b/guid') == 333

    def test_update_container_with_container_recalculates_structure(self):
        """Replacement of one container with another one will cause
        recalculation of nodes structure"""
        content = {
            "arr": [
                [1,2,3],
                [4,5,6]
            ],
            "obj": {
                "id": 4,
                "posts": [3,4,5],
                "location": {
                    "long": 34.43434,
                    "lat": 35.333535
                }
            }
        }
        wrapper = FlatJsonWrapper(content)
        expected_arr = [[9, 12, 15], [0, 1]]
        expected_obj = {
            "size": {
                "height": 100,
                "width": 300
            },
            "color": [11,22,33]
        }
        wrapper.update('/arr', expected_arr)
        wrapper.update('/obj', expected_obj )

        assert wrapper.get('/arr') == expected_arr
        assert wrapper.get('/arr/0') == expected_arr[0]
        assert wrapper.get('/arr/0/0') == expected_arr[0][0]
        assert wrapper.get('/arr/0/1') == expected_arr[0][1]
        assert wrapper.get('/arr/0/2') == expected_arr[0][2]
        assert wrapper.get('/arr/1') == expected_arr[1]
        assert wrapper.get('/arr/1/0') == expected_arr[1][0]
        assert wrapper.get('/arr/1/1') == expected_arr[1][1]

        assert wrapper.get('/obj') == expected_obj
        assert wrapper.get('/obj/size') == expected_obj['size']
        assert wrapper.get('/obj/size/height') == expected_obj['size']['height']
        assert wrapper.get('/obj/size/width') == expected_obj['size']['width']
        assert wrapper.get('/obj/color') == expected_obj['color']
        assert wrapper.get('/obj/color/0') == expected_obj['color'][0]
        assert wrapper.get('/obj/color/1') == expected_obj['color'][1]
        assert wrapper.get('/obj/color/2') == expected_obj['color'][2]





    # --- Negative tests
    def test_update_root_should_fail(self):
        """Update attempt to directly modify root node should fail"""
        cnt = FlatJsonWrapper({})
        with pytest.raises(ValueError, match='Direct root modifications is not allowed!*'):
            cnt.update('', {'a': 1})

    def test_update_using_append_char_in_middle_fails(self, wrapper):
        """Update attempt to modify content using '-' (append char)
        in the middle of the pointer"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.update('/c/-/-', 100)

    @pytest.mark.parametrize('ptr', TestData.INVALID_POINTERS)
    def test_update_by_invalid_pointer_fails(
        self, wrapper: FlatJsonWrapper, ptr: str):
        """Update using strings that can't be parsed to valid pointer
        should fail with exception"""
        with pytest.raises(ValueError,
                           match='Invalid JSON Pointer syntax.*'):
            wrapper.update(ptr, 333)

    def test_update_by_oob_index_fails(self, wrapper: FlatJsonWrapper):
        """Update using pointer to valid list node, but index is out of bounds
        should fail with exception"""
        with pytest.raises(IndexError,
                           match='Update failed due to invalid list index.*'):
            wrapper.update('/a/b2/3', 333)

    @pytest.mark.parametrize("ptr", [
        '/c/5/0',
        '/c/5/enabled'
    ])
    def test_update_by_oob_node_index_fails(self, wrapper: FlatJsonWrapper, ptr: str):
        """Update using pointer to valid list node, but index is out of bounds
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.update(ptr, 333)

    @pytest.mark.parametrize('ptr', TestData.INVALID_INDEX_POINTER)
    def test_update_by_invalid_index_fails(
        self, wrapper: FlatJsonWrapper, ptr: str):
        """Update using pointer to valid list node, but index is not integer
        should fail with exception"""
        with pytest.raises(IndexError,
                           match='Update failed due to invalid list index .*'):
            wrapper.update(ptr, 333)

    @pytest.mark.parametrize('ptr', TestData.INVALID_STORAGE_POINTERS)
    def test_update_from_ivalid_storage_fails(
        self, wrapper: FlatJsonWrapper, ptr: str):
        """Update using pointer that tries to pick key/index from not a dict/list
        should fail with exception"""
        with pytest.raises(KeyError,
                           match='Not possible to add new key/element to path node.*'):
            wrapper.update(ptr, 333)

class TestFlatJsonWrapperDelete:
    """Tests FlatJsonWrapper .delete() method using JSON dict object"""
    # --- Positive tests
    @pytest.mark.parametrize("ptr, delete_path", [
        ('/a/b1', "['a']['b1']"),
        ('/c', "['c']")
    ])
    def test_delete_by_key(self, wrapper: FlatJsonWrapper, content: dict,
                                                ptr: str, delete_path: str):
        """Delete by key should be successful and return True"""
        exec_deletion(content, delete_path)
        assert wrapper.delete(ptr), f'Deletion of content at pointer "{ptr}" was unsuccessfull!'
        assert wrapper.get('') == content

    @pytest.mark.parametrize("ptr, delete_path", [
        ('/a/b2/2', "['a']['b2'][2]"),
        ('/c/0/1', "['c'][0][1]"),
        ('/d/0/arr/0/obj/2', "['d'][0]['arr'][0]['obj'][2]"),
    ])
    def test_delete_by_index(self, wrapper: FlatJsonWrapper, content: dict,
                                                   ptr: str, delete_path: str):
        """Delete by negative indicies should be successful and return True"""
        exec_deletion(content, delete_path)
        assert wrapper.delete(ptr), f'Deletion of content at pointer "{ptr}" was unsuccessfull!'
        assert wrapper.get('') == content

    def test_delete_all(self, wrapper: FlatJsonWrapper):
        """Deletion of entire content should be successful and return True"""
        assert wrapper.delete('')
        assert wrapper.get('') == {}
        assert not wrapper._node_map
        assert not wrapper.has('/a')
        assert not wrapper.has('/a/b1')
        assert not wrapper.has('/a/b2/0')

    def test_delete_container_recalculates_structure(self):
        """Deletion of container should recalculate structure and remove
        refs to deleted nodes"""
        content = {
            "arr": [1,2,3],
            "obj": {
                "id": 1,
                "guid": 333
            },
            "c": 100
        }
        wrapper = FlatJsonWrapper(content)
        wrapper.delete('/arr')
        wrapper.delete('/obj')

        assert wrapper.has('/c')
        assert not wrapper.has('/arr')
        assert not wrapper.has('/obj')

    def test_delete_nested_container_recalculates_substructure(self):
        """Deletion of container should recalculate structure and remove
        refs to deleted nodes"""
        content = {
            "a": {
                "arr": [1,2,3],
                "obj": {
                    "id": 1,
                    "guid": 333
                }
            },
            "c": 100
        }
        wrapper = FlatJsonWrapper(content)
        wrapper.delete('/a/arr')
        wrapper.delete('/a/obj')

        assert wrapper.has('/a')
        assert wrapper.has('/c')
        assert not wrapper.has('/a/arr')
        assert not wrapper.has('/a/obj')


    # --- Negative tests
    @pytest.mark.parametrize('ptr', (
        *TestData.MISSING_KEY_POINTERS,
        *TestData.MISSING_NODE_POINTERS,
        *TestData.OUT_OF_BOUNDS_INDEX_POINTERS,
        *TestData.OUT_OF_BOUNDS_NODE_INDEX_POINTER,
        *TestData.INVALID_INDEX_POINTER,
        *TestData.INVALID_INDEX_OF_NODE_POINTER,
        *TestData.INVALID_STORAGE_POINTERS
    ))
    def test_delete_missing_pointer_fails_silently(
        self, wrapper: FlatJsonWrapper, content: dict, ptr: str):
        """Attempt to delete by missing pointer should fail without exception
        and return False"""
        assert not wrapper.delete(ptr)
        assert wrapper.get('') == content

    @pytest.mark.parametrize('ptr', TestData.INVALID_POINTERS)
    def test_delete_invalid_pointer_fails(
        self, wrapper: FlatJsonWrapper, ptr: str):
        """Delete by invalid pointer should fail with exception"""
        with pytest.raises(ValueError, match='Invalid JSON Pointer syntax .*'):
            wrapper.delete(ptr)

class TestFlatJsonWrapperIterate:
    """Tests FlatJsonWrapper .__iter__() method using JSON dict object"""
    def test_iterate(self):
        """Iteration return all entities"""
        content = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3
            },
            "e": [1,2,3]
        }

        wrapper = FlatJsonWrapper(content)
        iterated = set(wrapper)
        expected = set((
            (Pointer.from_string('/a'), 1),
            (Pointer.from_string('/b/c'), 2),
            (Pointer.from_string('/b/d'), 3),
            (Pointer.from_string('/e/0'), 1),
            (Pointer.from_string('/e/1'), 2),
            (Pointer.from_string('/e/2'), 3),
        ))
        assert iterated == expected


# --- Tests (array content)
class TestFlatJsonWrapperArrayGet:
    """Tests .get() method of FlatJsonWrapper object based on JSON array"""
    # --- Positive tests
    def test_array_get_entire_content(
        self, array_wrapper: FlatJsonWrapper):
        """Get entire array content should be successful"""
        assert array_wrapper.get('') == ArrayTestData.CONTENT

    @pytest.mark.parametrize('ptr, expected', (
        ('/0', ArrayTestData.CONTENT[0]),
        ('/1/posts/0', ArrayTestData.CONTENT[1]['posts'][0]),
    ))
    def test_array_get_by_index(
        self, array_wrapper: FlatJsonWrapper, ptr: str, expected: Any):
        """Get element by index should be successful"""
        assert array_wrapper.get(ptr) == expected

    @pytest.mark.parametrize('ptr, expected', (
        ('/0/id', ArrayTestData.CONTENT[0]['id']),
    ))
    def test_array_get_by_key(
        self, array_wrapper: FlatJsonWrapper, ptr: str, expected: Any):
        """Get element by mixed key and index should be successful"""
        assert array_wrapper.get(ptr) == expected

class TestFlatJsonWrapperArrayUpdate:
    """Tests .update() method of FlatJsonWrapper object based on JSON array"""

    @pytest.mark.parametrize('ptr, value, update_path', [
        ('/0/enabled', False, "[0]['enabled']"),
        ('/1/posts', [100, 200, 300], "[1]['posts']"),
        ('/1/posts/0', 1337, "[1]['posts'][0]"),
    ])
    def test_array_update(self,
                                               array_wrapper: FlatJsonWrapper,
                                               array_content: list,
                                               ptr: str, value: Any, update_path: str):
        """Update value at valid pointer is successful and returns True"""
        exec_modification(array_content, update_path, value)
        assert array_wrapper.update(ptr, value)
        assert array_wrapper.get('') == array_content

    def test_array_update_add_key(self,
                                               array_wrapper: FlatJsonWrapper,
                                               array_content: list):
        """Update is able to add new key to array's element"""
        array_content[0]['posts'] = [1, 5, 76]
        assert array_wrapper.update('/0/posts', [1, 5, 76])
        assert array_wrapper.get('') == array_content

    def test_array_update_append(self,
                                               array_wrapper: FlatJsonWrapper,
                                               array_content: list):
        """Update is able to append to array (list)"""
        array_content[1]['posts'].append(100)
        assert array_wrapper.update('/1/posts/-', 100)
        assert array_wrapper.get('') == array_content

class TestFlatJsonWrapperArrayDelete:
    """Tests .delete() method of FlatJsonWrapper object based on JSON array"""

    @pytest.mark.parametrize('ptr, delete_path', [
        ('/0/enabled', "[0]['enabled']"),
        ('/1/enabled', "[1]['enabled']"),
        ('/1/posts', "[1]['posts']"),
    ])
    def test_array_delete_by_key(self,
                                               array_wrapper: FlatJsonWrapper,
                                               array_content: list,
                                               ptr: str, delete_path: str):
        """Delete by valid key pointer should be valid and return True"""
        exec_deletion(array_content, delete_path)
        assert array_wrapper.delete(ptr)
        assert array_wrapper.get('') == array_content

    @pytest.mark.parametrize('ptr, delete_path', [
        ('/0', "[0]"),
        ('/1/posts/1', "[1]['posts'][1]"),
        ('/1/posts/0', "[1]['posts'][0]"),
    ])
    def test_array_delete_by_index(self,
                                               array_wrapper: FlatJsonWrapper,
                                               array_content: list,
                                               ptr: str, delete_path: str):
        """Delete by valid index pointer should be valid and return True"""
        exec_deletion(array_content, delete_path)
        assert array_wrapper.delete(ptr)
        assert array_wrapper.get('') == array_content

    def test_array_delete_all(self,
                                               array_wrapper: FlatJsonWrapper):
        """Deletion of entire content should be successful and return True"""
        assert array_wrapper.delete('')
        assert array_wrapper.get('') == []

class TestFlatJsonWrapperArrayIterate:
    """Tests FlatJsonWrapper .__iter__() method using JSON wrapper based on JSON array"""
    def test_iterate(self):
        """Iteration return all entities"""
        content = [
            1,
            2,
            {"a": 1, "b": 2},
            [
                [3, 4]
            ]
        ]

        wrapper = FlatJsonWrapper(content)
        iterated = set(wrapper)
        expected = set((
            (Pointer.from_string('/0'), 1),
            (Pointer.from_string('/1'), 2),
            (Pointer.from_string('/2/a'), 1),
            (Pointer.from_string('/2/b'), 2),
            (Pointer.from_string('/3/0/0'), 3),
            (Pointer.from_string('/3/0/1'), 4),
        ))
        assert iterated == expected


# --- Helper functions
def exec_modification(cnt: dict, exec_str: str, value: Any) -> None:
    """Helper function to update content dictionary according to given path.

    Args:
        cnt (dict): dictionary to update
        exec_str (str): path to key for modiciation, e.g. "['a'][0]" for cnt['a'][0]
        value (Any): value to set.

    Example:
    ```
    exec_modification(content, "['a']['b'][0]['c']", 100)
    # equals to command: content['a']['b'][0]['c'] = 100
    ```
    """
    # Exec is used as most simple and short way to apply changes
    # pylint: disable-next=exec-used
    exec(f'content{exec_str} = value', {}, {"content": cnt, "value": value})

def exec_deletion(cnt: dict, exec_str: str) -> None:
    """Helper function to delete key from content dictionary/list according to given path.

    Args:
        cnt (dict): dictionary to update
        exec_str (str): path to key for modiciation, e.g. "['a'][0]" for cnt['a'][0].

    Example:
    ```
    exec_deletion(content, "['a']['b'][0]['c']")
    # equals to command: del content['a']['b'][0]['c']
    ```
    """
    # Exec is used as most simple and short way to apply changes
    # pylint: disable-next=exec-used
    exec(f'del content{exec_str}', {}, {"content": cnt})
