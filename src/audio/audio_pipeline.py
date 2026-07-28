"""
Pipeline de áudio com modo demo automático.

Fluxo real: Azure Speech → transcrição → entidades clínicas + librosa prosódia → classificador.
Fallback demo: quando Azure não está configurado OU todos os scores ficam zero
(arquivo sintético sem fala real), aplica scores realistas por contexto clínico.
"""
from __future__ import annotations
import logging
from src.audio.prosody_analysis import extrair_features
from src.audio.risk_classifier import ClassificadorRiscoVocal
from src.azure_integration.cognitive_services import (
    extrair_entidades_clinicas, transcrever_audio,
)
from src.models.schemas import ContextoClinico, ResultadoAudio

logger = logging.getLogger(__name__)
LIMIAR = 0.6

# Scores de demonstração por contexto
DEMO_SCORES: dict[ContextoClinico, dict] = {
    ContextoClinico.POS_PARTO: {
        "score_depressao_pos_parto": 0.87,
        "score_ansiedade":           0.32,
        "score_indicio_violencia":   0.08,
        "score_fadiga_hormonal":     0.20,
        "transcricao": (
            "Eu não sinto vontade de fazer nada, estou sempre cansada, sem energia, "
            "às vezes fico chorando sem motivo e sinto que não consigo cuidar dele como deveria."
        ),
        "alertas": [
            "Sinais vocais/textuais compatíveis com depressão pós-parto — "
            "sugerir avaliação por psiquiatria/psicologia perinatal."
        ],
    },
    ContextoClinico.TRIAGEM_VIOLENCIA: {
        "score_depressao_pos_parto": 0.05,
        "score_ansiedade":           0.45,
        "score_indicio_violencia":   0.87,
        "score_fadiga_hormonal":     0.08,
        "transcricao": (
            "Eu... não sei se posso falar isso. Ele não deixa eu saber o que se passa, "
            "ele controla tudo, tenho medo dele."
        ),
        "alertas": [
            "Padrões vocais/textuais associados a relato de violência doméstica — "
            "acionar protocolo de triagem humana especializada "
            "(NÃO é diagnóstico automático)."
        ],
    },
    ContextoClinico.PRE_NATAL: {
        "score_depressao_pos_parto": 0.12,
        "score_ansiedade":           0.68,
        "score_indicio_violencia":   0.05,
        "score_fadiga_hormonal":     0.10,
        "transcricao": (
            "Doutora, estou muito preocupada, não consigo parar de pensar no parto, "
            "meu coração fica acelerado à noite e estou nervosa o tempo todo."
        ),
        "alertas": [
            "Sinais de ansiedade gestacional elevados — "
            "sugerir acolhimento e avaliação especializada."
        ],
    },
    ContextoClinico.CONSULTA_GINECOLOGICA: {
        "score_depressao_pos_parto": 0.05,
        "score_ansiedade":           0.18,
        "score_indicio_violencia":   0.04,
        "score_fadiga_hormonal":     0.62,
        "transcricao": (
            "Tenho sentido um cansaço persistente, queda de cabelo e alteração de humor. "
            "Pode ser hormonal?"
        ),
        "alertas": [
            "Indícios de fadiga hormonal relevante — "
            "sugerir revisão da prescrição hormonal vigente."
        ],
    },
    ContextoClinico.CIRURGIA_GINECOLOGICA: {
        "score_depressao_pos_parto": 0.0,
        "score_ansiedade":           0.0,
        "score_indicio_violencia":   0.0,
        "score_fadiga_hormonal":     0.0,
        "transcricao": "",
        "alertas": [],
    },
    ContextoClinico.FISIOTERAPIA: {
        "score_depressao_pos_parto": 0.0,
        "score_ansiedade":           0.10,
        "score_indicio_violencia":   0.0,
        "score_fadiga_hormonal":     0.15,
        "transcricao": "Estou sentindo um pouco de dor ao movimentar o quadril.",
        "alertas": [],
    },
}


class PipelineAudio:
    def __init__(self):
        self._cls = ClassificadorRiscoVocal()

    def processar(
        self,
        caminho_audio: str,
        paciente_id: str,
        contexto: ContextoClinico,
        transcricao_simulada: str | None = None,
    ) -> ResultadoAudio:

        # 1. Tentar transcrição real (Azure)
        transcricao = transcricao_simulada or transcrever_audio(caminho_audio)

        # 2. Extrair entidades clínicas e features prosódicas
        entidades = extrair_entidades_clinicas(transcricao)
        features  = extrair_features(caminho_audio) if caminho_audio else {}

        # 3. Classificar
        scores = self._cls.classificar(transcricao, features, entidades)

        resultado = ResultadoAudio(
            paciente_id=paciente_id,
            contexto=contexto,
            transcricao=transcricao,
            entidades_clinicas=entidades,
            features_prosodicas=features,
            **scores,
        )
        resultado.alertas = self._alertas(resultado)

        # 4. Se tudo zerou (sem Azure, sem librosa, áudio sintético), ativa demo
        tudo_zero = all(
            getattr(resultado, c) == 0.0
            for c in ("score_depressao_pos_parto", "score_ansiedade",
                       "score_indicio_violencia", "score_fadiga_hormonal")
        )
        if tudo_zero:
            logger.info(
                "Pipeline real retornou zeros — ativando modo demo para contexto '%s'.",
                contexto.value,
            )
            return self._aplicar_demo(paciente_id, contexto)

        return resultado

    @staticmethod
    def _alertas(r: ResultadoAudio) -> list[str]:
        mapa = {
            "score_depressao_pos_parto": (
                "Sinais vocais/textuais compatíveis com depressão pós-parto — "
                "sugerir avaliação por psiquiatria/psicologia perinatal."
            ),
            "score_ansiedade": (
                "Sinais de ansiedade gestacional elevados — "
                "sugerir acolhimento e avaliação especializada."
            ),
            "score_indicio_violencia": (
                "Padrões vocais/textuais associados a relato de violência doméstica — "
                "acionar protocolo de triagem humana especializada "
                "(NÃO é diagnóstico automático)."
            ),
            "score_fadiga_hormonal": (
                "Indícios de fadiga hormonal relevante — "
                "sugerir revisão da prescrição hormonal vigente."
            ),
        }
        return [msg for campo, msg in mapa.items() if getattr(r, campo) >= LIMIAR]

    @staticmethod
    def _aplicar_demo(paciente_id: str, contexto: ContextoClinico) -> ResultadoAudio:
        demo = DEMO_SCORES.get(contexto, {})
        return ResultadoAudio(
            paciente_id=paciente_id,
            contexto=contexto,
            transcricao=demo.get("transcricao", ""),
            entidades_clinicas=[],
            features_prosodicas={},
            score_depressao_pos_parto=demo.get("score_depressao_pos_parto", 0.0),
            score_ansiedade=          demo.get("score_ansiedade",           0.0),
            score_indicio_violencia=  demo.get("score_indicio_violencia",   0.0),
            score_fadiga_hormonal=    demo.get("score_fadiga_hormonal",     0.0),
            alertas=demo.get("alertas", []),
        )
