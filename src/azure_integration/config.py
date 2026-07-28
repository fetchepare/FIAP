from __future__ import annotations
import os
from dataclasses import dataclass
from functools import lru_cache

@dataclass(frozen=True)
class AzureConfig:
    speech_key: str | None; speech_region: str | None
    language_key: str | None; language_endpoint: str | None
    vision_key: str | None; vision_endpoint: str | None
    communication_connection_string: str | None

    @property
    def speech_configurado(self): return bool(self.speech_key and self.speech_region)
    @property
    def language_configurado(self): return bool(self.language_key and self.language_endpoint)
    @property
    def communication_configurado(self): return bool(self.communication_connection_string)

@lru_cache(maxsize=1)
def get_azure_config() -> AzureConfig:
    return AzureConfig(
        speech_key=os.getenv("AZURE_SPEECH_KEY"),
        speech_region=os.getenv("AZURE_SPEECH_REGION"),
        language_key=os.getenv("AZURE_LANGUAGE_KEY"),
        language_endpoint=os.getenv("AZURE_LANGUAGE_ENDPOINT"),
        vision_key=os.getenv("AZURE_VISION_KEY"),
        vision_endpoint=os.getenv("AZURE_VISION_ENDPOINT"),
        communication_connection_string=os.getenv("AZURE_COMMUNICATION_CONNECTION_STRING"),
    )
