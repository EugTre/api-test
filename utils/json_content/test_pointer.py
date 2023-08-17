"""Unit tests for Pointer class

pytest -s -vv ./utils/json_content/test_pointer.py
"""
import pytest

from utils.json_content.pointer import Pointer, ReferencePointer, FilePointer


class TestPointer:
    """Tests for Pointer class"""
    VALID_POINTERS = (
        (r"/foo",('foo',)),
        ("", None),
        (r"/", ('',)),
        (r"/0/3", ("0", "3")),

        (r"/foo/bar/a", ('foo', 'bar', 'a')),
        (r"/foo//bar", ('foo', '', 'bar')),
        (r"/foo~1bar~0/baz", ('foo/bar~', 'baz')),
        (r"/  /  a", ('  ', '  a'))
    )
    INVALID_POINTERS = (
        None,
        (r"dsf"),
        (" "),
        (r"df/fd"),
        (r"!ref /a/b/c"),
        (r"!file /a/b/c")
    )

    @pytest.mark.parametrize("ptr", [v for v, _ in VALID_POINTERS])
    def test_match(self, ptr):
        assert Pointer.match(ptr)

    @pytest.mark.parametrize("ptr, expected_path", VALID_POINTERS)
    def test_parse_from_string(self, ptr, expected_path):
        pointer = Pointer.from_string(ptr)
        assert pointer.raw == ptr
        assert pointer.path == expected_path

    @pytest.mark.parametrize("path, expected_ptr", [
        (None, Pointer.from_string('')),
        (tuple(), Pointer.from_string('')),
        (('', ), Pointer.from_string('/')),
        (("a", ), Pointer.from_string('/a')),
        (("a", "b", "c"), Pointer.from_string('/a/b/c')),
        (("a", 0, "c"), Pointer.from_string('/a/0/c')),
        (('foo/bar', ), Pointer.from_string('/foo~1bar')),
        (('foo~bar', ), Pointer.from_string('/foo~0bar')),
        (('foo~/bar', ), Pointer.from_string('/foo~0~1bar')),
    ])
    def test_parse_from_path(self, path, expected_ptr):
        ptr = Pointer.from_path(path)
        assert ptr.path == expected_ptr.path
        assert ptr.rfc_pointer == expected_ptr.rfc_pointer
        assert ptr.raw == expected_ptr.raw
        assert ptr == expected_ptr

    @pytest.mark.parametrize("ptr_under_test, ptr_parent", [
        ('/a/b/c', '/a/b'),
        ('/a', ''),
        ('/0/1', '/0'),
    ])
    def test_is_child_of(self, ptr_under_test, ptr_parent):
        ptr1 = Pointer.from_string(ptr_under_test)
        ptr2 = Pointer.from_string(ptr_parent)
        assert ptr1.is_child_of(ptr2)

    @pytest.mark.parametrize("ptr_under_test, ptr_parent", [
        ('/a/b', '/a/b/c'),
        ('/0', '/0/1'),
        ('', '/a'),
        ('/a', '/a'),
        ('', '')
    ])
    def test_is_not_child_of(self, ptr_under_test, ptr_parent):
        ptr1 = Pointer.from_string(ptr_under_test)
        ptr2 = Pointer.from_string(ptr_parent)
        assert not ptr1.is_child_of(ptr2)

    @pytest.mark.parametrize("ptr_under_test, ptr_parent", [
        ('/a/b/c', '/a/b'),
        ('/0/1', '/0'),
        ('/a', ''),
    ])
    def test_get_parent(self, ptr_under_test, ptr_parent):
        ptr1 = Pointer.from_string(ptr_under_test)
        ptr2 = Pointer.from_string(ptr_parent)
        ptr1_parent = ptr1.parent()

        assert ptr1_parent == ptr2
        assert ptr1_parent.path == ptr2.path

    def test_get_parent_when_no_parent_return_self(self):
        ptr1 = Pointer.from_string('')
        ptr1_parent = ptr1.parent()
        assert ptr1_parent == ptr1
        assert ptr1_parent.path == ptr1.path

    def test_equals(self):
        raw_ptr = "/a/b/c"
        ptr1 = Pointer.from_string(raw_ptr)
        ptr2 = Pointer.from_string(raw_ptr)
        assert ptr1 == ptr2

    def test_not_equals(self):
        ptr1 = Pointer.from_string("/a/b/c")
        ptr2 = Pointer.from_string("/a/b")
        assert ptr1 != ptr2

    @pytest.mark.parametrize("ptr", INVALID_POINTERS)
    def test_not_match(self, ptr):
        assert not Pointer.match(ptr)

    @pytest.mark.parametrize("ptr", INVALID_POINTERS)
    def test_parse_invalid_fails(self, ptr):
        with pytest.raises(ValueError, match='Invalid JSON Pointer syntax .*'):
            Pointer.from_string(ptr)

class TestReferencePointer:
    """Tests for ReferencePointer class"""
    VALID_REF_POINTERS = (
        {"raw": "!ref /", "path": ("", ), "rfc": "/"},
        {"raw": "!ref /a/b/c", "path": ("a", "b", "c"), "rfc": "/a/b/c"},
        {"raw": "!ref /0/2", "path": ("0", "2",), "rfc": "/0/2"},
        {"raw": "!ref /foo//bar", "path": ('foo', '', 'bar'), "rfc": "/foo//bar"},
        {"raw": "!ref /foo~1bar~0/baz", "path": ('foo/bar~', 'baz'), "rfc": "/foo~1bar~0/baz"},
    )
    INVALID_REF_POINTERS = (
        None,
        "/a/b/c",
        "/",
        "",
        "!ref",
        "ref /a/b/c",
        "!file foo/bar.json",
        "!file"
    )

    @pytest.mark.parametrize("ptr", [v['raw'] for v in VALID_REF_POINTERS])
    def test_match(self, ptr):
        assert ReferencePointer.match(ptr)

    @pytest.mark.parametrize("ptr, expected_path, expected_rfc",
        [(v['raw'], v['path'], v['rfc']) for v in VALID_REF_POINTERS]
    )
    def test_parse(self, ptr, expected_path, expected_rfc):
        pointer = ReferencePointer.from_string(ptr)
        assert pointer.path == expected_path
        assert pointer.rfc_pointer == expected_rfc
        assert pointer.raw == ptr

    @pytest.mark.parametrize("ptr", INVALID_REF_POINTERS)
    def test_not_match_invalid_pointer(self, ptr):
        assert not ReferencePointer.match(ptr)

    def test_equals(self):
        raw_ptr = "!ref /a/b/c"
        ptr1 = ReferencePointer.from_string(raw_ptr)
        ptr2 = ReferencePointer.from_string(raw_ptr)
        assert ptr1 == ptr2

    def test_not_equals(self):
        ptr1 = ReferencePointer.from_string("!ref /a/b/c")
        ptr2 = ReferencePointer.from_string("!ref /a/b")
        assert ptr1 != ptr2

    @pytest.mark.parametrize("ptr", INVALID_REF_POINTERS)
    def test_parse_invalid_pointer_fails(self, ptr):
        with pytest.raises(ValueError, match='Invalid JSON Reference Pointer syntax.*'
                                        'JSON Reference Pointer must start with.*'):
            ReferencePointer.from_string(ptr)

    def test_parse_to_entire_fails(self):
        with pytest.raises(ValueError, match='Invalid JSON Reference Pointer syntax.*'
                                        'Refering to entire document is not allowed'):
            ReferencePointer.from_string("!ref ")

class TestFilePointer:
    """Tests for File Pointer class"""
    VALID_FILE_POINTERS = (
        (r'!file path/to/file', r'path/to/file'),
        (r'!file foo.json', r'foo.json'),
        (r'!file      foo.json', r'foo.json'),
    )
    INVALID_FILE_POINTERS = (
        None,
        "path/to/file",
        "!file",
        "file path/to/file",
        "!ref",
        "!ref /a/b/c",
        "/a/b/c"
    )

    @pytest.mark.parametrize("ptr", [v for v, _ in VALID_FILE_POINTERS])
    def test_match(self, ptr):
        assert FilePointer.match(ptr)

    @pytest.mark.parametrize("ptr, expected_path", VALID_FILE_POINTERS)
    def test_parse(self, ptr, expected_path):
        pointer = FilePointer.from_string(ptr)
        assert pointer.path == expected_path
        assert pointer.raw == ptr

    @pytest.mark.parametrize("ptr", INVALID_FILE_POINTERS)
    def test_not_match_invalid_pointer(self, ptr):
        assert not FilePointer.match(ptr)

    def test_equals(self):
        raw_ptr = r"!file C:\Files\file.json"
        ptr1 = FilePointer.from_string(raw_ptr)
        ptr2 = FilePointer.from_string(raw_ptr)
        assert ptr1 == ptr2

    def test_not_equals(self):
        ptr1 = FilePointer.from_string(r"!file C:\Files\file.json")
        ptr2 = FilePointer.from_string(r"!file Files\file.json")
        assert ptr1 != ptr2

    @pytest.mark.parametrize("ptr", INVALID_FILE_POINTERS)
    def test_parse_invalid_pointer_fails(self, ptr):
        with pytest.raises(ValueError, match='Invalid File Pointer syntax.*'):
            FilePointer.from_string(ptr)

    def test_parse_empty_fails(self):
        with pytest.raises(ValueError, match='Empty File Pointer is not allowed!'):
            FilePointer.from_string("!file ")

class TestPointersEquals:
    """Tests for equals method for difference Pointer sub-classes"""
    def test_pointer_equals_ref_pointer(self):
        ptr = Pointer.from_string("/a/b/c")
        ref_ptr = ReferencePointer.from_string("!ref /a/b/c")
        assert ptr == ref_ptr
        assert ref_ptr == ptr

    def test_pointer_not_equal_file_pointer(self):
        ptr = Pointer.from_string("/a/b/c")
        ref_ptr = ReferencePointer.from_string("!ref /a/b/c")
        file_ptr = FilePointer.from_string("!file /a/b/c")

        assert file_ptr != ptr
        assert file_ptr != ref_ptr
        assert ptr != file_ptr
        assert ref_ptr != file_ptr
