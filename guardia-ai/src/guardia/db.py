"""Persistência SQLite: usuários, análises, revisões humanas e trilha de auditoria (hash encadeado)."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('admin','profissional','auditor')),
  active INTEGER NOT NULL DEFAULT 1,
  failed_attempts INTEGER NOT NULL DEFAULT 0,
  locked_until TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS analyses(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  user_id INTEGER NOT NULL REFERENCES users(id),
  case_ref TEXT NOT NULL,
  input_json TEXT NOT NULL,
  relato TEXT,
  probability REAL NOT NULL,
  threshold REAL NOT NULL,
  risk_band TEXT NOT NULL,
  contributions_json TEXT NOT NULL,
  sources_json TEXT NOT NULL,
  explanation TEXT NOT NULL,
  llm_provider TEXT NOT NULL,
  model_version TEXT NOT NULL,
  flags_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  analysis_id INTEGER NOT NULL REFERENCES analyses(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  decision TEXT NOT NULL,
  notes TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  detail TEXT NOT NULL,
  prev_hash TEXT NOT NULL,
  hash TEXT NOT NULL
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def conn():
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(config.DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA journal_mode=WAL")
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def init_db():
    with conn() as c:
        c.executescript(SCHEMA)


# ---------- auditoria com hash encadeado (evidência de adulteração) ----------
def _h(prev: str, ts: str, actor: str, action: str, detail: str) -> str:
    return hashlib.sha256(f"{prev}|{ts}|{actor}|{action}|{detail}".encode()).hexdigest()


def audit(actor: str, action: str, detail: dict | str = "") -> None:
    detail = detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False, sort_keys=True)
    with conn() as c:
        c.execute("BEGIN IMMEDIATE")
        row = c.execute("SELECT hash FROM audit ORDER BY id DESC LIMIT 1").fetchone()
        prev = row["hash"] if row else "GENESIS"
        ts = now()
        c.execute(
            "INSERT INTO audit(ts,actor,action,detail,prev_hash,hash) VALUES(?,?,?,?,?,?)",
            (ts, actor, action, detail, prev, _h(prev, ts, actor, action, detail)),
        )


def verify_audit_chain() -> tuple[bool, int | None]:
    """Retorna (ok, id_do_primeiro_registro_inconsistente)."""
    with conn() as c:
        rows = c.execute("SELECT * FROM audit ORDER BY id").fetchall()
    prev = "GENESIS"
    for r in rows:
        if r["prev_hash"] != prev or r["hash"] != _h(prev, r["ts"], r["actor"], r["action"], r["detail"]):
            return False, r["id"]
        prev = r["hash"]
    return True, None
