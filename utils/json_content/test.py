"""Unit tests for JsonContent

pytest -s -vv ./utils/json_content/test.py
"""
import pytest

from utils.json_content.json_content import JsonContent
from utils.json_content.pointer import Pointer, PointerType

def test_json_content_get():
    content = {
        "a": {
            "b1": 100,
            "b2": [1,2,3]
        }
    }

    ctn = JsonContent(content)

    # By string pointer
    assert ctn.get('/a/b1') == content['a']['b1']
    assert ctn.get('/a/b2') == content['a']['b2']
    assert ctn.get('/a/b2/0') == content['a']['b2'][0]
    assert ctn.get('/a/b2/1') == content['a']['b2'][1]
    assert ctn.get('/a/b2/2') == content['a']['b2'][2]
    assert ctn.get() == content
    assert ctn.get('/') == content


def test_pointers():
    ptrs = (
        ("/foo", PointerType.POINTER, ('foo',)),
        ("/", PointerType.POINTER, ('',)),
        ("/foo/bar/a", PointerType.POINTER, ('foo', 'bar', 'a')),
        ("!ref /foo/bar", PointerType.REFERENCE, ('foo', 'bar')),
        ("!ref    /foo   /bar   /a  ", PointerType.REFERENCE, ('foo', 'bar', 'a')),
        ("!file content/file.json", PointerType.FILE_REF, 'content/file.json'),
        ("!file    content  /  file.json", PointerType.FILE_REF, 'content  /  file.json')
    )

    for ptr, ptr_type, ptr_path in ptrs:
        assert Pointer.match_any_pointer(ptr)
        pointer = Pointer.from_string(ptr)

        assert pointer.raw == ptr
        assert pointer.type == ptr_type
        assert pointer.pointer == ptr_path

        match ptr_type:
            case PointerType.POINTER:
                assert pointer.is_pointer
            case PointerType.REFERENCE:
                assert pointer.is_reference
            case PointerType.FILE_REF:
                assert pointer.is_file

def test_pointers_check_is_pointer():
    for ptr in (
        '/a/b/c',
        '!ref /a/b/c',
        '!file path/to/file'
    ):
        assert Pointer.match_any_pointer(ptr)

    for ptr in (
        '!ref /a/b/c',
        '!file path/to/file',
    ):
        assert Pointer.match_ref_pointer(ptr)

    for ptr in (
        'a/b/c',
        'a b c',
        'ref a b c',
        'file a b c'
    ):
        assert not Pointer.match_any_pointer(ptr)

    for ptr in (
        '/a/b/c',
        'ref a b c',
        'file a b c',
        'file a b c'
    ):
        assert not Pointer.match_ref_pointer(ptr)



def test_pointers_invalid():
    ptrs = (
        (None, r'Pointer should be a string in format .*'),
        ('a/b/c', r'Pointer ".*" should start from root "/" element.'),
        ('/a//b', r'Undefined \(empty\) reference in ".*"'),
        ('!file ', r'Pointer ".*" has invalid/empty path!'),
    )

    for ptr, exc_msg in ptrs:
        with pytest.raises(ValueError, match=exc_msg):
            Pointer.from_string(ptr)
