"""Tests for DatabseHandler class"""
import sqlite3
import logging
import uuid
import datetime
import time
from dataclasses import dataclass

import pytest

from utils.api_client.models import ApiRequestLogEventType, ApiClientIdentificator, ApiLogEntity
from utils.matchers import matcher as match
from .log_database_handler import DatabaseHandler

# --- Models of DB entities
@dataclass
class TimedDBRecord:
    """Base class for DB record with time fields"""
    def __post_init__(self):
        # DB stores without UTC marker, so adding Z suffix for all time attrs
        for time_attr in ['started_at', 'ended_at']:
            val = getattr(self, time_attr)
            if val is not None and isinstance(val, str):
                setattr(self, time_attr, f'{val}Z')

@dataclass
class SessionDBRecord():
    """Model of DB record for `sessions` table"""
    session_id: int
    client_id: str
    api: str
    api_url: str
    started_at: str
    ended_at: str

@dataclass
class RequestDBRecord():
    """Model of DB record for `requests` table"""
    record_id: int
    session_id: int
    request_id: int
    status: str
    method: str
    url: str
    started_at: str
    ended_at: str|None
    request_params: str
    request: str|None = None
    response: str|None = None
    error_info: str|None = None


# --- Helper functions ---
def get_db_logger(db_file, buffer_size=1):
    """Returns configured logger object"""
    db_handler = DatabaseHandler(db_file, buffer_size)
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
def get_client_id() -> ApiClientIdentificator:
    """Returns configured ApiClientIdentificator"""
    return ApiClientIdentificator(
        instance_id=f"MyClientId-{uuid.uuid4()}",
        api_name="Test API",
        url="localhost:9092/v1"
    )

@pytest.fixture(name='request_params', scope='session')
def get_request_params():
    """Returns some pre-configured request params
    with `method` and `url` fields"""
    return {
        'method': 'GET',
        'url': 'localhost:9092/v1/stuff'
    }

# --- Constants ---
SELECT_ALL_FROM_SESSIONS = "SELECT * FROM sessions"
SELECT_ALL_FROM_REQUESTS = "SELECT * FROM requests"


# --- Tests ---
def test_log_database_handler_initialization(db_file):
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

class TestLogDatabaseHandlerSession:
    """Tests session creation and update"""
    def test_create_session(self, client_id: ApiClientIdentificator,
                            request_params, db_file, caplog):
        """Test session creation on first log emission by db handler"""

        # Sets pytest's logging capturing to DEBUG -
        # otherwise pytest will supress any log emission until test fails
        caplog.set_level(logging.DEBUG)
        expected_record = SessionDBRecord(
            session_id=1,
            client_id=client_id.instance_id,
            api=client_id.api_name,
            api_url=client_id.url,
            started_at=match.AnyDateInRange('-1s', '+1s'),
            ended_at=match.AnyDateInRange('-1s', '+1s')
        )

        logger = get_db_logger(db_file)
        logger.log(logging.INFO, msg="Stuff", extra=ApiLogEntity(
            event_type=ApiRequestLogEventType.PREPARED,
            client_id=client_id,
            request_id=0,
            request_params=request_params
        ))

        with sqlite3.connect(db_file) as conn:
            records = conn.cursor().execute(SELECT_ALL_FROM_SESSIONS).fetchall()

        assert len(records) == 1
        assert (record := SessionDBRecord(*records[0]))
        assert record == expected_record

    def test_update_session(self, client_id: ApiClientIdentificator,
                            request_params, db_file, caplog):
        """Test session update on multiple log emission for same client id"""
        caplog.set_level(logging.DEBUG)
        expected_record = SessionDBRecord(
            session_id=1,
            client_id=client_id.instance_id,
            api=client_id.api_name,
            api_url=client_id.url,
            started_at=match.AnyDateInRange('-2s', '+0s'),
            ended_at=match.AnyDateInRange('-1s', '+1s')
        )

        logger = get_db_logger(db_file)
        logger.info(msg='', extra={
            'event_type': ApiRequestLogEventType.PREPARED,
            'request_id': 0,
            'request_params': request_params,
            'client_id': client_id
        })
        time.sleep(0.5)

        logger.info(msg='', extra=ApiLogEntity(
            event_type=ApiRequestLogEventType.SUCCESS,
            request_id=0,
            client_id=client_id,
            request='',
            response='',
        ))

        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            records = cursor.execute(SELECT_ALL_FROM_SESSIONS).fetchall()

        assert len(records) == 1
        assert (record := SessionDBRecord(*records[0]))
        assert record == expected_record

class TestLogDatabaseHandlerLogging:
    """Tests actual logging to DB"""
    def test_log_prepare_request(self, client_id: ApiClientIdentificator,
                                 request_params, db_file, caplog):
        """Tests creation of new PREPARE record at `requests` table"""
        caplog.set_level(logging.DEBUG)

        log_data = ApiLogEntity(
            event_type=ApiRequestLogEventType.PREPARED,
            request_id=0,
            client_id=client_id,
            request_params=request_params
        )
        expected_record = RequestDBRecord(
            record_id=1,
            session_id=1,
            request_id=log_data.request_id,
            status=log_data.event_type.name,
            method=log_data.request_params['method'],
            url=log_data.request_params['url'],
            started_at=match.AnyDateInRange('-2s', 'now'),
            ended_at=None,
            request_params=str(request_params)
        )

        logger = get_db_logger(db_file)
        logger.info(msg='', extra=log_data)

        with sqlite3.connect(db_file) as conn:
            records = conn.cursor().execute(SELECT_ALL_FROM_REQUESTS).fetchall()

        assert len(records) == 1
        assert (record := RequestDBRecord(*records[0]))
        assert record == expected_record

    def test_log_request_success(self, client_id, request_params, db_file, caplog):
        """Tests update of existing PREPARE record at `requests` table with response data"""
        caplog.set_level(logging.DEBUG)

        log_data_prepare = ApiLogEntity(
            event_type=ApiRequestLogEventType.PREPARED,
            request_id=0,
            request_params=request_params,
            client_id=client_id
        )
        log_data_update = ApiLogEntity(
            event_type=ApiRequestLogEventType.SUCCESS,
            request_id=log_data_prepare.request_id,
            request='some request data',
            response='some response data',
            client_id=client_id
        )
        expected_record = RequestDBRecord(
            record_id=1,
            session_id=1,
            request_id=log_data_prepare.request_id,
            status=log_data_update.event_type.name,
            method=log_data_prepare.request_params['method'],
            url=log_data_prepare.request_params['url'],
            started_at=match.AnyDateInRange('-2s', 'now'),
            ended_at=match.AnyDateInRange('-2s', 'now'),
            request_params=str(request_params),
            request=log_data_update['request'],
            response=log_data_update['response']
        )

        logger = get_db_logger(db_file)
        logger.info(msg='', extra=log_data_prepare)

        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            records = cursor.execute(SELECT_ALL_FROM_REQUESTS).fetchall()
            assert len(records) == 1

            logger.info(msg='', extra=log_data_update)
            records_updated = cursor.execute(SELECT_ALL_FROM_REQUESTS).fetchall()

        assert len(records_updated) == 1
        assert (record := RequestDBRecord(*records_updated[0]))
        assert record == expected_record
        assert (datetime.datetime.fromisoformat(record.started_at)
                <=
                datetime.datetime.fromisoformat(record.ended_at))

    def test_log_error_on_request(self, client_id, request_params, db_file, caplog):
        """Tests update of existing PREPARE record at `requests` table with error"""
        caplog.set_level(logging.DEBUG)

        log_data_prepare = ApiLogEntity(
            event_type=ApiRequestLogEventType.PREPARED,
            request_id=0,
            request_params=request_params,
            client_id=client_id
        )
        log_data_update = ApiLogEntity(
            event_type=ApiRequestLogEventType.ERROR,
            request_id=0,
            request=None,
            response=None,
            client_id=client_id
        )
        expected_record = RequestDBRecord(
            record_id=1,
            session_id=1,
            request_id=log_data_prepare.request_id,
            status=log_data_update.event_type.name,
            method=log_data_prepare.request_params['method'],
            url=log_data_prepare.request_params['url'],
            started_at=match.AnyDateInRange('-2s', 'now'),
            ended_at=match.AnyDateInRange('-2s', 'now'),
            request_params=str(request_params),
            request=log_data_update['request'],
            response=log_data_update['response'],
            error_info=match.AnyTextWith('ValueError')
        )

        logger = get_db_logger(db_file)
        logger.info(msg='', extra=log_data_prepare)

        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            records = cursor.execute(SELECT_ALL_FROM_REQUESTS).fetchall()
            assert len(records) == 1

            try:
                raise ValueError("Faked exception")
            except ValueError:
                logger.error(msg='', extra=log_data_update, exc_info=True)
            records_updated = cursor.execute(SELECT_ALL_FROM_REQUESTS).fetchall()

        assert len(records_updated) == 1
        assert (record := RequestDBRecord(*records_updated[0]))
        assert record == expected_record
        assert (datetime.datetime.fromisoformat(record.started_at)
                <=
                datetime.datetime.fromisoformat(record.ended_at))

    @pytest.mark.parametrize("buffer_size",(3, 10))
    def test_log_buffered(self, client_id: ApiClientIdentificator,
                                 request_params, db_file, caplog, buffer_size):
        """Tests creation of new PREPARE record at `requests` table"""
        caplog.set_level(logging.DEBUG)

        logger = get_db_logger(db_file, buffer_size)
        with sqlite3.connect(db_file) as conn:
            db_cur = conn.cursor()

            # Log few messaged, but don't reach the limit
            for i in range(buffer_size - 1):
                log_data = ApiLogEntity(
                    event_type=ApiRequestLogEventType.PREPARED,
                    request_id=i,
                    client_id=client_id,
                    request_params=request_params
                )
                logger.info(msg=f'Logging request {i}', extra=log_data)

            # Logged below buffer limit - no record in db expected
            records = db_cur.execute(SELECT_ALL_FROM_REQUESTS).fetchall()
            assert len(records) == 0

            # Log another item to overfill buffer
            log_data = ApiLogEntity(
                event_type=ApiRequestLogEventType.PREPARED,
                request_id=99,
                client_id=client_id,
                request_params=request_params
            )
            logger.info(msg=f'Logging LAST request', extra=log_data)

            # Check that buffer dumped to db
            records = db_cur.execute(SELECT_ALL_FROM_REQUESTS).fetchall()
            assert len(records) == buffer_size
