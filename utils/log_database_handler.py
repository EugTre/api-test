import sqlite3
import logging
import logging.handlers
from logging import Handler, LogRecord
from datetime import datetime

class DatabaseHandler(Handler):
    """Logging Handler that saves log messages to database"""
    def __init__(self, db_filename: str) -> None:
        if not db_filename:
            raise ValueError('Database file is not defined!')

        self.db_name = db_filename

        self.session_id = None
        self.session_api = None
        self.session_desc = None
        self.db_conn = None
        self.cursor = None

        Handler.__init__(self)

    def set_session_parameters(self, api_name: str, api_base_url: str) -> None:
        """Sets parameters for session.
        :api_name (str) - name of the API used.
        :api_base_url (str) - base URL of the API
        """
        self.session_api = api_name
        self.session_desc = api_base_url

    def emit(self, record: LogRecord) -> None:
        """Checks for log record parameters and save record to specific table.
           Log records with defined 'response' field will be saved to `api_calls` table.
           Otherwise - record will be formatted and saved to `log_records` table.
        """
        if 'request' in record.__dict__:
            # API call
            # self._add_api_call_record(record)
            print('[DB.API_CALLS] %s [%s]' % (record.message, record.request))
            # print('[DB.API_CALLS] Response:\n  URL: %s\n  Status code: %s\n  Content: %s\n   Headers: %s' % (
            #     record.response.url,
            #     record.response.status_code,
            #     record.response.content,
            #     record.response.headers
            # ))
        else:
            # Normal log
            try:
                msg = self.format(record)
                # self._add_log_record(msg, record.asctime, record.levelno)
                print('[DB.LOG_RECORDS] %s' % msg)
            except Exception:
                self.handleError(record)

    def close(self) -> None:
        if self.db_conn is None:
            return
        self.acquire()
        self._end_session()
        self.cursor.close()
        self.db_conn.close()
        self.release()

    def _connect(self) -> None:
        self.db_conn = sqlite3.connect(self.db_name)
        self.cursor = self.db_conn.cursor()
        self._initialize()
        self._add_session()

    def _initialize(self) -> None:
        # Check for existance of tables in DB
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if self.cursor.fetchone():
            return

        # If no tables - create new
        # Log Levels
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_levels
            (level_id INTEGER PRIMARY KEY,
             level TEXT NOT NULL
            )""")
        self.cursor.executemany("""
            INSERT INTO log_levels (level_id, level)
            VALUES(?, ?)""",
            (
                (logging.CRITICAL, logging.getLevelName(logging.CRITICAL)),
                (logging.ERROR, logging.getLevelName(logging.ERROR)),
                (logging.WARNING, logging.getLevelName(logging.WARNING)),
                (logging.INFO, logging.getLevelName(logging.INFO)),
                (logging.DEBUG, logging.getLevelName(logging.DEBUG)),
                (logging.NOTSET, logging.getLevelName(logging.NOTSET))
            )
        )

        # Session info
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions
            (session_id INTEGER PRIMARY KEY AUTOINCREMENT,
             started_at TEXT NOT NULL,
             ended_at TEXT,
             level TEXT NOT NULL,
             api TEXT NOT NULL,
             description TEXT,
             FOREIGN KEY (level) REFERENCES log_levels(level_id)
            )""")

        # Log records
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS records
            (record_id INTEGER PRIMARY KEY AUTOINCREMENT,
             session_id TEXT NOT NULL,
             timestamp TEXT NOT NULL,
             level INT NOT NULL,
             message TEXT NOT NULL,
             FOREIGN KEY (session_id) REFERENCES sessions(session_id),
             FOREIGN KEY (level) REFERENCES log_levels(level_id)
            )""")

        self.db_conn.commit()

    def _start_session(self) -> None:
        """Adds session info to DB. Should be called before any log message emitted."""
        if self.session_id is not None:
            return

        started_at = datetime.now().isoformat()

        self.cursor.execute("""
            INSERT INTO sessions (started_at, level, api, description)
            VALUES (?, ?, ?, ?)""", (
                started_at,
                self.level,
                self.session_api,
                self.session_desc
            ))
        self.db_conn.commit()

        self.cursor.execute("SELECT session_id FROM sessions WHERE started_at = ?",
                            (started_at, ))
        self.session_id = self.cursor.fetchone()[0]

    def _end_session(self) -> None:
        """Marks end time of the session"""
        if self.session_id is None:
            return

        self.cursor.execute("""
            UPDATE sessions
            SET ended_at = ?
            WHERE session_id = ?""", (
                datetime.now().isoformat(),
                self.session_id
            ))
        self.db_conn.commit()

    def _add_api_call_record(self, record: LogRecord) -> None:
        """Saves API Call record to DB api_calls table"""
        pass

    def _add_log_record(self, msg: str, timestamp: str, level_no: int) -> None:
        """Saves log record to DB log_records table"""
        self.cursor.execute("""
            INSERT INTO records (session_id, timestamp, level, message)
            VALUES (:session_id, :timestamp, :level, :message)""",
            {
                'session_id': self.session_id,
                'timestamp': timestamp,
                'level': level_no,
                'message': msg,
            })
        self.db_conn.commit()


logging.handlers.DatabaseHandler = DatabaseHandler