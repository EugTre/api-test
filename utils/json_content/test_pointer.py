"""Unit tests for Pointer class

pytest -s -vv ./utils/json_content/test_pointer.py
"""
import pytest

from .pointer import Pointer


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
        """Valid JSON pointer string successfully matches"""
        assert Pointer.match(ptr)

    @pytest.mark.parametrize("ptr, expected_path", VALID_POINTERS)
    def test_parse_from_string(self, ptr, expected_path):
        """Parsing of valid pointers as strings"""
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
        """Parsing of valid pointers as path tuple"""
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
        """Detect child is successful for valid """
        ptr1 = Pointer.from_string(ptr_under_test)
        ptr2 = Pointer.from_string(ptr_parent)
        assert ptr1.is_child_of(ptr2)

    @pytest.mark.parametrize("ptr_parent, ptr_child", [
        ('/a/b', '/a/b/c'),
        ('', '/a'),
        ('/0', '/0/1'),
    ])
    def test_is_parent_of(self, ptr_parent, ptr_child):
        """Parent detection is successful for valid pointer"""
        ptr1 = Pointer.from_string(ptr_parent)
        ptr2 = Pointer.from_string(ptr_child)
        assert ptr1.is_parent_of(ptr2)

    @pytest.mark.parametrize("ptr_under_test, ptr_parent", [
        ('/a/b', '/a/b/c'),
        ('/0', '/0/1'),
        ('', '/a'),
        ('/a', '/a'),
        ('', '')
    ])
    def test_is_not_child_of(self, ptr_under_test, ptr_parent):
        """Not child pointers detection is correct"""
        ptr1 = Pointer.from_string(ptr_under_test)
        ptr2 = Pointer.from_string(ptr_parent)
        assert not ptr1.is_child_of(ptr2)

    @pytest.mark.parametrize("ptr_parent, ptr_to_test_against", [
        ('/a/b', '/d/c'),
        ('/0/1', '/0'),
        ('/a', ''),
        ('/a', '/a'),
        ('', '')
    ])
    def test_is_not_parent_of(self, ptr_parent, ptr_to_test_against):
        """Not parent pointers detection is correct"""
        ptr1 = Pointer.from_string(ptr_parent)
        ptr2 = Pointer.from_string(ptr_to_test_against)
        assert not ptr1.is_parent_of(ptr2)

    @pytest.mark.parametrize("ptr_under_test, ptr_parent", [
        ('/a/b/c', '/a/b'),
        ('/0/1', '/0'),
        ('/a', ''),
    ])
    def test_get_parent(self, ptr_under_test, ptr_parent):
        """Return parent of pointer"""
        ptr1 = Pointer.from_string(ptr_under_test)
        ptr2 = Pointer.from_string(ptr_parent)
        ptr1_parent = ptr1.parent()

        assert ptr1_parent == ptr2
        assert ptr1_parent.path == ptr2.path

    def test_get_parent_when_no_parent_return_self(self):
        """Return self if parent is not exists (root node)"""
        ptr1 = Pointer.from_string('')
        ptr1_parent = ptr1.parent()
        assert ptr1_parent == ptr1
        assert ptr1_parent.path == ptr1.path

    @pytest.mark.parametrize("child_ptr, expected_ptr", [
        ("/b", "/root/b"),
        ("/b/c", "/root/b/c"),
        ("b", "/root/b"),
        ("b/c", "/root/b/c"),
        (0, "/root/0"),
        (-1, "/root/-1"),
        (("b", ), "/root/b"),
        (("b", "c"), "/root/b/c"),
        ((0, ), "/root/0"),
        ((0, 1), "/root/0/1"),
        (("",""), "/root//")
    ])
    def test_get_child(self, child_ptr, expected_ptr):
        """Return child from pointer"""
        ptr = Pointer.from_string('/root').child(child_ptr)
        ptr_expected = Pointer.from_string(expected_ptr)
        assert ptr == ptr_expected

    @pytest.mark.parametrize('child_ptr, expected_ptr', [
        ("", '/'),
        ('b', '/b'),
        ('/b', '/b'),
        (0, '/0'),
        (('a',), '/a'),
        ((0, 1), '/0/1')
    ])
    def test_get_child_from_root(self, child_ptr, expected_ptr):
        """Return child from root node"""
        ptr = Pointer.from_string('').child(child_ptr)
        ptr_expected = Pointer.from_string(expected_ptr)
        assert ptr == ptr_expected

    @pytest.mark.parametrize("child_ptr", [
        None,
        (None,),
        4.55,
        [],
        tuple()
    ])
    def test_get_child_with_invalid_subpointer_fails(self, child_ptr):
        """Error handling on invalid pointer"""
        with pytest.raises(ValueError, match='Child sub-path must be non empty.*'):
            Pointer.from_string('/root').child(child_ptr)

    def test_equals(self):
        """Same pointers equals"""
        raw_ptr = "/a/b/c"
        ptr1 = Pointer.from_string(raw_ptr)
        ptr2 = Pointer.from_string(raw_ptr)
        assert ptr1 == ptr2

    def test_not_equals(self):
        """Different pointers not equals"""
        ptr1 = Pointer.from_string("/a/b/c")
        ptr2 = Pointer.from_string("/a/b")
        assert ptr1 != ptr2

    @pytest.mark.parametrize("ptr", INVALID_POINTERS)
    def test_not_match(self, ptr):
        """Invalid pointers doesn't match expected format"""
        assert not Pointer.match(ptr)

    @pytest.mark.parametrize("ptr", INVALID_POINTERS)
    def test_parse_invalid_fails(self, ptr):
        """Error handling on parsing pointers of invalid pointer"""
        with pytest.raises(ValueError, match='Invalid JSON Pointer syntax .*'):
            Pointer.from_string(ptr)
