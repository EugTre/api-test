"""Unit tests for Pointer class

pytest -s -vv ./utils/json_content/test_pointer.py
"""
import pytest

from utils.json_content.pointer import Pointer, PointerType

class TestPointer:
    """Points tests"""
    @pytest.mark.parametrize("ptr", (
        '/a/b/c',
        r'!ref /a/b/c',
        r'!file path/to/file'
    ))
    def test_pointer_check_is_any_pointer(self, ptr):
        """Tests that match_any_pointer() method returns True for valid pointer"""
        assert Pointer.match_any_pointer(ptr), \
            f'Pointer "{ptr}" doesn\'t match any pointer type'

    @pytest.mark.parametrize("ptr", (
        r'!ref /a/b/c',
        r'!ref /',
        r'!ref /0/1'
    ))
    def test_pointer_check_is_ref_pointer(self, ptr):
        """Tests that match_ref_pointer() method returns True for valid !ref pointer"""
        assert Pointer.match_ref_pointer(ptr), \
            f'Pointer "{ptr}" doesn\'t match reference pointer type'

    @pytest.mark.parametrize("ptr", (
        r'!file path/to/file',
        r'!file foo.json'
    ))
    def test_pointer_check_is_file_pointer(self, ptr):
        """Tests that match_file_ref_pointer() method returns True for valid !file pointer"""
        assert Pointer.match_file_ref_pointer(ptr), \
            f'Pointer "{ptr}" doesn\'t match file reference pointer type'

    @pytest.mark.parametrize("ptr, expected_type, expected_path", [
        (r"/foo", PointerType.POINTER, ('foo',)),
        ("", PointerType.POINTER, None),
        (r"/", PointerType.POINTER, ('',)),

        (r"/foo/bar/a", PointerType.POINTER, ('foo', 'bar', 'a')),
        (r"/foo//bar", PointerType.POINTER, ('foo', '', 'bar')),
        (r"/foo~1bar~0/baz", PointerType.POINTER, ('foo/bar~', 'baz')),
        (r"/  /  a", PointerType.POINTER, ('  ', '  a')),

        (r"!ref /foo", PointerType.REFERENCE, ('foo', )),
        (r"!ref /foo/bar", PointerType.REFERENCE, ('foo', 'bar')),
        (r"!ref /", PointerType.REFERENCE, ('', )),
        (r"!ref    /foo   /bar   /a  ", PointerType.REFERENCE, ('foo   ', 'bar   ', 'a  ')),
        (r"!ref /foo//bar", PointerType.REFERENCE, ('foo', '', 'bar')),
        (r"!ref /foo~1bar~0/baz", PointerType.REFERENCE, ('foo/bar~', 'baz')),
        (r"!ref /  /  a", PointerType.REFERENCE, ('  ', '  a')),

        (r"!file content/file.json", PointerType.FILE_REF, 'content/file.json'),
        (r"!file    content  /  file.json", PointerType.FILE_REF, 'content  /  file.json')
    ])
    def test_pointer_json_pointer_parsing(self, ptr, expected_type, expected_path):
        """Basic pointers test"""
        assert Pointer.match_any_pointer(ptr), \
            'Pointer syntax doesn\'t match to basic pointer syntax!'

        pointer = Pointer.from_string(ptr)

        assert pointer.raw == ptr, f'Pointer raw: E="{ptr}" vs A="{pointer.raw}"'
        assert pointer.type == expected_type, \
            f'Pointer type: E="{expected_type}" vs A="{pointer.type}"'
        assert pointer.pointer == expected_path, \
            f'Pointer path: E="{expected_path}" vs A="{pointer.pointer}"'

        match expected_type:
            case PointerType.POINTER:
                assert pointer.is_pointer
            case PointerType.REFERENCE:
                assert pointer.is_reference
            case PointerType.FILE_REF:
                assert pointer.is_file

    @pytest.mark.parametrize("ptr, rfc_pointer", [
        (r"/foo",                   r"/foo"),
        ("",                        ""),
        (r"/",                      r"/"),

        (r"/foo/bar/a",             r"/foo/bar/a"),
        (r"/foo//bar",              r"/foo//bar"),
        (r"/foo~1bar~0/baz",        r"/foo~1bar~0/baz"),
        (r"/  /  a",                r"/  /  a"),

        (r"!ref /foo",              r"/foo"),
        (r"!ref /foo/bar",          r"/foo/bar"),
        (r"!ref /",                 r"/"),
        (r"!ref    /foo   /bar   /a  ",
                                    r"/foo   /bar   /a  "),
        (r"!ref /foo//bar",         r"/foo//bar"),
        (r"!ref /foo~1bar~0/baz",   r"/foo~1bar~0/baz"),
        (r"!ref /  /  a",           r"/  /  a"),

        (r"!file content/file.json",        r""),
        (r"!file    content  /  file.json", r"")
    ])
    def test_pointer_json_pointer_get_rfc_pointer_method(self, ptr: str, rfc_pointer: str):
        """.get_rfc_pointer() method returns pointer in valid RFC6901 format"""
        pointer: Pointer = Pointer.from_string(ptr)
        assert pointer.get_rfc_pointer() == rfc_pointer

    @pytest.mark.parametrize("ptr", (
            r'a/b/c',
            'a b c',
            'ref a b c',
            'file a b c',
            r'!!file path/to/file',
            '!file',
            '!ref',
            r'!ref/a/b/c'
        ))
    def test_pointer_check_is_any_pointer_invalid_ptr_should_fail(self, ptr):
        """Tests that check_any_pointer() method returns false for pointers
        of invalid syntax"""
        assert not Pointer.match_any_pointer(ptr), \
            f'Pointer "{ptr}" matches any pointer type, but not expected to be'

    @pytest.mark.parametrize("ptr", (
            r'/a/b/c',
            '!ref',
            r'!ref/a/b/c'
            '!file path/to/file'
            'ref a/b/c',
            r'file a/b/c',
        ))
    def test_pointer_check_is_ref_pointer_invalid_ptr_should_fail(self, ptr):
        """Tests that match_ref_pointer() method returns false for pointers
        of invalid syntax or format"""
        assert not Pointer.match_ref_pointer(ptr), \
            f'Pointer "{ptr}" matches reference pointer type, but not expected to be'

    @pytest.mark.parametrize("ptr", (
            'file',
            '!file',
            r'/a/b/c',
            r'!ref /a/b/c'
            'file foo/bar.json',
        ))
    def test_pointer_check_is_file_pointer_invalid_ptr_should_fail(self, ptr):
        """Tests that match_file_ref_pointer() method returns false for pointers
        of invalid syntax or format"""
        assert not Pointer.match_file_ref_pointer(ptr), \
            f'Pointer "{ptr}" matches file pointer type, but not expected to be'

    @pytest.mark.parametrize("ptr, exception_msg_pattern", (
        (None, r'Null pointer was given. .*'),
        (r'a/b/c', r'Pointer ".*" should start from root "/" element.'),
        ('!ref ', r'Reference to the whole document is prohibited.'),
        ('!ref', r'Invalid pointer syntax.*'),
        (r'!ref a/b/c', r'Pointer ".*" should start from root "/" element.'),
        ('!file ', r'Pointer ".*" has invalid/empty path!'),
        ('!file', r'Invalid pointer syntax of pointer.*'),
    ))
    def test_pointer_invalid_should_fail(self, ptr, exception_msg_pattern):
        """Test exceptions on invalid pointer"""
        with pytest.raises(ValueError, match=exception_msg_pattern):
            Pointer.from_string(ptr)
