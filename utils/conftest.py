"""Conftest for unit tests of framework"""

import shutil
import uuid
import pathlib
import json
import typing
import http.server
import socketserver
import threading
import pathlib

import pytest
from filelock import FileLock


LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 8000
LOCAL_SERVER_URL = f"http://{LOCAL_HOST}:{LOCAL_PORT}"


def start_server(server):
    """Starts server. Should be executed in separate thread."""
    with server:
        server.serve_forever()

@pytest.fixture(name='localhost_server', scope='session')
def handle_local_server():
    """Creates server in separate thread and stop it afterwards
    In case of xdist launch this fixture fails
    Tests that using it must be marked as @pytest.mark.xdist_group("localhost_server")
    """
    server = socketserver.TCPServer(
        (LOCAL_HOST, LOCAL_PORT),
        http.server.BaseHTTPRequestHandler
    )
    srv_thread = threading.Thread(target=start_server, args=(server, ))
    yield srv_thread.start()

    server.shutdown()
    srv_thread.join()


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
def get_json_file(tmp_folder) -> AppendableFilePath:
    """Provides unqiue path to JSON file, content of which may be written/appended"""
    return AppendableFilePath(tmp_folder / f'{uuid.uuid4()}.json')

@pytest.fixture(name='get_file')
def get_unique_file(tmp_folder) -> typing.Callable:
    """Return unique file path generator"""
    def callback(prefix: str = "", ext: str = "json"):
        return AppendableFilePath(tmp_folder / f'{prefix}_{uuid.uuid4()}.{ext}')
    return callback

@pytest.fixture(name='ini_file')
def get_ini_file(tmp_folder) -> AppendableFilePath:
    """Provides unqiue path to INI file"""
    return AppendableFilePath(tmp_folder / f'{uuid.uuid4()}.ini')
