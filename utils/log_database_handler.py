"""Handler for logging request/response data to database for history purposes"""
import os
import sqlite3
import datetime
from pathlib import Path
from logging import Handler, LogRecord

from filelock import FileLock

from utils.api_client.models import ApiRequestLogEventType, ApiClientIdentificator


class DatabaseHandler(Handler):
    """Logging Handler that saves log messages to database.

    In order to correctly write data to DB it is expected to pass request/response
    data as dict in `extra` param of logging function calls (log(), info(), err(), etc.).

    Expected structure of a `utils.api_client.model.ApiLogEntity`.

    On logging errors `event_type` must be RequestLogEventType.ERROR and
    `exc_info` param must be set to `True`.

    E.g.:
    ```
    logger.log(logging.INFO, msg='Request failed', exc_info=True, extra=ApiLogEntity(
        event_type=RequestLogEventType.ERROR,
        request_id=10,
        client_id=self.client_id
    ))
    """

    def __init__(self, db_filename: str, buffer_size: int = 10) -> None:
        if not db_filename:
            raise ValueError('Database file is not defined!')

        self.buffer_size = buffer_size
        self.buffer = []

        self.db_name = db_filename
        self.db_conn = None
        self.cursor = None
        self.active_sessions = {}

        self._connect_to_db()

        Handler.__init__(self)

    def close(self) -> None:
        if self.db_conn is None:
            return
        self.acquire()
        self.write_from_buffer()
        self.cursor.close()
        self.db_conn.close()
        self.release()

    def emit(self, record: LogRecord) -> None:
        """"Handles log record of specific structure and log request/response data
        into the database.
        Does nothing if log record missing expected fields.

        Args:
            record (LogRecord): log record to handle.
        """
        if 'event_type' not in record.__dict__:
            return

        self.buffer.append(record)
        if len(self.buffer) == self.buffer_size:
            self.write_from_buffer()

    def write_from_buffer(self):
        """Actually write to database and clears buffer"""
        for record in self.buffer:
            if record.event_type == ApiRequestLogEventType.PREPARED:
                self.log_request_preparation(record)
            elif record.event_type  == ApiRequestLogEventType.SUCCESS:
                self.log_request_result(record, ApiRequestLogEventType.SUCCESS.name)
            elif record.event_type == ApiRequestLogEventType.ERROR:
                self.log_request_result(record, ApiRequestLogEventType.ERROR.name)

        self.db_conn.commit()
        self.buffer.clear()

    def log_request_preparation(self, record: LogRecord) -> None:
        """Saves request preparation data to database as new entity
        in 'requests' table.
        Also registers client session if not yet done.

        Args:
            record (LogRecord): record from logger.
        """
        session_id = self._get_session_for_client(record.client_id, record.created)

        # Add request info with session_id
        self._add_record(
            session_id=session_id,
            request_id=record.request_id,
            method=record.request_params['method'],
            url=record.request_params['url'],
            request_params=str(record.request_params),
            timestamp=record.created
        )

    def log_request_result(self, record: LogRecord, new_status: str) -> None:
        """Updates request record logged in DB with request's result - error or
        response data.

        Args:
            record (LogRecord): record from logger.
            new_status (str): status of the request.
        """
        session_id = self._get_session_for_client(record.client_id, record.created)
        error_info= None
        if record.exc_info:
            error_info = record.exc_text \
                    if record.exc_text else \
                    self.formatter.formatException(record.exc_info)

        self._update_record(
            session_id=session_id,
            request_id=record.request_id,
            status=new_status,
            request=record.request,
            response=record.response,
            error_info=error_info,
            timestamp=record.created
        )

    def _get_session_for_client(self, client_id: ApiClientIdentificator,
                                timestamp: float) -> int:
        """Returns session_id for client.
        If session is not yet started - adds session to DB.
        Otherwise - update session's end_at param.

        Args:
            client_id (dict): client's id and api info (name, url).

        Returns:
            int: session id for client.
        """
        instance_id = client_id.instance_id
        if instance_id in self.active_sessions:
            session_id = self.active_sessions[instance_id]
            self._update_session(session_id, timestamp)
            return session_id

        session_id = self._add_session(client_id, timestamp)
        self.active_sessions[instance_id] = session_id
        return session_id

    def _add_session(self, client_id: ApiClientIdentificator, timestamp: float) -> int:
        """Adds session info to DB and return session_id

        Args:
            client_id (dict): client's id and api info (name, url).

        Returns:
            int: session id for client.
        """
        self.cursor.execute("""
            INSERT INTO sessions (client_id, api, api_url, started_at, ended_at)
            VALUES (:id, :api, :url, :timestamp, :timestamp)""",
            {
                'id': client_id.instance_id,
                'api': client_id.api_name,
                'url': client_id.url,
                'timestamp': self._to_utc_time(timestamp)
            }
        )
        self.db_conn.commit()

        self.cursor.execute(
            "SELECT session_id FROM sessions WHERE client_id = ?",
            (client_id.instance_id, )
        )
        return self.cursor.fetchone()[0]

    def _update_session(self, session_id: int, timestamp: float) -> None:
        """Updates 'ended_at' timestamp for given session.

        Args:
            session_id (int): session id for client
        """
        self.cursor.execute("""
            UPDATE sessions
            SET ended_at = ?
            WHERE session_id = ?""",
            (self._to_utc_time(timestamp), session_id)
        )
        #self.db_conn.commit()

    def _add_record(self, session_id: int, request_id: int, method: str, url: str,
                    request_params: str, timestamp: float) -> None:
        """Saves request info by adding new record to table"""
        self.cursor.execute("""
            INSERT INTO requests
            (session_id, request_id, status, method, url, request_params, started_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, request_id,
                ApiRequestLogEventType.PREPARED.name,
                method, url, request_params, self._to_utc_time(timestamp)
            )
        )
        #self.db_conn.commit()

    def _update_record(self, session_id: int, request_id: int, status: str, timestamp: float,
            request: str = None, response: str = None, error_info: str = None) -> None:
        """Updates request info by session_id + request_id with response or with error_info"""
        self.cursor.execute("""UPDATE requests
            SET status = ?, request = ?, response = ?, error_info = ?, ended_at = ?
            WHERE session_id = ? AND request_id = ?""",
            (
                status, request, response, error_info, self._to_utc_time(timestamp),
                session_id, request_id
            )
        )
        #self.db_conn.commit()

    def _connect_to_db(self):
        """Initialize new connection to DB if exists. If not exists - create new DB file and
        initialize it with needed tables.

        For parallel run use file lock to initialize only 1 instance of DB.
        """
        db_file = Path(self.db_name)
        if db_file.exists():
            self._connect()
            return

        worker_id = os.getenv('PYTEST_XDIST_WORKER')
        if worker_id is None or worker_id == 'master':
            # If one worker - just create
            self._initialize_db()
            return

        lock_file = str(db_file) + '.lock'
        with FileLock(lock_file):
            # If not yet created - create and initialize db
            # otherwise initialize new connection
            if not db_file.is_file():
                self._initialize_db()
            else:
                self._connect()

    def _connect(self):
        """Creates new connection and cursort for DB"""
        self.db_conn = sqlite3.connect(self.db_name, timeout=30)
        self.cursor = self.db_conn.cursor()

    def _initialize_db(self):
        """Creates needed tables: `sessions` and `requests` in database"""
        self._connect()

        # Session info
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions
            (session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            api TEXT,
            api_url TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT
        )""")

        # Log records
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests
            (record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            request_id INT NOT NULL,
            status TEXT NOT NULL,
            method TEXT NOT NULL,
            url TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            request_params BLOB,
            request BLOB,
            response BLOB,
            error_info BLOB,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )""")

        self.db_conn.commit()

    def _to_utc_time(self, timestamp):
        """Converts timestamp to ISO formatted UTC time"""
        return datetime.datetime.fromtimestamp(timestamp) \
            .astimezone(datetime.timezone.utc) \
            .isoformat()
