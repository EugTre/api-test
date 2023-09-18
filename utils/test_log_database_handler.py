
import sqlite3
import logging
import uuid
import datetime
import time
from dataclasses import dataclass

import pytest

from utils.api_client.models import RequestLogEventType
from utils.matchers import matcher as match
from .log_database_handler import DatabaseHandler

# --- Models of DB entities
@dataclass
class SessionRecord:
    session_id: int
    client_id: str
    api: str
    api_url: str
    started_at: str
    ended_at: str

    def __post_init__(self):
        # DB stores without UTC marker, so adding
        if isinstance(self.started_at, str):
            self.started_at = f'{self.started_at}Z'
        if isinstance(self.ended_at, str):
            self.ended_at = f'{self.ended_at}Z'

# --- Helper functions ---
def get_db_logger(db_file):
    """Returns configured logger object"""
    db_handler = DatabaseHandler(db_file)
    db_handler.setLevel(logging.DEBUG)
    db_handler.setFormatter(logging.Formatter(fmt='%(message)s'))

    logger = logging.getLogger('MyCustomLogger')
    logger.addHandler(db_handler)
    return logger

def convert_from_iso(date):
    """sqlite3 date function return UTC time, so make datetime aware"""
    return datetime.datetime.fromisoformat(date).replace(tzinfo=datetime.timezone.utc)

def get_iso_utc_now():
    """Drop microseconds, as DB doesn't saves them"""
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0
    )

# --- Fixtures ---
# ----------------
@pytest.fixture(name='client_id', scope='session')
def get_client_id():
    return {
        'id': f"MyClientId-{uuid.uuid4()}",
        "api": "Test API",
        "url": "localhost:9092/v1"
    }

@pytest.fixture(name='request_params', scope='session')
def get_request_params():
    return {
        'method': 'GET',
        'url': 'localhist:9092/v1/stuff'
    }

@pytest.fixture(name='db_file')
def get_unique_db_file(tmp_path):
    return tmp_path / f'test_db_{uuid.uuid4()}.db'

# --- Constnats ---
SELECT_ALL_FROM_SESSIONS = "SELECT * FROM sessions"
COUNT_SESSIONS = "SELECT COUNT(*) FROM sessions"

def test_db_initialization(db_file):
    """Tests that DB initialize needed tables"""
    get_db_logger(db_file)

    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_schema
            WHERE  type ='table' AND name NOT LIKE 'sqlite_%';
            """)
        tables = [table[0] for table in cursor.fetchall()]

    assert len(tables) == 2
    assert 'sessions' in tables
    assert 'requests' in tables


def test_create_session(client_id, request_params, db_file, caplog):
    """Test session creation on first log emission by db handler"""

    # Sets pytest's logging capturing to DEBUG -
    # otherwise pytest will supress any log emission until test fails
    caplog.set_level(logging.DEBUG)
    expected_record = SessionRecord(
        session_id=1,
        client_id=client_id['id'],
        api=client_id['api'],
        api_url=client_id['url'],
        started_at=match.AnyDateInRange('-1s', '+1s'),
        ended_at=match.AnyDateInRange('-1s', '+1s')
    )

    logger = get_db_logger(db_file)
    logger.log(logging.INFO, msg="Stuff", extra={
        'event_type': RequestLogEventType.PREPARED,
        'request_id': 0,
        'request_params': request_params,
        'client_id': client_id
    })

    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(COUNT_SESSIONS)
        count = cursor.fetchone()[0]
        cursor.execute(SELECT_ALL_FROM_SESSIONS)
        session_info = cursor.fetchone()

    assert count == 1
    assert (record := SessionRecord(*session_info))
    assert record == expected_record

def test_update_session(client_id, request_params, db_file, caplog):
    """Test session update on multiple log emission for same client id"""
    caplog.set_level(logging.DEBUG)
    expected_record = SessionRecord(
        session_id=1,
        client_id=client_id['id'],
        api=client_id['api'],
        api_url=client_id['url'],
        started_at=match.AnyDateInRange('-2s', '+0s'),
        ended_at=match.AnyDateInRange('-1s', '+1s')
    )

    logger = get_db_logger(db_file)
    logger.info(msg='', extra={
        'event_type': RequestLogEventType.PREPARED,
        'request_id': 0,
        'request_params': request_params,
        'client_id': client_id
    })
    time.sleep(1)

    logger.info(msg='', extra={
        'event_type': RequestLogEventType.SUCCESS,
        'request_id': 0,
        'request': '',
        'response': '',
        'client_id': client_id
    })

    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(COUNT_SESSIONS)
        count = cursor.fetchone()[0]
        cursor.execute(SELECT_ALL_FROM_SESSIONS)
        session_info = cursor.fetchone()

    assert count == 1
    assert (record := SessionRecord(*session_info))
    assert record == expected_record
