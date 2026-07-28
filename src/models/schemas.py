from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class ContextoClinico(str, Enum):
    CIRURGIA_GINECOLOGICA = "cirurgia_ginecologica"
    CONSULTA_GINECOLOGICA = "consulta_ginecologica"
    PRE_NATAL = "pre_natal"
    POS_PARTO = "pos_parto"
    FISIOTERAPIA = "fisioterapia"
    TRIAGEM_VIOLENCIA = "triagem_violencia"

class NivelRisco(str, Enum):
    BAIXO = "baixo"; MEDIO = "medio"; ALTO = "alto"; CRITICO = "critico"

class CategoriaRisco(str, Enum):
    SAUDE_MATERNA = "saude_materna"
    COMPLICACAO_CIRURGICA = "complicacao_cirurgica"
    VIOLENCIA_DOMESTICA = "violencia_domestica"
    SAUDE_PSICOLOGICA = "saude_psicologica"
    ANOMALIA_GINECOLOGICA = "anomalia_ginecologica"

class DeteccaoObjeto(BaseModel):
    classe: str; confianca: float; bbox: tuple[float,float,float,float]; frame: int

class ResultadoVideo(BaseModel):
    paciente_id: str; contexto: ContextoClinico
    deteccoes: list[DeteccaoObjeto] = Field(default_factory=list)
    sangramento_score: float = 0.0; sinais_desconforto_score: float = 0.0
    sinais_violencia_score: float = 0.0; alertas: list[str] = Field(default_factory=list)

class ResultadoAudio(BaseModel):
    paciente_id: str; contexto: ContextoClinico; transcricao: str = ""
    entidades_clinicas: list[str] = Field(default_factory=list)
    score_depressao_pos_parto: float = 0.0; score_ansiedade: float = 0.0
    score_indicio_violencia: float = 0.0; score_fadiga_hormonal: float = 0.0
    features_prosodicas: dict[str, float] = Field(default_factory=dict)
    alertas: list[str] = Field(default_factory=list)

class LeituraVital(BaseModel):
    paciente_id: str; timestamp: datetime = Field(default_factory=datetime.utcnow)
    pressao_sistolica: Optional[float] = None; pressao_diastolica: Optional[float] = None
    bcf_bpm: Optional[float] = None; proteinuria: Optional[bool] = None
    prescricao_hormonal: Optional[str] = None; dose_mg: Optional[float] = None

class ResultadoVitais(BaseModel):
    paciente_id: str; anomalias: list[str] = Field(default_factory=list)
    nivel_risco: NivelRisco = NivelRisco.BAIXO

class ScoreCategoria(BaseModel):
    categoria: CategoriaRisco; score: float; nivel: NivelRisco; origem: list[str]

class ResultadoFusao(BaseModel):
    paciente_id: str; timestamp: datetime = Field(default_factory=datetime.utcnow)
    scores: list[ScoreCategoria]; nivel_risco_geral: NivelRisco
    requer_intervencao_humana: bool

class Alerta(BaseModel):
    paciente_id: str; categoria: CategoriaRisco; nivel: NivelRisco
    mensagem: str; timestamp: datetime = Field(default_factory=datetime.utcnow)
    canal: str = "fila_equipe_especializada"
