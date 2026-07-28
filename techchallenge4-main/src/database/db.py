"""
Banco de dados SQLite.
No Azure App Service, o diretório /home é persistente entre reinicializações.
Localmente usa ./data/saude_mulher.db
"""
from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Azure App Service → /home/data/  |  Local → ./data/
_AZURE = Path("/home/data")
_LOCAL = Path(__file__).resolve().parents[2] / "data"

if os.getenv("WEBSITE_SITE_NAME"):          # variável injetada pelo Azure
    DB_PATH = _AZURE / "saude_mulher.db"
else:
    DB_PATH = _LOCAL / "saude_mulher.db"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DDL = """
CREATE TABLE IF NOT EXISTS pacientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    idade           INTEGER,
    contexto        TEXT NOT NULL,
    gestante        INTEGER DEFAULT 0,
    semanas_gestacao INTEGER,
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS leituras_vitais (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    timestamp       TEXT NOT NULL,
    pa_sistolica    REAL, pa_diastolica REAL, bcf_bpm REAL,
    proteinuria     INTEGER DEFAULT 0,
    prescricao      TEXT, dose_mg REAL,
    nivel_risco     TEXT DEFAULT 'baixo',
    anomalias       TEXT DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS resultados_audio (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id                 INTEGER NOT NULL REFERENCES pacientes(id),
    timestamp                   TEXT NOT NULL,
    contexto                    TEXT, transcricao TEXT,
    score_depressao_pos_parto   REAL DEFAULT 0,
    score_ansiedade             REAL DEFAULT 0,
    score_indicio_violencia     REAL DEFAULT 0,
    score_fadiga_hormonal       REAL DEFAULT 0,
    alertas                     TEXT DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS resultados_video (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id              INTEGER NOT NULL REFERENCES pacientes(id),
    timestamp                TEXT NOT NULL, contexto TEXT,
    sangramento_score        REAL DEFAULT 0,
    sinais_desconforto_score REAL DEFAULT 0,
    sinais_violencia_score   REAL DEFAULT 0,
    alertas                  TEXT DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS resultados_fusao (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id               INTEGER NOT NULL REFERENCES pacientes(id),
    timestamp                 TEXT NOT NULL,
    nivel_risco_geral         TEXT DEFAULT 'baixo',
    requer_intervencao_humana INTEGER DEFAULT 0,
    scores_json               TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS alertas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
    categoria   TEXT NOT NULL, nivel TEXT NOT NULL,
    mensagem    TEXT NOT NULL, canal TEXT,
    lido        INTEGER DEFAULT 0,
    timestamp   TEXT NOT NULL
);
"""

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(DDL)
