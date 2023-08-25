"""Unit tests for JsonWrapper

pytest -s -vv ./utils/json_content/test_json_wrapper.py
"""
import copy
from typing import Any

import pytest
from utils.json_content.json_wrapper import JsonWrapper
from utils.json_content.pointer import Pointer

KEY_ERROR_MSG_ON_FAIL_TO_FIND = 'Failed to find value by ".*" JSON Pointer in the document.*'
INVALID_INDEX_MSG_ON_POINTER_FAIL = 'Invalid list index .*'

# --- Pytest fixtures
@pytest.fixture(name='wrapper')
def get_wrapper() -> JsonWrapper:
    """Returns instance of JsonWrapper class with copied content"""
    return JsonWrapper(copy.deepcopy(TestData.CONTENT))

@pytest.fixture(name='content')
def get_copy_of_content() -> dict:
    """Returns deep copy of the test data content"""
    return copy.deepcopy(TestData.CONTENT)

@pytest.fixture(name='array_wrapper')
def get_array_wrapper() -> JsonWrapper:
    """Returns instance of JsonWrapper class with copied content"""
    return JsonWrapper(copy.deepcopy(ArrayTestData.CONTENT))

@pytest.fixture(name='array_content')
def get_copy_of_array_content() -> list:
    """Returns deep copy of the test data content"""
    return copy.deepcopy(ArrayTestData.CONTENT)

# --- Test data
class TestData:
    """Test data for JsonWrapper (dict) tests"""
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
    """Test data for array-based JsonWrapper"""
    CONTENT = [
        {'id': 1, 'enabled': True},
        {'id': 2, 'enabled': True, "posts": [1,2,3,55]},
        {'id': 3, 'enabled': True, "posts": []},
    ]

# --- Tests (dict content)
class TestJsonWrapperGet:
    """Tests JsonWrapper .get() method using JSON dict object"""
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
        self, wrapper: JsonWrapper, pointer: str, expected: Any):
        """Get by key pointer from dict node is successful"""
        assert wrapper.get(pointer) == expected

    @pytest.mark.parametrize('pointer, expected', (
        ('/a/b2/0', TestData.CONTENT['a']['b2'][0]),
        ('/a/b2/2', TestData.CONTENT['a']['b2'][2]),
        ('/c/0/1', TestData.CONTENT['c'][0][1]),
    ))
    def test_get_by_index_pointer(
        self, wrapper: JsonWrapper, pointer: str, expected: Any):
        """Get by index pointer from list node is successful"""
        assert wrapper.get(pointer) == expected

    @pytest.mark.parametrize('pointer', [
        "/a",
        "/a/b1",
        "/a/b2/0",
        "/c/1/enabled"
    ])
    def test_contains_on_existing_key(self,
        wrapper: JsonWrapper, pointer: str):
        """Has method returns True if pointer is valid"""
        assert pointer in wrapper
        assert Pointer.from_string(pointer) in wrapper

    @pytest.mark.parametrize('pointer', [
        "/x",
        "/a/b2/5",
        "/a/b5/3",
        "/c/5/enabled",
        "/d/b2/0/3",
        "/a/b1/key",
        "/a/b1/5"
    ])
    def test_contains_on_non_existing_key(self,
        wrapper: JsonWrapper, pointer: str):
        """Has method returns False if pointer is not exists"""
        assert pointer not in wrapper
        assert Pointer.from_string(pointer) not in wrapper

    @pytest.mark.parametrize('pointer', [
        "/a",
        "/a/b1",
        "/a/b2/0",
        "/c/1/enabled",
    ])
    def test_get_or_default_exists_returns_value(
        self, wrapper: JsonWrapper, pointer: str):
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
        self, wrapper: JsonWrapper, pointer: str):
        """Get or default method for non-existend key return default value"""
        assert wrapper.get_or_default(pointer, 333) == 333

    def test_equals(self):
        """Wrappers with same contents equals"""
        wrapper1 = JsonWrapper(copy.deepcopy(TestData.CONTENT))
        wrapper2 = JsonWrapper(copy.deepcopy(TestData.CONTENT))

        assert wrapper1.get('') == wrapper2.get('')
        assert wrapper1.get('') is not wrapper2.get('')

        wrapper1.update('/a/b1', 333)
        wrapper2.update('/a/b1', 333)

        assert wrapper1 is not wrapper2
        assert wrapper1 == wrapper2

    def test_not_equals(self):
        """Wrappers with different contents not equals"""
        wrapper1 = JsonWrapper(copy.deepcopy(TestData.CONTENT))
        wrapper2 = JsonWrapper(copy.deepcopy(TestData.CONTENT))

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
        wrapper = JsonWrapper(copy.deepcopy(TestData.CONTENT))
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
        wrapper = JsonWrapper(copy.deepcopy(TestData.CONTENT))
        assert pointer not in wrapper

    # --- Negative tests
    @pytest.mark.parametrize('ptr', TestData.INVALID_POINTERS)
    def test_get_by_invalid_pointer_fails(
        self, wrapper: JsonWrapper, ptr: str):
        """Get using strings that can't be parsed to valid pointer
        should fail with exception"""
        with pytest.raises(ValueError,
                           match='Invalid pointer.*'):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.MISSING_KEY_POINTERS)
    def test_get_by_missing_key_fails(
        self, wrapper: JsonWrapper, ptr: str):
        """Get using pointer to valid dict node, but key is missing
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.MISSING_NODE_POINTERS)
    def test_get_by_missing_node_fails(
        self, wrapper: JsonWrapper, ptr: str):
        """Get using pointer that have some missing node in the middle
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.OUT_OF_BOUNDS_INDEX_POINTERS)
    def test_get_by_oob_index_fails(
        self, wrapper: JsonWrapper, ptr: str):
        """Get using pointer to valid list node, but index is out of bounds
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.OUT_OF_BOUNDS_NODE_INDEX_POINTER)
    def test_get_by_oob_index_of_node_fails(
        self, wrapper: JsonWrapper, ptr: str):
        """Get using pointer that have out of bounds index of list node in the middle
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.INVALID_INDEX_POINTER)
    def test_get_by_invalid_index_fails(
        self, wrapper: JsonWrapper, ptr: str):
        """Get using pointer to valid list node, but index is not integer
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.INVALID_INDEX_OF_NODE_POINTER)
    def test_get_by_invalid_index_of_node_fails(
        self, wrapper: JsonWrapper, ptr: str):
        """Get using pointer that have not-integer index of list node in the middle
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.INVALID_STORAGE_POINTERS)
    def test_get_from_ivalid_storage_fails(
        self, wrapper: JsonWrapper, ptr: str):
        """Get using pointer that tries to pick key/index from not a dict/list
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.get(ptr)

class TestJsonWrapperUpdate:
    """Tests JsonWrapper .update() method using JSON dict object"""

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
        self, wrapper: JsonWrapper, content: dict,
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
        self, wrapper: JsonWrapper, content: dict,
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
        self, wrapper: JsonWrapper, content: dict,
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
        wrapper = JsonWrapper(copy.deepcopy(content))

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
        expected_content = {
            'a': [1,2,3],
            'b': {
                'id': 1,
                'guid': 333
            }
        }
        wrapper = JsonWrapper(content)
        wrapper.update('/a', expected_content['a'])
        wrapper.update('/b', expected_content['b'])

        assert wrapper == expected_content
        for ptr in [
            '/a', '/a/0', '/a/1', '/a/2',
            '/b', '/b/id', '/b/guid'
        ]:
            assert ptr in wrapper

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
        expected_content = {
            "arr": [
                [9, 12],
                [0, 1]
            ],
            "obj":  {
                "size": {
                    "height": 100,
                    "width": 300
                },
                "color": [11,22,33]
            }
        }
        wrapper = JsonWrapper(content)
        wrapper.update('/arr', expected_content['arr'])
        wrapper.update('/obj', expected_content['obj'] )

        # Check existing keys are present
        for ptr in [
            '/arr',
            '/arr/0',
            '/arr/0/0',
            '/arr/0/1',
            '/arr/1/0',
            '/arr/1/1',

            '/obj',
            '/obj/size',
            '/obj/size/height',
            '/obj/size/width',
            '/obj/color',
            '/obj/color/0',
            '/obj/color/1',
            '/obj/color/2',
        ]:
            assert ptr in wrapper

        # Check removed keys are not present
        for ptr in [
            '/arr/0/2',
            '/arr/1/2',

            '/obj/id',
            '/obj/posts',
            '/obj/posts/0',
            '/obj/posts/1',
            '/obj/posts/2',
            '/obj/location',
            '/obj/location/long',
            '/obj/location/lat',
        ]:
            assert ptr not in wrapper

        # Values updated
        assert wrapper == expected_content

    def test_update_container_with_plain_value_recalculate_structure(self):
        """Update by replacing container with single plain value
        recalculates structure"""
        content = {
            "a": [1, 2, 3],
            "b": {
                "x": 100,
                "y": 200
            }
        }
        expected_content = {
            "a": 100,
            "b": 200
        }

        wrapper = JsonWrapper(content)
        wrapper.update("/a", expected_content['a'])
        wrapper.update("/b", expected_content['b'])

        assert wrapper == expected_content

        # Nodes map recalculated
        assert '/a' in wrapper
        assert '/b' in wrapper
        assert '/a/0' not in wrapper
        assert '/a/1' not in wrapper
        assert '/a/2' not in wrapper
        assert '/b/x' not in wrapper
        assert '/b/y' not in wrapper

        # New values applied and mmay be accesed
        assert wrapper == expected_content

    # --- Negative tests
    def test_update_root_should_fail(self):
        """Update attempt to directly modify root node should fail"""
        cnt = JsonWrapper({})
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
        self, wrapper: JsonWrapper, ptr: str):
        """Update using strings that can't be parsed to valid pointer
        should fail with exception"""
        with pytest.raises(ValueError,
                           match='Invalid pointer.*'):
            wrapper.update(ptr, 333)

    def test_update_by_oob_index_fails(self, wrapper: JsonWrapper):
        """Update using pointer to valid list node, but index is out of bounds
        should fail with exception"""
        with pytest.raises(IndexError,
                           match='Update failed due to invalid list index.*'):
            wrapper.update('/a/b2/3', 333)

    @pytest.mark.parametrize("ptr", [
        '/c/5/0',
        '/c/5/enabled'
    ])
    def test_update_by_oob_node_index_fails(self, wrapper: JsonWrapper, ptr: str):
        """Update using pointer to valid list node, but index is out of bounds
        should fail with exception"""
        with pytest.raises(KeyError,
                           match=KEY_ERROR_MSG_ON_FAIL_TO_FIND):
            wrapper.update(ptr, 333)

    @pytest.mark.parametrize('ptr', TestData.INVALID_INDEX_POINTER)
    def test_update_by_invalid_index_fails(
        self, wrapper: JsonWrapper, ptr: str):
        """Update using pointer to valid list node, but index is not integer
        should fail with exception"""
        with pytest.raises(IndexError,
                           match='Update failed due to invalid list index .*'):
            wrapper.update(ptr, 333)

    @pytest.mark.parametrize('ptr', TestData.INVALID_STORAGE_POINTERS)
    def test_update_from_ivalid_storage_fails(
        self, wrapper: JsonWrapper, ptr: str):
        """Update using pointer that tries to pick key/index from not a dict/list
        should fail with exception"""
        with pytest.raises(ValueError,
                           match='Not possible to add new key/element to path node.*'):
            wrapper.update(ptr, 333)

class TestJsonWrapperDelete:
    """Tests JsonWrapper .delete() method using JSON dict object"""
    # --- Positive tests
    @pytest.mark.parametrize("ptr, delete_path, ptr_expected_to_remove", [
        ('/a/b1', "['a']['b1']", ['/a/b1']),
        ('/c', "['c']", [
            '/c',
            '/c/0', '/c/0/0', '/c/0/1', '/c/0/2',
            '/c/1', '/c1/enabled'
        ])
    ])
    def test_delete_by_key(self, wrapper: JsonWrapper, content: dict,
                                                ptr: str, delete_path: str,
                                                ptr_expected_to_remove: list):
        """Delete by key should be successful and return True"""
        exec_deletion(content, delete_path)
        assert wrapper.delete(ptr), f'Deletion of content at pointer "{ptr}" was unsuccessfull!'

        for ptr in ptr_expected_to_remove:
            assert ptr not in wrapper
        assert wrapper == content

    @pytest.mark.parametrize("ptr, delete_path, ptr_expected_to_remove", [
        # Last item deleted and pointer no longer available
        ('/a/b2/2', "['a']['b2'][2]", ['/a/b2/2']),
        # 2nd item deleted and 3rd item moves to index 1 and pointer to index 2 should be removed
        ('/c/0/1', "['c'][0][1]", ['/c/0/2']),
        # Deletes subsection element in array
        ('/d/0/arr/0', "['d'][0]['arr'][0]", [
            '/d/0/arr/0',
            '/d/0/arr/0/obj',
            '/d/0/arr/0/obj/0',
            '/d/0/arr/0/obj/1',
            '/d/0/arr/0/obj/2'
        ])
    ])
    def test_delete_by_index(self, wrapper: JsonWrapper, content: dict,
                            ptr: str, delete_path: str, ptr_expected_to_remove: list):
        """Delete by negative indicies should be successful and return True"""
        exec_deletion(content, delete_path)
        assert wrapper.delete(ptr), f'Deletion of content at pointer "{ptr}" was unsuccessfull!'

        assert wrapper.get('') == content
        for ptr in ptr_expected_to_remove:
            assert ptr not in wrapper


    def test_delete_all(self, wrapper: JsonWrapper):
        """Deletion of entire content should be successful and return True"""
        assert wrapper.delete('')
        assert wrapper.get('') == {}
        assert not wrapper._node_map

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
        wrapper = JsonWrapper(content)
        wrapper.delete('/arr')
        wrapper.delete('/obj')

        assert '/c' in wrapper
        for ptr in [
            '/arr', '/arr/0', '/arr/1', '/arr/2',
            '/obj', '/obj/id', '/obj/guid'
        ]:
            assert ptr not in  wrapper

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
        wrapper = JsonWrapper(content)
        wrapper.delete('/a/arr')
        wrapper.delete('/a/obj')

        assert '/a' in wrapper
        assert '/c' in wrapper
        for ptr in [
            '/a/arr', '/a/arr/0', '/a/arr/1', '/a/arr/2',
            '/a/obj', '/a/obj/id', '/a/obj/guid'
        ]:
            assert ptr not in wrapper

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
        self, wrapper: JsonWrapper, content: dict, ptr: str):
        """Attempt to delete by missing pointer should fail without exception
        and return False"""
        assert not wrapper.delete(ptr)
        assert wrapper.get('') == content

    @pytest.mark.parametrize('ptr', TestData.INVALID_POINTERS)
    def test_delete_invalid_pointer_fails(
        self, wrapper: JsonWrapper, ptr: str):
        """Delete by invalid pointer should fail with exception"""
        with pytest.raises(ValueError, match='Invalid pointer .*'):
            wrapper.delete(ptr)

class TestJsonWrapperIterate:
    """Tests JsonWrapper .__iter__() method using JSON dict object"""
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

        wrapper = JsonWrapper(content)
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
class TestJsonWrapperArrayGet:
    """Tests .get() method of JsonWrapper object based on JSON array"""
    # --- Positive tests
    def test_array_get_entire_content(
        self, array_wrapper: JsonWrapper):
        """Get entire array content should be successful"""
        assert array_wrapper.get('') == ArrayTestData.CONTENT

    @pytest.mark.parametrize('ptr, expected', (
        ('/0', ArrayTestData.CONTENT[0]),
        ('/1/posts/0', ArrayTestData.CONTENT[1]['posts'][0]),
    ))
    def test_array_get_by_index(
        self, array_wrapper: JsonWrapper, ptr: str, expected: Any):
        """Get element by index should be successful"""
        assert array_wrapper.get(ptr) == expected

    @pytest.mark.parametrize('ptr, expected', (
        ('/0/id', ArrayTestData.CONTENT[0]['id']),
    ))
    def test_array_get_by_key(
        self, array_wrapper: JsonWrapper, ptr: str, expected: Any):
        """Get element by mixed key and index should be successful"""
        assert array_wrapper.get(ptr) == expected

class TestJsonWrapperArrayUpdate:
    """Tests .update() method of JsonWrapper object based on JSON array"""

    @pytest.mark.parametrize('ptr, value, update_path', [
        ('/0/enabled', False, "[0]['enabled']"),
        ('/1/posts', [100, 200, 300], "[1]['posts']"),
        ('/1/posts/0', 1337, "[1]['posts'][0]"),
    ])
    def test_array_update(self,
                                               array_wrapper: JsonWrapper,
                                               array_content: list,
                                               ptr: str, value: Any, update_path: str):
        """Update value at valid pointer is successful and returns True"""
        exec_modification(array_content, update_path, value)
        assert array_wrapper.update(ptr, value)
        assert array_wrapper.get('') == array_content

    def test_array_update_add_key(self, array_wrapper: JsonWrapper,
                                        array_content: list):
        """Update is able to add new key to array's element"""
        array_content[0]['posts'] = [1, 5]
        assert array_wrapper.update('/0/posts', [1, 5])

        assert array_wrapper == array_content
        for ptr in [
            '/0/posts/2',
            '/0/posts/3'
        ]:
            assert ptr not in array_wrapper

    def test_array_update_append(self, array_wrapper: JsonWrapper, array_content: list):
        """Update is able to append to array (list)"""
        array_content[1]['posts'].append(100)
        assert array_wrapper.update('/1/posts/-', 100)

        assert array_wrapper == array_content
        assert array_wrapper.get('/1/posts/4') == array_content[1]['posts'][4]

    def test_array_update_replace_container_with_plain_value(self, array_wrapper: JsonWrapper,
                                                             array_content: list):
        """Update by replacing container with plain value should recalculate node map"""
        array_content[1] = 100
        array_wrapper.update('/1', 100)

        assert array_wrapper == array_content
        for ptr in [
            '/1/id', '/1/enabled', '/1/posts',
            '/1/posts/0', '/1/posts/1', '/1/posts/2', '/1/posts/3'
        ]:
            assert ptr not in array_wrapper

class TestJsonWrapperArrayDelete:
    """Tests .delete() method of JsonWrapper object based on JSON array"""

    @pytest.mark.parametrize('ptr, delete_path, ptr_expected_to_remove', [
        ('/0/enabled', "[0]['enabled']", ['/0/enabled']),
        ('/1/posts', "[1]['posts']", [
            '/1/posts', '/1/posts/0', '/1/posts/1', '/1/posts/2', '/1/posts/3'
        ]),
    ])
    def test_array_delete_by_key(self, array_wrapper: JsonWrapper, array_content: list,
                                ptr: str, delete_path: str, ptr_expected_to_remove: list):
        """Delete by valid key pointer should be valid and return True"""
        exec_deletion(array_content, delete_path)
        assert array_wrapper.delete(ptr)
        assert array_wrapper.get('') == array_content
        for ptr in ptr_expected_to_remove:
            assert ptr not in array_wrapper

    @pytest.mark.parametrize('ptr, delete_path, ptr_expected_to_remove', [
        # When deleting by index - only last index should be removed,
        # as elements will be shifted to the beginning of the list
        ('/1/posts/3', "[1]['posts'][3]", ['/1/posts/3']),
        ('/1/posts/0', "[1]['posts'][0]", ['/1/posts/3']),
    ])
    def test_array_delete_by_index(self, array_wrapper: JsonWrapper, array_content: list,
                                    ptr: str, delete_path: str, ptr_expected_to_remove: list):
        """Delete by valid index pointer should be valid and return True"""
        exec_deletion(array_content, delete_path)
        assert array_wrapper.delete(ptr)
        assert array_wrapper.get('') == array_content
        for ptr in ptr_expected_to_remove:
            assert ptr not in array_wrapper

    def test_array_delete_all(self, array_wrapper: JsonWrapper):
        """Deletion of entire content should be successful and return True"""
        assert array_wrapper.delete('')
        assert array_wrapper == []
        assert not array_wrapper._node_map

    def test_array_delete_value_at_root(self):
        """Delete elements of root array updates nodes successfully"""
        content = [1,2,3]
        wrapper = JsonWrapper(copy.deepcopy(content))

        del content[0]
        wrapper.delete('/0')

        assert wrapper.get('') == content
        assert '/0' in wrapper
        assert '/1' in wrapper
        assert '/2' not in wrapper

    def test_array_delete_container_at_root_recalculates_map(self, array_wrapper: JsonWrapper,
                                                    array_content: list):
        """Deletion of array element will recalculate node map.
        In this test elements will be shifted and new map should reflect that.
        """
        del array_content[2]
        del array_content[0]

        array_wrapper.delete('/2')
        array_wrapper.delete('/0')

        assert array_wrapper.get('') == array_content

        # Now element 0 is {'id': 2, 'enabled': True, "posts": [1,2,3,55]}
        for ptr in [
            '/0', '/0/id', '/0/enabled', '/0/posts',
            '/0/posts/0', '/0/posts/1', '/0/posts/2', '/0/posts/3'
        ]:
            assert ptr in array_wrapper

        # Other elements pointers should be removed
        for ptr in [
            '/1', '/1/id', '/1/enabled', '/1/posts',
                '/1/posts/0', '/1/posts/1', '/1/posts/2', '/1/posts/3'
            '/2', '/2/id', '/2/enabled', '/2/posts'
        ]:
            assert ptr not in array_wrapper



class TestJsonWrapperArrayIterate:
    """Tests JsonWrapper .__iter__() method using JSON wrapper based on JSON array"""
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

        wrapper = JsonWrapper(content)
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
