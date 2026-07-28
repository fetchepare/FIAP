"""
Integração com serviços de IA externos.

Transcrição de áudio: Google Cloud Speech-to-Text (substitui Azure Speech)
Entidades clínicas:   Azure AI Language — Text Analytics for Health
Alertas:              Azure Communication Services

Variáveis de ambiente necessárias:
  GOOGLE_APPLICATION_CREDENTIALS  → caminho para o JSON de credenciais do Google
  AZURE_LANGUAGE_KEY               → chave do Azure Language
  AZURE_LANGUAGE_ENDPOINT          → endpoint do Azure Language
  AZURE_COMMUNICATION_CONNECTION_STRING → connection string do Azure Communication
"""
from __future__ import annotations
import logging
import os
from pathlib import Path
from .config import get_azure_config

logger = logging.getLogger(__name__)

_PALAVRAS_CLINICAS = [
    "dor", "sangramento", "cólica", "enjoo", "náusea", "pressão",
    "ansiedade", "insônia", "fadiga", "tontura", "inchaço",
    "tristeza", "choro", "medo", "cansaço", "queda de cabelo",
]


# ── TRANSCRIÇÃO — Google Cloud Speech-to-Text ─────────────────────────────

def transcrever_audio(caminho_audio: str) -> str:
    """
    Transcreve áudio usando Google Cloud Speech-to-Text.

    Requer:
      pip install google-cloud-speech
      GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credenciais.json
    """
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not creds_path or not Path(creds_path).exists():
        logger.warning(
            "GOOGLE_APPLICATION_CREDENTIALS não configurado ou arquivo não encontrado "
            "— transcrição indisponível (modo demo ativo)."
        )
        return ""

    try:
        from google.cloud import speech
    except ImportError:
        logger.warning("google-cloud-speech não instalado. Execute: pip install google-cloud-speech")
        return ""

    try:
        client = speech.SpeechClient()

        # Ler o arquivo de áudio
        with open(caminho_audio, "rb") as f:
            conteudo = f.read()

        # Detectar formato pelo sufixo
        sufixo = Path(caminho_audio).suffix.lower()
        encoding_map = {
            ".wav":  speech.RecognitionConfig.AudioEncoding.LINEAR16,
            ".mp3":  speech.RecognitionConfig.AudioEncoding.MP3,
            ".flac": speech.RecognitionConfig.AudioEncoding.FLAC,
            ".ogg":  speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            ".webm": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        }
        encoding = encoding_map.get(sufixo, speech.RecognitionConfig.AudioEncoding.LINEAR16)

        config = speech.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=16000,
            language_code="pt-BR",
            enable_automatic_punctuation=True,
            model="latest_long",
        )
        audio = speech.RecognitionAudio(content=conteudo)

        # Arquivos < 1 min: recognize síncrono
        # Arquivos > 1 min: usar long_running_recognize
        tamanho_mb = len(conteudo) / (1024 * 1024)
        if tamanho_mb < 8:
            response = client.recognize(config=config, audio=audio)
            transcricao = " ".join(
                result.alternatives[0].transcript
                for result in response.results
                if result.alternatives
            )
        else:
            operation = client.long_running_recognize(config=config, audio=audio)
            logger.info("Áudio grande — aguardando transcrição assíncrona...")
            response = operation.result(timeout=300)
            transcricao = " ".join(
                result.alternatives[0].transcript
                for result in response.results
                if result.alternatives
            )

        logger.info("Transcrição Google Speech concluída: %d chars", len(transcricao))
        return transcricao

    except Exception as e:
        logger.error("Erro na transcrição Google Speech: %s", e)
        return ""


# ── ENTIDADES CLÍNICAS — Azure AI Language ────────────────────────────────

def extrair_entidades_clinicas(texto: str) -> list[str]:
    """
    Extrai entidades clínicas usando Azure Text Analytics for Health.
    Fallback: busca por palavras-chave clínicas no texto.
    """
    if not texto:
        return []

    cfg = get_azure_config()
    if not cfg.language_configurado:
        logger.warning("AZURE_LANGUAGE_KEY não configurado — usando extração por palavras-chave.")
        return _entidades_fallback(texto)

    try:
        from azure.ai.textanalytics import TextAnalyticsClient
        from azure.core.credentials import AzureKeyCredential
        client = TextAnalyticsClient(
            endpoint=cfg.language_endpoint,
            credential=AzureKeyCredential(cfg.language_key),
        )
        poller = client.begin_analyze_healthcare_entities([texto])
        resultado = poller.result()
        entidades = [
            f"{e.category}:{e.text}"
            for doc in resultado if not doc.is_error
            for e in doc.entities
        ]
        logger.info("Entidades clínicas extraídas: %d", len(entidades))
        return entidades

    except Exception as e:
        logger.error("Erro ao extrair entidades clínicas: %s", e)
        return _entidades_fallback(texto)


def _entidades_fallback(texto: str) -> list[str]:
    texto_lower = texto.lower()
    return [p for p in _PALAVRAS_CLINICAS if p in texto_lower]


# ── ALERTAS — Azure Communication Services ────────────────────────────────

def enviar_alerta_equipe(destinatario: str, assunto: str, mensagem: str) -> bool:
    """
    Envia alerta por e-mail via Azure Communication Services.
    Fallback: registra apenas em log.
    """
    cfg = get_azure_config()
    if not cfg.communication_configurado:
        logger.warning("AZURE_COMMUNICATION não configurado — alerta registrado em log: %s", mensagem)
        return False

    try:
        from azure.communication.email import EmailClient
        client = EmailClient.from_connection_string(cfg.communication_connection_string)
        poller = client.begin_send({
            "senderAddress": "alertas@hospital.azurecomm.net",
            "recipients": {"to": [{"address": destinatario}]},
            "content": {"subject": assunto, "plainText": mensagem},
        })
        poller.result()
        logger.info("Alerta enviado para %s", destinatario)
        return True
    except Exception as e:
        logger.error("Erro ao enviar alerta: %s", e)
        return False
