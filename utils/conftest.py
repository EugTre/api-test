"""Conftest for unit tests of framework"""

import shutil
import uuid
import pathlib
import json

import pytest

class AppendableFilePath(type(pathlib.Path())):
    """Extension to Path class"""
    def append_text(self, text):
        """Append to file"""
        with self.open('a', encoding='utf-8') as file:
            file.write(text)

    def write_as_json(self, value):
        """Overwrite file, converting given data to JSON"""
        self.write_text(json.dumps(value), encoding='utf-8')

    def append_as_json(self, value):
        """Append to file, converting given data to JSON"""
        self.append_text(json.dumps(value))


@pytest.fixture(name='tmp_folder', scope='session')
def handle_tmp_path(tmp_path_factory):
    """Creates temporary directory and deletes on session end"""
    tmpdir = tmp_path_factory.mktemp('files', numbered=False)
    yield tmpdir
    shutil.rmtree(tmpdir)

@pytest.fixture(name='json_file')
def get_json_file(tmp_folder):
    """Provides unqiue path to JSON file"""
    return AppendableFilePath(tmp_folder / f'{uuid.uuid4()}.json')

@pytest.fixture(name='get_file')
def get_unique_file(tmp_folder):
    """Return unique file path generator"""
    def callback(prefix: str = "", ext: str = "json"):
        return AppendableFilePath(tmp_folder / f'{prefix}_{uuid.uuid4()}.{ext}')
    return callback


@pytest.fixture(name='ini_file')
def get_ini_file(tmp_folder):
    """Provides unqiue path to INI file"""
    return AppendableFilePath(tmp_folder / f'{uuid.uuid4()}.ini')
