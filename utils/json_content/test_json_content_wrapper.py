"""Unit tests for JsonContentWrapper

pytest -s -vv ./utils/json_content/test_json_content_wrapper.py
"""
import copy
from typing import Any

import pytest
from utils.json_content.json_content_wrapper import JsonContentWrapper

# --- Pytest fixtures
@pytest.fixture(name='wrapper')
def get_wrapper() -> JsonContentWrapper:
    """Returns instance of JsonContentWrapper class with copied content"""
    return JsonContentWrapper(copy.deepcopy(TestData.CONTENT))

@pytest.fixture(name='content')
def get_copy_of_content() -> dict:
    """Returns deep copy of the test data content"""
    return copy.deepcopy(TestData.CONTENT)

@pytest.fixture(name='array_wrapper')
def get_array_wrapper() -> JsonContentWrapper:
    """Returns instance of JsonContentWrapper class with copied content"""
    return JsonContentWrapper(copy.deepcopy(ArrayTestData.CONTENT))

@pytest.fixture(name='array_content')
def get_copy_of_array_content() -> list:
    """Returns deep copy of the test data content"""
    return copy.deepcopy(ArrayTestData.CONTENT)

# --- Test data
class TestData:
    """Test data for JsonContentWrapper (dict) tests"""
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
            }
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
        '/d/0/missing-node/0/obj/0'
    )
    # Pointers to valid list node, but index is out of bounds
    OUT_OF_BOUNDS_INDEX_POINTERS = (
        '/a/b2/3',
        '/a/b2/-4',
        '/c/5/0',
        '/c/-5/0',
        '/c/5/enabled',
        '/c/-5/enabled'
    )
    # Pointers that have out of bounds index of list node in the middle
    OUT_OF_BOUNDS_NODE_INDEX_POINTER = (
        '/c/2/0',
        '/c/-3/0',
        '/d/0/arr/5/obj/0',
        '/d/0/arr/-5/obj/0',
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
    """Test data for array-based JsonContentWrapper"""
    CONTENT = [
        {'id': 1, 'enabled': True},
        {'id': 2, 'enabled': True, "posts": [1,2,3,55]},
        {'id': 3, 'enabled': True, "posts": []},
    ]

# --- Tests (dict content)
class TestJsonContentWrapperGet:
    """Tests JsonContentWrapper .get() method using JSON dict object"""
    # --- Positive tests
    def test_json_content_wrapper_get_entire_content(self, wrapper):
        """Get entire content by root selector is successful"""
        assert wrapper.get('') == TestData.CONTENT

    @pytest.mark.parametrize('pointer, expected', (
        ('/a/b1', TestData.CONTENT['a']['b1']),
        ('/', TestData.CONTENT['']),
        ('/c/1/enabled', TestData.CONTENT['c'][1]['enabled']),
        ('/c/-1/enabled', TestData.CONTENT['c'][-1]['enabled']),
        ('/  /   a', TestData.CONTENT['  ']['   a']),
        ('/foo~1bar', TestData.CONTENT['foo/bar']),
        ('/foo~0bar', TestData.CONTENT['foo~bar']),
        ('/foo~0~1bar/a~1~0b', TestData.CONTENT['foo~/bar']['a/~b'])
    ))
    def test_json_content_wrapper_get_by_key_pointer(
        self, wrapper: JsonContentWrapper, pointer: str, expected: Any):
        """Get by key pointer from dict node is successful"""
        assert wrapper.get(pointer) == expected

    @pytest.mark.parametrize('pointer, expected', (
        ('/a/b2/0', TestData.CONTENT['a']['b2'][0]),
        ('/a/b2/2', TestData.CONTENT['a']['b2'][2]),
        ('/a/b2/-2', TestData.CONTENT['a']['b2'][-2]),
        ('/a/b2/-0', TestData.CONTENT['a']['b2'][-0]),
        ('/c/0/1', TestData.CONTENT['c'][0][1]),
        ('/c/-2/1', TestData.CONTENT['c'][-2][1]),
    ))
    def test_json_content_wrapper_get_by_index_pointer(
        self, wrapper: JsonContentWrapper, pointer: str, expected: Any):
        """Get by index pointer from list node is successful"""
        assert wrapper.get(pointer) == expected

    @pytest.mark.parametrize('pointer', [
        "/a",
        "/a/b1",
        "/a/b2/0",
        "/a/b2/-1",
        "/c/1/enabled"
    ])
    def test_json_content_wrapper_has_on_existing_key(self,
        wrapper: JsonContentWrapper, pointer: str):
        """Has method returns True if pointer is valid"""
        assert wrapper.has(pointer)

    @pytest.mark.parametrize('pointer', [
        "/x",
        "/a/b2/5",
        "/a/b2/-5",
        "/a/b5/3",
        "/c/5/enabled",
        "/d/b2/0/3",
        "/d/b2/-5/key",
        "/a/b1/key",
        "/a/b1/5"
    ])
    def test_json_content_wrapper_has_on_non_existing_key(self,
        wrapper: JsonContentWrapper, pointer: str):
        """Has method returns False if pointer is not exists"""
        assert not wrapper.has(pointer)

    @pytest.mark.parametrize('pointer', [
        "/a",
        "/a/b1",
        "/a/b2/0",
        "/a/b2/-1",
        "/c/1/enabled",
    ])
    def test_json_content_wrapper_get_or_default_exists_returns_value(
        self, wrapper: JsonContentWrapper, pointer: str):
        """Get or default method for existend key return actual value"""
        assert wrapper.get_or_default(pointer, False) == wrapper.get(pointer)

    @pytest.mark.parametrize('pointer', [
        "/x",
        "/a/b2/5",
        "/a/b2/-5",
        "/a/b5/3",
        "/c/5/enabled",
        "/d/b2/0/3",
        "/d/b2/-5/key"
    ])
    def test_json_content_wrapper_get_or_default_non_existent_returns_default(
        self, wrapper: JsonContentWrapper, pointer: str):
        """Get or default method for non-existend key return default value"""
        assert wrapper.get_or_default(pointer, 333) == 333

    def test_json_content_wrapper_equals(self):
        """Wrappers with same contents equals"""
        wrapper1 = JsonContentWrapper(copy.deepcopy(TestData.CONTENT))
        wrapper2 = JsonContentWrapper(copy.deepcopy(TestData.CONTENT))

        assert wrapper1.get('') == wrapper2.get('')
        assert wrapper1.get('') is not wrapper2.get('')

        wrapper1.update('/a/b1', 333)
        wrapper2.update('/a/b1', 333)

        assert wrapper1 is not wrapper2
        assert wrapper1 == wrapper2

    def test_json_content_wrapper_not_equals(self):
        """Wrappers with different contents not equals"""
        wrapper1 = JsonContentWrapper(copy.deepcopy(TestData.CONTENT))
        wrapper2 = JsonContentWrapper(copy.deepcopy(TestData.CONTENT))

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
        "/a/b2/-1",
        "/c/1/enabled"
    ])
    def test_json_content_wrapper_check_exists_by_in(self, pointer: str):
        """Wrappers with different contents not equals"""
        wrapper = JsonContentWrapper(copy.deepcopy(TestData.CONTENT))
        assert pointer in wrapper

    @pytest.mark.parametrize('pointer', [
        "/x",
        "//x",
        "/a/b2/5",
        "/a/b2/-5",
        "/a/b5/3",
        "/c/5/enabled",
        "/c/-5/0",
        "/d/b2/0/3",
        "/d/b2/-5/key",
        "/a/b1/key",
        "/a/b1/5"
    ])
    def test_json_content_wrapper_check_not_exists_by_in(self, pointer: str):
        """Wrappers with different contents not equals"""
        wrapper = JsonContentWrapper(copy.deepcopy(TestData.CONTENT))
        assert pointer not in wrapper

    # --- Negative tests
    @pytest.mark.parametrize('ptr', TestData.INVALID_POINTERS)
    def test_json_content_wrapper_get_by_invalid_pointer_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Get using strings that can't be parsed to valid pointer
        should fail with exception"""
        with pytest.raises(ValueError,
                           match='Invalid pointer.*'):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.MISSING_KEY_POINTERS)
    def test_json_content_wrapper_get_by_missing_key_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Get using pointer to valid dict node, but key is missing
        should fail with exception"""
        with pytest.raises(KeyError,
                           match='Key ".*" is not present.*'):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.MISSING_NODE_POINTERS)
    def test_json_content_wrapper_get_by_missing_node_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Get using pointer that have some missing node in the middle
        should fail with exception"""
        with pytest.raises(KeyError,
                           match='Key ".*" is not present.*'):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.OUT_OF_BOUNDS_INDEX_POINTERS)
    def test_json_content_wrapper_get_by_oob_index_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Get using pointer to valid list node, but index is out of bounds
        should fail with exception"""
        with pytest.raises(IndexError,
                           match='Index ".*" is out of range for given node.*'):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.OUT_OF_BOUNDS_NODE_INDEX_POINTER)
    def test_json_content_wrapper_get_by_oob_index_of_node_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Get using pointer that have out of bounds index of list node in the middle
        should fail with exception"""
        with pytest.raises(IndexError,
                           match='Index ".*" is out of range for given node.*'):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.INVALID_INDEX_POINTER)
    def test_json_content_wrapper_get_by_invalid_index_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Get using pointer to valid list node, but index is not integer
        should fail with exception"""
        with pytest.raises(IndexError,
                           match='Invalid list index .*'):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.INVALID_INDEX_OF_NODE_POINTER)
    def test_json_content_wrapper_get_by_invalid_index_of_node_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Get using pointer that have not-integer index of list node in the middle
        should fail with exception"""
        with pytest.raises(IndexError,
                           match='Invalid list index .*'):
            wrapper.get(ptr)

    @pytest.mark.parametrize('ptr', TestData.INVALID_STORAGE_POINTERS)
    def test_json_content_wrapper_get_from_ivalid_storage_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Get using pointer that tries to pick key/index from not a dict/list
        should fail with exception"""
        with pytest.raises(KeyError,
                           match='Path node ".*" at pointer ".*" is not a dict or list.*'):
            wrapper.get(ptr)

class TestJsonContentWrapperUpdate:
    """Tests JsonContentWrapper .update() method using JSON dict object"""

    # --- Positive tests
    @pytest.mark.parametrize('ptr, value, update_path', [
        ('/a/b1', 1, "['a']['b1']"),
        ('/', 2, "['']"),
        ('/c/1/enabled', 3, "['c'][1]['enabled']"),
        ('/c/-1/enabled', 4, "['c'][-1]['enabled']"),
        ('/  /   a', 5, "['  ']['   a']"),
        ('/foo~1bar', 6, "['foo/bar']"),
        ('/foo~0bar', 7, "['foo~bar']"),
        ('/foo~0~1bar/a~1~0b', 8, "['foo~/bar']['a/~b']"),
    ])
    def test_json_content_wrapper_update_by_key_pointer(
        self, wrapper: JsonContentWrapper, content: dict,
        ptr: str, value: Any, update_path: str
    ):
        """Update by key pointer from dict node is successful"""
        exec_modification(content, update_path, value)
        assert wrapper.update(ptr, value)
        assert wrapper.get('') == content

    @pytest.mark.parametrize('ptr, value, update_path', [
        ('/a/b2/0', 1, "['a']['b2'][0]"),
        ('/a/b2/2', 2, "['a']['b2'][2]"),
        ('/a/b2/-2', 3, "['a']['b2'][-2]"),
        ('/a/b2/-0', 4, "['a']['b2'][-0]"),
        ('/c/0/1', 5, "['c'][0][1]"),
        ('/c/-2/1', 6, "['c'][-2][1]"),
    ])
    def test_json_content_wrapper_update_by_index_pointer(
        self, wrapper: JsonContentWrapper, content: dict,
        ptr: str, value: Any, update_path: str
    ):
        """Update by index pointer from list node is successful"""

        exec_modification(content, update_path, value)
        assert wrapper.update(ptr, value)
        assert wrapper.get('') == content

    @pytest.mark.parametrize('ptr, value, update_path', [
        ('/x', 1, "['x']"),
        ('/c/1/allow', 2, "['c'][1]['allow']"),
        ('/a/b3', [3, 33], "['a']['b3']")
    ])
    def test_json_content_wrapper_update_add_new_key(
        self, wrapper: JsonContentWrapper, content: dict,
        ptr: str, value: Any, update_path: str
    ):
        """Update by missing key will add new key-value pair."""

        exec_modification(content, update_path, value)
        assert wrapper.update(ptr, value)
        assert wrapper.get('') == content

    def test_json_content_wrapper_update_append_index_pointer(
        self, wrapper: JsonContentWrapper, content):
        """Update by append will add new element of list."""
        assert wrapper.update('/a/b2/-', 4)
        content['a']['b2'].append(4)

        assert wrapper.update('/c/-', {'enabled': False, 'allow': False})
        content['c'].append({'enabled': False, 'allow': False})

        assert wrapper.get('') == content

    # --- Negative tests
    def test_json_content_wrapper_update_root_should_fail(self):
        """Update attempt to directly modify root node should fail"""
        cnt = JsonContentWrapper({})
        with pytest.raises(ValueError, match='Direct root modifications is not allowed!*'):
            cnt.update('', {'a': 1})

    def test_json_content_wrapper_update_using_append_char_in_middle_fails(self, wrapper):
        """Update attempt to modify content using '-' (append char)
        in the middle of the pointer"""
        with pytest.raises(IndexError, match='Invalid list index ".*" at node.*'):
            wrapper.update('/c/-/-', 100)

    @pytest.mark.parametrize('ptr', TestData.INVALID_POINTERS)
    def test_json_content_wrapper_update_by_invalid_pointer_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Update using strings that can't be parsed to valid pointer
        should fail with exception"""
        with pytest.raises(ValueError,
                           match='Invalid pointer.*'):
            wrapper.update(ptr, 333)

    @pytest.mark.parametrize('ptr', TestData.OUT_OF_BOUNDS_INDEX_POINTERS)
    def test_json_content_wrapper_update_by_oob_index_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Update using pointer to valid list node, but index is out of bounds
        should fail with exception"""
        with pytest.raises(IndexError,
                           match='Index ".*" is out of range for given node.*'):
            wrapper.update(ptr, 333)

    @pytest.mark.parametrize('ptr', TestData.INVALID_INDEX_POINTER)
    def test_json_content_wrapper_update_by_invalid_index_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Update using pointer to valid list node, but index is not integer
        should fail with exception"""
        with pytest.raises(IndexError,
                           match='Invalid list index .*'):
            wrapper.update(ptr, 333)

    @pytest.mark.parametrize('ptr', TestData.INVALID_STORAGE_POINTERS)
    def test_json_content_wrapper_update_from_ivalid_storage_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Update using pointer that tries to pick key/index from not a dict/list
        should fail with exception"""
        with pytest.raises(KeyError,
                           match='Path node ".*" at pointer ".*" is not a dict or list.*'):
            wrapper.update(ptr, 333)

class TestJsonContentWrapperDelete:
    """Tests JsonContentWrapper .delete() method using JSON dict object"""
    # --- Positive tests
    @pytest.mark.parametrize("ptr, delete_path", [
        ('/a/b1', "['a']['b1']"),
        ('/c', "['c']")
    ])
    def test_json_content_wrapper_delete_by_key(self, wrapper: JsonContentWrapper, content: dict,
                                                ptr: str, delete_path: str):
        """Delete by key should be successful and return True"""
        exec_deletion(content, delete_path)
        assert wrapper.delete(ptr), f'Deletion of content at pointer "{ptr}" was unsuccessfull!'
        assert wrapper.get('') == content

    @pytest.mark.parametrize("ptr, delete_path", [
        ('/a/b2/-1', "['a']['b2'][-1]"),
        ('/c/-2/-3', "['c'][-2][-3]"),
        ('/d/0/arr/0/obj/2', "['d'][0]['arr'][0]['obj'][2]"),
    ])
    def test_json_content_wrapper_delete_by_index(self, wrapper: JsonContentWrapper, content: dict,
                                                   ptr: str, delete_path: str):
        """Delete by negative indicies should be successful and return True"""
        exec_deletion(content, delete_path)
        assert wrapper.delete(ptr), f'Deletion of content at pointer "{ptr}" was unsuccessfull!'
        assert wrapper.get('') == content

    def test_json_content_wrapper_delete_all(self, wrapper: JsonContentWrapper):
        """Deletion of entire content should be successful and return True"""
        assert wrapper.delete('')
        assert wrapper.get('') == {}

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
    def test_json_content_wrapper_delete_missing_pointer_fails_silently(
        self, wrapper: JsonContentWrapper, content: dict, ptr: str):
        """Attempt to delete by missing pointer should fail without exception
        and return False"""
        assert not wrapper.delete(ptr)
        assert wrapper.get('') == content

    @pytest.mark.parametrize('ptr', TestData.INVALID_POINTERS)
    def test_json_content_wrapper_delete_invalid_pointer_fails(
        self, wrapper: JsonContentWrapper, ptr: str):
        """Delete by invalid pointer should fail with exception"""
        with pytest.raises(ValueError, match='Invalid pointer.*'):
            wrapper.delete(ptr)

# --- Tests (array content)
class TestJsonContentWrapperArrayGet:
    """Tests .get() method of JsonContentWrapper object based on JSON array"""
    # --- Positive tests
    def test_json_content_wrapper_array_get_entire_content(
        self, array_wrapper: JsonContentWrapper):
        """Get entire array content should be successful"""
        assert array_wrapper.get('') == ArrayTestData.CONTENT

    @pytest.mark.parametrize('ptr, expected', (
        ('/0', ArrayTestData.CONTENT[0]),
        ('/-0', ArrayTestData.CONTENT[-0]),
        ('/-1', ArrayTestData.CONTENT[-1]),
        ('/1/posts/0', ArrayTestData.CONTENT[1]['posts'][0]),
        ('/1/posts/-1', ArrayTestData.CONTENT[1]['posts'][-1]),
    ))
    def test_json_content_wrapper_array_get_by_index(
        self, array_wrapper: JsonContentWrapper, ptr: str, expected: Any):
        """Get element by index should be successful"""
        assert array_wrapper.get(ptr) == expected

    @pytest.mark.parametrize('ptr, expected', (
        ('/0/id', ArrayTestData.CONTENT[0]['id']),
        ('/-1/enabled', ArrayTestData.CONTENT[-1]['enabled']),
    ))
    def test_json_content_wrapper_array_get_by_key(
        self, array_wrapper: JsonContentWrapper, ptr: str, expected: Any):
        """Get element by mixed key and index should be successful"""
        assert array_wrapper.get(ptr) == expected

class TestJsonContentWrapperArrayUpdate:
    """Tests .update() method of JsonContentWrapper object based on JSON array"""

    @pytest.mark.parametrize('ptr, value, update_path', [
        ('/0/enabled', False, "[0]['enabled']"),
        ('/-1/posts', [100, 200, 300], "[-1]['posts']"),
        ('/1/posts/0', 1337, "[1]['posts'][0]"),
    ])
    def test_json_content_wrapper_array_update(self,
                                               array_wrapper: JsonContentWrapper,
                                               array_content: list,
                                               ptr: str, value: Any, update_path: str):
        """Update value at valid pointer is successful and returns True"""
        exec_modification(array_content, update_path, value)
        assert array_wrapper.update(ptr, value)
        assert array_wrapper.get('') == array_content

    def test_json_content_wrapper_array_update_add_key(self,
                                               array_wrapper: JsonContentWrapper,
                                               array_content: list):
        """Update is able to add new key to array's element"""
        array_content[0]['posts'] = [1, 5, 76]
        assert array_wrapper.update('/0/posts', [1, 5, 76])
        assert array_wrapper.get('') == array_content

    def test_json_content_wrapper_array_update_append(self,
                                               array_wrapper: JsonContentWrapper,
                                               array_content: list):
        """Update is able to append to array (list)"""
        array_content[-1]['posts'].append(100)
        assert array_wrapper.update('/-1/posts/-', 100)
        assert array_wrapper.get('') == array_content

class TestJsonContentWrapperArrayDelete:
    """Tests .delete() method of JsonContentWrapper object based on JSON array"""

    @pytest.mark.parametrize('ptr, delete_path', [
        ('/0/enabled', "[0]['enabled']"),
        ('/1/enabled', "[1]['enabled']"),
        ('/-1/posts', "[-1]['posts']"),
    ])
    def test_json_content_wrapper_array_delete_by_key(self,
                                               array_wrapper: JsonContentWrapper,
                                               array_content: list,
                                               ptr: str, delete_path: str):
        """Delete by valid key pointer should be valid and return True"""
        exec_deletion(array_content, delete_path)
        assert array_wrapper.delete(ptr)
        assert array_wrapper.get('') == array_content

    @pytest.mark.parametrize('ptr, delete_path', [
        ('/-1', "[-1]"),
        ('/1/posts/1', "[1]['posts'][1]"),
        ('/1/posts/-1', "[1]['posts'][-1]"),
    ])
    def test_json_content_wrapper_array_delete_by_index(self,
                                               array_wrapper: JsonContentWrapper,
                                               array_content: list,
                                               ptr: str, delete_path: str):
        """Delete by valid index pointer should be valid and return True"""
        exec_deletion(array_content, delete_path)
        assert array_wrapper.delete(ptr)
        assert array_wrapper.get('') == array_content

    def test_json_content_wrapper_array_delete_all(self,
                                               array_wrapper: JsonContentWrapper):
        """Deletion of entire content should be successful and return True"""
        assert array_wrapper.delete('')
        assert array_wrapper.get('') == []



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
