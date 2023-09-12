"""Handler for logging request/response data to database for history purposes"""

import sqlite3
from logging import Handler, LogRecord
from utils.api_client.basic_api_client import RequestLogEventType


def initialize_database(db_filename):
    """Helper function to prepare database. This should be called once to create empty
    database of specific structure if one going to use DatabaseHandler"""
    # Check for existance of tables in DB
    with sqlite3.connect(db_filename) as conn:
        cursor = conn.cursor()

        # Check for DB existence - do nothing if exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if cursor.fetchone():
            return

        # If no tables - create new
        # Session info
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions
            (session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            api TEXT,
            api_url TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT
        )""")

        # Log records
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests
            (record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INT NOT NULL,
            request_id INT NOT NULL,
            status TEXT NOT NULL,
            method TEXT NOT NULL,
            url TEXT NOT NULL,
            start_at TEXT NOT NULL,
            end_at TEXT,
            request_params BLOB,
            request BLOB,
            response BLOB,
            error_info BLOB,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )""")

        conn.commit()

class DatabaseHandler(Handler):
    """Logging Handler that saves log messages to database"""
    def __init__(self, db_filename: str) -> None:
        if not db_filename:
            raise ValueError('Database file is not defined!')

        self.db_name = db_filename
        self.db_conn = sqlite3.connect(self.db_name)
        self.cursor = self.db_conn.cursor()
        self.active_sessions = {}

        Handler.__init__(self)

    def close(self) -> None:
        if self.db_conn is None:
            return
        self.acquire()
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

        if record.event_type == RequestLogEventType.PREPARED.value:
            self.log_request_preparation(record)
        elif record.event_type  == RequestLogEventType.SUCCESS.value:
            self.log_request_result(record, RequestLogEventType.SUCCESS.name)
        elif record.event_type == RequestLogEventType.ERROR.value:
            self.log_request_result(record, RequestLogEventType.ERROR.name)

    def log_request_preparation(self, record: LogRecord) -> None:
        """Saves request preparation data to database as new entity
        in 'requests' table.
        Also registers client session if not yet done.

        Args:
            record (LogRecord): record from logger.
        """
        session_id = self._get_session_for_client(record.client_id)

        # Add request info with session_id
        self._add_record(
            session_id=session_id,
            request_id=record.request_id,
            method=record.request_params['method'],
            url=record.request_params['url'],
            request_params=str(record.request_params)
        )

    def log_request_result(self, record: LogRecord, new_status: str) -> None:
        """Updates request record logged in DB with request's result - error or
        response data.

        Args:
            record (LogRecord): record from logger.
            new_status (str): status of the request.
        """
        session_id = self._get_session_for_client(record.client_id)

        self._update_record(
            session_id=session_id,
            request_id=record.request_id,
            status=new_status,
            request=record.request,
            response=record.response,
            error_info=str(record.exc_text) if record.exc_text else None
        )

    def _get_session_for_client(self, client_id: dict) -> int:
        """Returns session_id for client.
        If session is not yet started - adds session to DB.
        Otherwise - update session's end_at param.

        Args:
            client_id (dict): client's id and api info (name, url).

        Returns:
            int: session id for client.
        """
        instance_id = client_id['id']
        if instance_id in self.active_sessions:
            session_id = self.active_sessions[instance_id]
            self._update_session(session_id)
            return session_id

        session_id = self._add_session(client_id)
        self.active_sessions[instance_id] = session_id
        return session_id

    def _add_session(self, client_id: dict) -> int:
        """Adds session info to DB and return session_id

        Args:
            client_id (dict): client's id and api info (name, url).

        Returns:
            int: session id for client.
        """
        self.cursor.execute("""
            INSERT INTO sessions (client_id, api, api_url, started_at, ended_at)
            VALUES (:id, :api, :url, DateTime('now'), DateTime('now'))""",
            client_id
        )
        self.db_conn.commit()

        self.cursor.execute(
            "SELECT session_id FROM sessions WHERE client_id = ?",
            (client_id['id'], )
        )
        return self.cursor.fetchone()[0]

    def _update_session(self, session_id: int) -> None:
        """Updates 'ended_at' timestamp for given session.

        Args:
            session_id (int): session id for client
        """
        self.cursor.execute("""
            UPDATE sessions
            SET ended_at = DateTime('now')
            WHERE session_id = ?""",
            (session_id, )
        )
        self.db_conn.commit()

    def _add_record(self, session_id, request_id, method, url, request_params):
        """Saves request info by adding new record to table"""
        self.cursor.execute("""
            INSERT INTO requests
            (session_id, request_id, status, method, url, start_at, request_params)
            VALUES (?, ?, ?, ?, ?, DateTime('now'), ?)
            """, (
                session_id, request_id,
                RequestLogEventType.PREPARED.name,
                method, url, request_params
            )
        )
        self.db_conn.commit()

    def _update_record(self, session_id, request_id,
            status, request = None, response = None, error_info = None):
        """Updates request info by session_id + request_id with response or with error_info"""
        self.cursor.execute("""UPDATE requests
            SET status = ?, request = ?, response = ?, error_info = ?, end_at = DateTime('now')
            WHERE session_id = ? AND request_id = ?""",
            (
                status, request, response, error_info,
                session_id, request_id
            )
        )
        self.db_conn.commit()


# initialize_database('logging.db')
