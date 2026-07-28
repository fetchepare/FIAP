"""
Seed do banco de dados com dados sintéticos realistas para demonstração.

5 pacientes cobrindo os cenários do projeto:
  1. Maria Silva      — pré-natal com tendência de pré-eclâmpsia (MÉDIO)
  2. Ana Costa        — pós-parto com depressão pós-parto           (ALTO)
  3. Julia Santos     — triagem com indícios de violência doméstica  (ALTO)
  4. Carla Oliveira   — consulta ginecológica de rotina              (BAIXO)
  5. Patricia Lima    — pré-natal com PA e BCF críticos              (CRÍTICO)
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from .db import get_conn, init_db


def _ts(dias_atras: float, hora: str = "08:00") -> str:
    dt = datetime.now() - timedelta(days=dias_atras)
    return dt.strftime(f"%Y-%m-%d {hora}:00")


def seed() -> None:
    init_db()
    with get_conn() as conn:
        if conn.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0] > 0:
            return  # já populado

        # ── PACIENTES ────────────────────────────────────────────────────────
        pacientes = [
            (1, "Maria Silva",    28, "pre_natal",           1, 32),
            (2, "Ana Costa",      35, "pos_parto",           0, None),
            (3, "Julia Santos",   22, "triagem_violencia",   0, None),
            (4, "Carla Oliveira", 45, "consulta_ginecologica",0, None),
            (5, "Patricia Lima",  31, "pre_natal",           1, 28),
        ]
        conn.executemany(
            "INSERT INTO pacientes(id,nome,idade,contexto,gestante,semanas_gestacao) VALUES(?,?,?,?,?,?)",
            pacientes,
        )

        # ── LEITURAS VITAIS ───────────────────────────────────────────────────
        # Maria Silva: tendência de PA subindo (risco baixo→médio)
        vitais_maria = [
            (1, _ts(7,  "07:00"), 118, 76,  None, 0, None, None, "baixo",  "[]"),
            (1, _ts(6,  "07:00"), 122, 79,  None, 0, None, None, "baixo",  "[]"),
            (1, _ts(5,  "07:00"), 127, 82,  None, 0, None, None, "baixo",  "[]"),
            (1, _ts(4,  "07:00"), 131, 84,  None, 0, None, None, "medio",  json.dumps(["Tendência de aumento progressivo da pressão sistólica nas últimas 4 leituras (118 → 131 mmHg)"])),
            (1, _ts(3,  "07:00"), 135, 86,  None, 0, None, None, "medio",  json.dumps(["Tendência de aumento progressivo da pressão sistólica"])),
            (1, _ts(2,  "07:00"), 139, 88,  None, 0, None, None, "medio",  json.dumps(["Hipertensão gestacional detectada (139/88 mmHg)"])),
            (1, _ts(1,  "07:00"), 141, 91,  None, 1, None, None, "alto",   json.dumps(["Hipertensão gestacional detectada (141/91 mmHg). Associada a proteinúria — suspeita de pré-eclâmpsia."])),
            (1, _ts(0.1,"07:00"), 143, 92,  None, 1, None, None, "alto",   json.dumps(["Hipertensão gestacional com proteinúria — suspeita de pré-eclâmpsia."])),
        ]

        # Ana Costa: PA normal, mas depressão pós-parto
        vitais_ana = [
            (2, _ts(6, "09:00"), 110, 70, None, 0, None, None, "baixo", "[]"),
            (2, _ts(4, "09:00"), 112, 71, None, 0, None, None, "baixo", "[]"),
            (2, _ts(2, "09:00"), 109, 69, None, 0, None, None, "baixo", "[]"),
            (2, _ts(1, "09:00"), 111, 72, None, 0, None, None, "baixo", "[]"),
        ]

        # Carla Oliveira: tudo normal, estradiol prescrito
        vitais_carla = [
            (4, _ts(5, "10:00"), 115, 74, None, 0, "estradiol", 2.0, "baixo", "[]"),
            (4, _ts(3, "10:00"), 113, 73, None, 0, "estradiol", 2.0, "baixo", "[]"),
            (4, _ts(1, "10:00"), 116, 75, None, 0, "estradiol", 2.0, "baixo", "[]"),
        ]

        # Patricia Lima: PA e BCF críticos
        vitais_patricia = [
            (5, _ts(5, "06:00"), 120, 78, 145, 0, None, None, "baixo",  "[]"),
            (5, _ts(4, "06:00"), 132, 85, 148, 0, None, None, "baixo",  "[]"),
            (5, _ts(3, "06:00"), 148, 94, 155, 1, None, None, "alto",   json.dumps(["Hipertensão gestacional com proteinúria — suspeita de pré-eclâmpsia."])),
            (5, _ts(2, "06:00"), 158, 102, 108, 1, None, None, "critico", json.dumps(["Pressão arterial em nível crítico (158/102 mmHg) — risco de pré-eclâmpsia grave/eclâmpsia.", "Bradicardia fetal (108 bpm)."])),
            (5, _ts(1, "06:00"), 165, 112, 95,  1, None, None, "critico", json.dumps(["Pressão arterial em nível crítico (165/112 mmHg) — avaliação imediata.", "Batimento cardíaco fetal em nível crítico (95 bpm) — avaliação obstétrica imediata."])),
        ]

        all_vitais = vitais_maria + vitais_ana + vitais_carla + vitais_patricia
        conn.executemany(
            """INSERT INTO leituras_vitais
               (paciente_id,timestamp,pa_sistolica,pa_diastolica,bcf_bpm,proteinuria,
                prescricao,dose_mg,nivel_risco,anomalias)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            all_vitais,
        )

        # ── RESULTADOS DE ÁUDIO ──────────────────────────────────────────────
        audio_rows = [
            # Maria — ansiedade gestacional
            (1, _ts(3, "14:00"), "pre_natal",
             "Doutora, estou muito preocupada, não consigo parar de pensar no parto, meu coração fica acelerado à noite e estou nervosa o tempo todo.",
             0.12, 0.68, 0.05, 0.10,
             json.dumps(["Sinais de ansiedade gestacional elevados — sugerir acolhimento e avaliação especializada."])),
            # Ana — depressão pós-parto
            (2, _ts(1, "10:00"), "pos_parto",
             "Eu não sinto vontade de fazer nada, estou sempre cansada, sem energia, às vezes fico chorando sem motivo e sinto que não consigo cuidar dele como deveria.",
             0.87, 0.32, 0.08, 0.20,
             json.dumps(["Sinais vocais/textuais compatíveis com depressão pós-parto — sugerir avaliação por psiquiatria/psicologia perinatal."])),
            # Julia — violência doméstica
            (3, _ts(0.5, "11:00"), "triagem_violencia",
             "Eu... não sei se posso falar isso. Ele não deixa eu saber o que se passa, ele controla tudo, tenho medo dele.",
             0.05, 0.25, 0.87, 0.08,
             json.dumps(["Padrões vocais/textuais associados a relato de violência doméstica — acionar protocolo de triagem humana especializada (NÃO é diagnóstico automático)."])),
            # Carla — fadiga hormonal leve
            (4, _ts(2, "15:00"), "consulta_ginecologica",
             "Tenho sentido um cansaço persistente, queda de cabelo e alteração de humor. Pode ser hormonal?",
             0.05, 0.18, 0.04, 0.62,
             json.dumps(["Indícios de fadiga hormonal relevante — sugerir revisão da prescrição hormonal vigente."])),
        ]
        conn.executemany(
            """INSERT INTO resultados_audio
               (paciente_id,timestamp,contexto,transcricao,
                score_depressao_pos_parto,score_ansiedade,
                score_indicio_violencia,score_fadiga_hormonal,alertas)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            audio_rows,
        )

        # ── RESULTADOS DE VÍDEO ──────────────────────────────────────────────
        video_rows = [
            # Julia — linguagem corporal de violência
            (3, _ts(0.5, "11:00"), "triagem_violencia",
             0.0, 0.71, 0.68,
             json.dumps(["Padrões de linguagem corporal associados a sinais de abuso identificados — recomendar triagem humana especializada (NÃO é um diagnóstico automático)."])),
            # Patricia — cirurgia de emergência (sangramento)
            (5, _ts(1, "08:00"), "cirurgia_ginecologica",
             0.22, 0.0, 0.0,
             json.dumps(["Possível sangramento anômalo detectado (score=0.22) — revisar trecho do vídeo."])),
        ]
        conn.executemany(
            """INSERT INTO resultados_video
               (paciente_id,timestamp,contexto,
                sangramento_score,sinais_desconforto_score,sinais_violencia_score,alertas)
               VALUES(?,?,?,?,?,?,?)""",
            video_rows,
        )

        # ── RESULTADOS DE FUSÃO ───────────────────────────────────────────────
        fusao_rows = [
            (1, _ts(1, "07:30"), "medio",  0, json.dumps([
                {"categoria": "saude_materna",     "score": 0.38, "nivel": "medio",  "origem": ["vitais", "audio"]},
                {"categoria": "saude_psicologica", "score": 0.20, "nivel": "baixo",  "origem": ["audio"]},
            ])),
            (2, _ts(1, "10:30"), "alto",   1, json.dumps([
                {"categoria": "saude_psicologica", "score": 0.61, "nivel": "alto",   "origem": ["audio"]},
                {"categoria": "saude_materna",     "score": 0.10, "nivel": "baixo",  "origem": ["vitais"]},
            ])),
            (3, _ts(0.5, "11:30"), "alto",  1, json.dumps([
                {"categoria": "violencia_domestica","score": 0.77, "nivel": "alto",  "origem": ["audio", "video"]},
                {"categoria": "saude_psicologica", "score": 0.40, "nivel": "medio", "origem": ["audio", "video"]},
            ])),
            (4, _ts(2, "15:30"), "baixo",  0, json.dumps([
                {"categoria": "anomalia_ginecologica","score": 0.12,"nivel":"baixo", "origem": ["vitais"]},
            ])),
            (5, _ts(1, "08:30"), "critico", 1, json.dumps([
                {"categoria": "saude_materna",       "score": 0.95, "nivel": "critico", "origem": ["vitais"]},
                {"categoria": "complicacao_cirurgica","score": 0.22, "nivel": "baixo",  "origem": ["video"]},
            ])),
        ]
        conn.executemany(
            """INSERT INTO resultados_fusao
               (paciente_id,timestamp,nivel_risco_geral,requer_intervencao_humana,scores_json)
               VALUES(?,?,?,?,?)""",
            fusao_rows,
        )

        # ── ALERTAS ───────────────────────────────────────────────────────────
        alertas_rows = [
            (1, "saude_materna",         "medio",   "Tendência de aumento progressivo de PA (118→143 mmHg) + ansiedade gestacional identificada na consulta.", "obstetricia-guarda@hospital.org",   0, _ts(1,  "07:31")),
            (2, "saude_psicologica",     "alto",    "[ALTO] Paciente Ana Costa: risco de saúde psicológica (score=0.61, modalidade: áudio).", "psicologia-perinatal@hospital.org", 0, _ts(1,  "10:31")),
            (3, "violencia_domestica",   "alto",    "[ALTO] Paciente Julia Santos: risco de violência doméstica (score=0.77, modalidades: áudio, vídeo).", "servico-social-psicologia@hospital.org", 0, _ts(0.5,"11:31")),
            (5, "saude_materna",         "critico", "[CRÍTICO] Paciente Patricia Lima: PA 165/112 mmHg + BCF 95 bpm — avaliação obstétrica IMEDIATA.", "obstetricia-guarda@hospital.org",   0, _ts(1,  "06:01")),
            (5, "complicacao_cirurgica", "medio",   "Sangramento anômalo identificado em vídeo cirúrgico (score=0.22) — revisar gravação.", "centro-cirurgico-guarda@hospital.org", 1, _ts(1,  "08:31")),
        ]
        conn.executemany(
            """INSERT INTO alertas
               (paciente_id,categoria,nivel,mensagem,canal,lido,timestamp)
               VALUES(?,?,?,?,?,?,?)""",
            alertas_rows,
        )
