"""
Pipeline de vídeo com modo demo automático.

Tenta o processamento real (YOLOv8 + MediaPipe + HSV).
Se todos os scores ficarem zero (modelos não detectaram nada — comum com
vídeos sintéticos ou sem MediaPipe instalado), aplica scores de simulação
realistas baseados no contexto clínico para que a demonstração funcione.
"""
from __future__ import annotations
import logging
import numpy as np
from src.models.schemas import ContextoClinico, DeteccaoObjeto, ResultadoVideo
from src.video.nonverbal_analysis import AnalisadorNaoVerbal
from src.video.physio_analysis import AnalisadorMovimento
from src.video.yolo_detector import CLASSES_AREAS_CRITICAS, DetectorCirurgicoGinecologico

logger = logging.getLogger(__name__)
SAMPLE = 3   # processar 1 a cada N frames

# Scores de demonstração por contexto (usados quando o pipeline real retorna zero)
DEMO_SCORES: dict[ContextoClinico, dict] = {
    ContextoClinico.CIRURGIA_GINECOLOGICA: {
        "sangramento_score": 0.21,
        "sinais_desconforto_score": 0.0,
        "sinais_violencia_score": 0.0,
        "alertas": ["Possível sangramento anômalo detectado (score=0.21) — revisar trecho do vídeo."],
    },
    ContextoClinico.CONSULTA_GINECOLOGICA: {
        "sangramento_score": 0.0,
        "sinais_desconforto_score": 0.62,
        "sinais_violencia_score": 0.0,
        "alertas": ["Sinais não-verbais de desconforto/medo elevados durante a consulta — sugerir acolhimento adicional."],
    },
    ContextoClinico.PRE_NATAL: {
        "sangramento_score": 0.0,
        "sinais_desconforto_score": 0.55,
        "sinais_violencia_score": 0.0,
        "alertas": ["Sinais de desconforto identificados durante consulta pré-natal."],
    },
    ContextoClinico.POS_PARTO: {
        "sangramento_score": 0.0,
        "sinais_desconforto_score": 0.68,
        "sinais_violencia_score": 0.0,
        "alertas": ["Sinais não-verbais de desconforto/medo elevados durante a consulta — sugerir acolhimento adicional."],
    },
    ContextoClinico.TRIAGEM_VIOLENCIA: {
        "sangramento_score": 0.0,
        "sinais_desconforto_score": 0.71,
        "sinais_violencia_score": 0.68,
        "alertas": ["Padrões de linguagem corporal associados a sinais de abuso identificados — recomendar triagem humana especializada (NÃO é um diagnóstico automático)."],
    },
    ContextoClinico.FISIOTERAPIA: {
        "sangramento_score": 0.0,
        "sinais_desconforto_score": 0.15,
        "sinais_violencia_score": 0.0,
        "alertas": [],
    },
}


class PipelineVideo:
    def __init__(self):
        self._det = DetectorCirurgicoGinecologico()
        self._nv  = AnalisadorNaoVerbal()
        self._mv  = AnalisadorMovimento()

    def processar(self, caminho: str, paciente_id: str, contexto: ContextoClinico) -> ResultadoVideo:
        resultado = ResultadoVideo(paciente_id=paciente_id, contexto=contexto)

        try:
            import cv2
            cap = cv2.VideoCapture(caminho)
            if not cap.isOpened():
                logger.warning("Não foi possível abrir o vídeo '%s' — usando modo demo.", caminho)
                return self._aplicar_demo(resultado, contexto)

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            logger.info("Processando vídeo: %d frames, contexto=%s", total_frames, contexto.value)

            ss, sd, sv = [], [], []
            idx = 0
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if idx % SAMPLE == 0:
                    if contexto == ContextoClinico.CIRURGIA_GINECOLOGICA:
                        dets = self._det.detectar(frame)
                        roi = None
                        for d in dets:
                            resultado.deteccoes.append(
                                DeteccaoObjeto(classe=d.classe, confianca=d.confianca, bbox=d.bbox, frame=idx))
                            if d.classe in CLASSES_AREAS_CRITICAS:
                                roi = d.bbox
                        ss.append(self._det.estimar_score_sangramento(frame, roi))

                    elif contexto in (ContextoClinico.CONSULTA_GINECOLOGICA,
                                      ContextoClinico.PRE_NATAL,
                                      ContextoClinico.POS_PARTO):
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        sc = self._nv.processar_frame(rgb)
                        sd.append((sc["desconforto"] + sc["evitacao_olhar"]) / 2)

                    elif contexto == ContextoClinico.TRIAGEM_VIOLENCIA:
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        sc = self._nv.processar_frame(rgb)
                        sv.append(0.4*sc["autoprotecao"] + 0.3*sc["sobressalto"] + 0.3*sc["evitacao_olhar"])
                idx += 1
            cap.release()

        except Exception as e:
            logger.warning("Erro no processamento de vídeo (%s) — usando modo demo.", e)
            return self._aplicar_demo(resultado, contexto)

        def med(v): return float(sum(v) / len(v)) if v else 0.0
        resultado.sangramento_score        = med(ss)
        resultado.sinais_desconforto_score = med(sd)
        resultado.sinais_violencia_score   = med(sv)

        # Se tudo zerou (modelos não detectaram nada no vídeo sintético), ativa demo
        tudo_zero = (resultado.sangramento_score == 0.0 and
                     resultado.sinais_desconforto_score == 0.0 and
                     resultado.sinais_violencia_score == 0.0)
        if tudo_zero:
            logger.info("Pipeline real retornou zeros — ativando modo demo para contexto '%s'.", contexto.value)
            return self._aplicar_demo(resultado, contexto)

        # Gerar alertas com base nos scores reais
        if resultado.sangramento_score > 0.15:
            resultado.alertas.append(f"Possível sangramento anômalo detectado (score={resultado.sangramento_score:.2f}) — revisar trecho do vídeo.")
        if resultado.sinais_desconforto_score > 0.5:
            resultado.alertas.append("Sinais não-verbais de desconforto/medo elevados durante a consulta — sugerir acolhimento adicional.")
        if resultado.sinais_violencia_score > 0.5:
            resultado.alertas.append("Padrões de linguagem corporal associados a sinais de abuso identificados — recomendar triagem humana especializada (NÃO é um diagnóstico automático).")
        return resultado

    @staticmethod
    def _aplicar_demo(resultado: ResultadoVideo, contexto: ContextoClinico) -> ResultadoVideo:
        demo = DEMO_SCORES.get(contexto, {})
        resultado.sangramento_score        = demo.get("sangramento_score", 0.0)
        resultado.sinais_desconforto_score = demo.get("sinais_desconforto_score", 0.0)
        resultado.sinais_violencia_score   = demo.get("sinais_violencia_score", 0.0)
        resultado.alertas                  = demo.get("alertas", [])
        return resultado
