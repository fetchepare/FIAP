"""
Endpoints de dashboard e suporte ao frontend web.

Rotas:
  GET  /dashboard/stats                   — cards do topo (KPIs)
  GET  /dashboard/alerts                  — alertas recentes
  GET  /patients                          — lista de pacientes
  GET  /patients/{id}                     — detalhe do paciente
  GET  /patients/{id}/vitals              — histórico de PA/BCF para gráfico
  GET  /patients/{id}/audio               — histórico de análises de áudio
  GET  /patients/{id}/video               — histórico de análises de vídeo
  GET  /patients/{id}/fusion              — último resultado de fusão
  POST /alerts/{id}/read                  — marcar alerta como lido
  POST /patients/{id}/vitals              — salvar leitura e rodar detector
  WS   /ws/monitor/{patient_id}           — monitor ao vivo (vitais sintéticos)
"""
from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.database.db import get_conn
from src.models.schemas import LeituraVital
from src.vitals.anomaly_detector import DetectorAnomaliasVitais

router = APIRouter()
_detector = DetectorAnomaliasVitais()

# ── helpers ─────────────────────────────────────────────────────────────────

NIVEL_COR = {"baixo": "#84B59F", "medio": "#E4A84B", "alto": "#C97B63", "critico": "#B33A3A"}
NIVEL_ORDEM = {"baixo": 0, "medio": 1, "alto": 2, "critico": 3}


def _row_to_dict(row) -> dict:
    return dict(row)


# ── KPIs ────────────────────────────────────────────────────────────────────

@router.get("/dashboard/stats")
def dashboard_stats():
    with get_conn() as conn:
        total_pacientes = conn.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0]
        alertas_nao_lidos = conn.execute(
            "SELECT COUNT(*) FROM alertas WHERE lido=0"
        ).fetchone()[0]
        alertas_criticos = conn.execute(
            "SELECT COUNT(*) FROM alertas WHERE nivel IN ('alto','critico') AND lido=0"
        ).fetchone()[0]
        dist = conn.execute(
            """SELECT nivel_risco_geral, COUNT(*) as n FROM resultados_fusao
               WHERE id IN (SELECT MAX(id) FROM resultados_fusao GROUP BY paciente_id)
               GROUP BY nivel_risco_geral"""
        ).fetchall()
        risco_dist = {r["nivel_risco_geral"]: r["n"] for r in dist}

    return {
        "total_pacientes": total_pacientes,
        "alertas_nao_lidos": alertas_nao_lidos,
        "alertas_criticos": alertas_criticos,
        "risco_distribuicao": risco_dist,
    }


# ── Alertas ──────────────────────────────────────────────────────────────────

@router.get("/dashboard/alerts")
def dashboard_alerts(limit: int = 20):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT a.*, p.nome as paciente_nome
               FROM alertas a JOIN pacientes p ON p.id=a.paciente_id
               ORDER BY a.timestamp DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


@router.post("/alerts/{alerta_id}/read")
def mark_read(alerta_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE alertas SET lido=1 WHERE id=?", (alerta_id,))
    return {"ok": True}


# ── Pacientes ────────────────────────────────────────────────────────────────

@router.get("/patients")
def list_patients():
    with get_conn() as conn:
        pacientes = conn.execute("SELECT * FROM pacientes ORDER BY id").fetchall()
        result = []
        for p in pacientes:
            pd = _row_to_dict(p)
            fusao = conn.execute(
                "SELECT nivel_risco_geral FROM resultados_fusao WHERE paciente_id=? ORDER BY id DESC LIMIT 1",
                (p["id"],),
            ).fetchone()
            pd["nivel_risco"] = fusao["nivel_risco_geral"] if fusao else "baixo"
            pd["cor_risco"] = NIVEL_COR.get(pd["nivel_risco"], "#84B59F")
            result.append(pd)
    return result


@router.get("/patients/{paciente_id}")
def get_patient(paciente_id: int):
    with get_conn() as conn:
        p = conn.execute("SELECT * FROM pacientes WHERE id=?", (paciente_id,)).fetchone()
        if not p:
            return {"error": "Paciente não encontrado"}
        pd = _row_to_dict(p)

        fusao = conn.execute(
            "SELECT * FROM resultados_fusao WHERE paciente_id=? ORDER BY id DESC LIMIT 1",
            (paciente_id,),
        ).fetchone()
        pd["ultima_fusao"] = _row_to_dict(fusao) if fusao else None
        if pd["ultima_fusao"]:
            pd["ultima_fusao"]["scores"] = json.loads(pd["ultima_fusao"]["scores_json"])

        pd["alertas_abertos"] = conn.execute(
            "SELECT COUNT(*) FROM alertas WHERE paciente_id=? AND lido=0",
            (paciente_id,),
        ).fetchone()[0]
    return pd


@router.get("/patients/{paciente_id}/vitals")
def patient_vitals(paciente_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM leituras_vitais WHERE paciente_id=? ORDER BY timestamp",
            (paciente_id,),
        ).fetchall()
    result = []
    for r in rows:
        d = _row_to_dict(r)
        d["anomalias"] = json.loads(d["anomalias"])
        result.append(d)
    return result


@router.get("/patients/{paciente_id}/audio")
def patient_audio(paciente_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM resultados_audio WHERE paciente_id=? ORDER BY timestamp DESC",
            (paciente_id,),
        ).fetchall()
    result = []
    for r in rows:
        d = _row_to_dict(r)
        d["alertas"] = json.loads(d["alertas"])
        result.append(d)
    return result


@router.get("/patients/{paciente_id}/video")
def patient_video(paciente_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM resultados_video WHERE paciente_id=? ORDER BY timestamp DESC",
            (paciente_id,),
        ).fetchall()
    result = []
    for r in rows:
        d = _row_to_dict(r)
        d["alertas"] = json.loads(d["alertas"])
        result.append(d)
    return result


@router.get("/patients/{paciente_id}/fusion")
def patient_fusion(paciente_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM resultados_fusao WHERE paciente_id=? ORDER BY timestamp DESC LIMIT 5",
            (paciente_id,),
        ).fetchall()
    result = []
    for r in rows:
        d = _row_to_dict(r)
        d["scores"] = json.loads(d["scores_json"])
        result.append(d)
    return result


# ── Salvar leitura vital com detecção ────────────────────────────────────────

@router.post("/patients/{paciente_id}/vitals")
def save_vital(paciente_id: int, leitura: LeituraVital):
    resultado = _detector.avaliar(leitura)
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO leituras_vitais
               (paciente_id,timestamp,pa_sistolica,pa_diastolica,bcf_bpm,
                proteinuria,prescricao,dose_mg,nivel_risco,anomalias)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                paciente_id, ts,
                leitura.pressao_sistolica, leitura.pressao_diastolica,
                leitura.bcf_bpm, int(bool(leitura.proteinuria)),
                leitura.prescricao_hormonal, leitura.dose_mg,
                resultado.nivel_risco.value,
                json.dumps(resultado.anomalias),
            ),
        )
        if resultado.anomalias:
            for anomalia in resultado.anomalias:
                conn.execute(
                    """INSERT INTO alertas(paciente_id,categoria,nivel,mensagem,canal,lido,timestamp)
                       VALUES(?,?,?,?,?,0,?)""",
                    (paciente_id, "saude_materna", resultado.nivel_risco.value,
                     anomalia, "obstetricia-guarda@hospital.org", ts),
                )
    return {"nivel_risco": resultado.nivel_risco.value, "anomalias": resultado.anomalias}


# ── WebSocket: monitor ao vivo ────────────────────────────────────────────────

@router.websocket("/ws/monitor/{paciente_id}")
async def monitor_live(websocket: WebSocket, paciente_id: int):
    """
    Envia leituras sintéticas de PA e BCF a cada 2 s para simular
    monitoramento contínuo em tempo real durante a apresentação.
    Usa a última leitura real como ponto de partida e aplica variação aleatória.
    """
    await websocket.accept()

    with get_conn() as conn:
        ultima = conn.execute(
            "SELECT * FROM leituras_vitais WHERE paciente_id=? ORDER BY id DESC LIMIT 1",
            (paciente_id,),
        ).fetchone()
        paciente = conn.execute(
            "SELECT gestante FROM pacientes WHERE id=?", (paciente_id,)
        ).fetchone()

    sist = float(ultima["pa_sistolica"] or 120) if ultima else 120.0
    diast = float(ultima["pa_diastolica"] or 78) if ultima else 78.0
    bcf = float(ultima["bcf_bpm"] or 140) if ultima else 140.0
    gestante = bool(paciente["gestante"]) if paciente else False

    try:
        while True:
            # leve variação aleatória
            sist  = round(max(80,  min(200, sist  + random.uniform(-1.5, 2.5))), 1)
            diast = round(max(50,  min(130, diast + random.uniform(-1.0, 1.5))), 1)
            bcf   = round(max(60,  min(200, bcf   + random.uniform(-3.0, 3.0))), 1)

            nivel = "baixo"
            if sist >= 160 or diast >= 110: nivel = "critico"
            elif sist >= 140 or diast >= 90: nivel = "alto"
            elif sist >= 130 or diast >= 85: nivel = "medio"

            payload = {
                "ts":    datetime.utcnow().strftime("%H:%M:%S"),
                "sist":  sist,
                "diast": diast,
                "bcf":   bcf if gestante else None,
                "nivel": nivel,
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
