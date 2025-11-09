# File: logdb.py
"""
Path: logdb.py
Persistent local logging using SQLite.
Provides simple audit logs for incidents and actions.
"""
import sqlite3
import datetime
from typing import Dict, Any, List, Optional

class LogDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        cur = self._conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            incident_json TEXT NOT NULL
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            incident_id INTEGER,
            action_json TEXT NOT NULL,
            result_json TEXT,
            FOREIGN KEY (incident_id) REFERENCES incidents(id)
        )
        """)
        self._conn.commit()

    def log_incident(self, incident: Dict[str, Any]) -> int:
        ts = datetime.datetime.utcnow().isoformat()
        cur = self._conn.cursor()
        cur.execute("INSERT INTO incidents (ts, incident_json) VALUES (?, ?)", (ts, str(incident)))
        self._conn.commit()
        return cur.lastrowid

    def log_action(self, incident_id: Optional[int], action: Dict[str, Any], result: Optional[Dict[str, Any]] = None) -> int:
        ts = datetime.datetime.utcnow().isoformat()
        cur = self._conn.cursor()
        cur.execute("INSERT INTO actions (ts, incident_id, action_json, result_json) VALUES (?, ?, ?, ?)",
                    (ts, incident_id, str(action), str(result) if result is not None else None))
        self._conn.commit()
        return cur.lastrowid

    def get_recent_incidents(self, limit: int = 20) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT id, ts, incident_json FROM incidents ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_actions_for_incident(self, incident_id: int) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT id, ts, action_json, result_json FROM actions WHERE incident_id = ? ORDER BY id ASC", (incident_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
