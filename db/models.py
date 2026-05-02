import sqlite3
import os


def get_db_path() -> str:
    try:
        import streamlit as st
        return st.secrets.get("database", {}).get("db_path", "life_game.db")
    except Exception:
        return "life_game.db"


def get_connection(db_path: str = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


_DDL = """
CREATE TABLE IF NOT EXISTS users (
    username        TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_login      TEXT
);

CREATE TABLE IF NOT EXISTS characters (
    username            TEXT PRIMARY KEY REFERENCES users(username),
    class               TEXT NOT NULL DEFAULT 'Warrior',
    level               INTEGER NOT NULL DEFAULT 1,
    xp                  REAL NOT NULL DEFAULT 0.0,
    xp_to_next          REAL NOT NULL DEFAULT 195.0,
    hp                  REAL NOT NULL DEFAULT 92.5,
    hp_max              REAL NOT NULL DEFAULT 92.5,
    mp                  REAL NOT NULL DEFAULT 32.0,
    mp_max              REAL NOT NULL DEFAULT 32.0,
    gold                REAL NOT NULL DEFAULT 0.0,
    strength            INTEGER NOT NULL DEFAULT 7,
    constitution        INTEGER NOT NULL DEFAULT 5,
    intelligence        INTEGER NOT NULL DEFAULT 1,
    perception          INTEGER NOT NULL DEFAULT 2,
    streak_bonus        REAL NOT NULL DEFAULT 0.0,
    mage_surge_active   INTEGER NOT NULL DEFAULT 0,
    warrior_stance_date TEXT,
    rogue_crit_pending  INTEGER NOT NULL DEFAULT 0,
    last_cron           TEXT NOT NULL DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS equipment (
    username        TEXT PRIMARY KEY REFERENCES users(username),
    head_slot       TEXT,
    body_slot       TEXT,
    weapon_slot     TEXT,
    shield_slot     TEXT,
    back_slot       TEXT
);

CREATE TABLE IF NOT EXISTS inventory (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL REFERENCES users(username),
    item_key        TEXT NOT NULL,
    acquired_at     TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(username, item_key)
);

CREATE TABLE IF NOT EXISTS habits (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL REFERENCES users(username),
    title           TEXT NOT NULL,
    notes           TEXT DEFAULT '',
    positive        INTEGER NOT NULL DEFAULT 1,
    negative        INTEGER NOT NULL DEFAULT 1,
    difficulty      TEXT NOT NULL DEFAULT 'easy',
    value           REAL NOT NULL DEFAULT 1.0,
    up_count        INTEGER NOT NULL DEFAULT 0,
    down_count      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS dailies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL REFERENCES users(username),
    title           TEXT NOT NULL,
    notes           TEXT DEFAULT '',
    difficulty      TEXT NOT NULL DEFAULT 'easy',
    frequency       TEXT NOT NULL DEFAULT 'daily',
    days_of_week    TEXT NOT NULL DEFAULT '0,1,2,3,4,5,6',
    streak          INTEGER NOT NULL DEFAULT 0,
    best_streak     INTEGER NOT NULL DEFAULT 0,
    completed_today INTEGER NOT NULL DEFAULT 0,
    last_completed  TEXT,
    start_date      TEXT NOT NULL DEFAULT (date('now')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS todos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL REFERENCES users(username),
    title           TEXT NOT NULL,
    notes           TEXT DEFAULT '',
    difficulty      TEXT NOT NULL DEFAULT 'easy',
    due_date        TEXT,
    completed       INTEGER NOT NULL DEFAULT 0,
    completed_at    TEXT,
    priority_flag   INTEGER NOT NULL DEFAULT 0,
    tag             TEXT DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS custom_rewards (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL REFERENCES users(username),
    title           TEXT NOT NULL,
    notes           TEXT DEFAULT '',
    gold_cost       REAL NOT NULL DEFAULT 10.0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS activity_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL REFERENCES users(username),
    event_type      TEXT NOT NULL,
    task_id         INTEGER,
    xp_delta        REAL DEFAULT 0.0,
    gold_delta      REAL DEFAULT 0.0,
    hp_delta        REAL DEFAULT 0.0,
    mp_delta        REAL DEFAULT 0.0,
    detail          TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cron_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL REFERENCES users(username),
    run_date        TEXT NOT NULL,
    dailies_due     INTEGER DEFAULT 0,
    dailies_missed  INTEGER DEFAULT 0,
    hp_lost         REAL DEFAULT 0.0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def initialize_database(db_path: str = None) -> None:
    conn = get_connection(db_path)
    with conn:
        conn.executescript(_DDL)
        # Migration: add tag column to todos for existing databases
        try:
            conn.execute("ALTER TABLE todos ADD COLUMN tag TEXT DEFAULT ''")
        except Exception:
            pass
    conn.close()
