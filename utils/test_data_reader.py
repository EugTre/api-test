"""Tests for DataReader class

pytest -s -vv ./utils/test_data_reader.py
"""
import pytest
from utils.data_reader import DataReader

@pytest.fixture(name='txt_file')
def get_txt_file(get_file):
    return get_file(ext='txt')


class TestDataReader:
    # --- Positive tests
    def test_read_file(self, txt_file):
        content = 'Some text file'
        txt_file.write_text(content)

        result = DataReader.read_from_file(txt_file)
        assert result == content

    def test_read_json_file(self, get_file):
        file = get_file(ext='json')
        content = '[1,2,3]'
        file.write_text(content)

        result = DataReader.read_from_file(file)
        assert result == [1,2,3]

    def test_read_file_explicit_extension(self, txt_file):
        content = '[1,2,3]'
        txt_file.write_text(content)

        result = DataReader.read_from_file(txt_file, 'json')
        assert result == [1,2,3]

    @pytest.mark.parametrize("content, expected", [
        ('234', 234),
        ('-234', -234),
        ('12.54', 12.54),
        ('-12.54', -12.54),
        ('Text to parse', 'Text to parse'),
        ('Text\nto join\nin line', 'Text to join in line'),
        ('True', True),
        ('true', True),
        ('False', False),
        ('false', False)
    ])
    def test_read_file_as_int(self, txt_file, content, expected):
        txt_file.write_text(content)
        assert DataReader.read_from_file(txt_file) == expected

    # --- Negative tests
    def test_read_non_existent_file_fails(self):
        with pytest.raises(FileNotFoundError, match='d'):
            DataReader.read_from_file('some-non-existent.json')
