from __future__ import annotations
import numpy as np
from src.models.schemas import CategoriaRisco, NivelRisco, ResultadoAudio, ResultadoFusao, ResultadoVideo, ResultadoVitais, ScoreCategoria

PESOS={
    CategoriaRisco.SAUDE_MATERNA:         {"vitais":0.7,"audio":0.3},
    CategoriaRisco.COMPLICACAO_CIRURGICA: {"video":1.0},
    CategoriaRisco.VIOLENCIA_DOMESTICA:   {"audio":0.5,"video":0.5},
    CategoriaRisco.SAUDE_PSICOLOGICA:     {"audio":0.7,"video":0.3},
    CategoriaRisco.ANOMALIA_GINECOLOGICA: {"vitais":0.5,"video":0.5},
}
_ORD=[NivelRisco.BAIXO,NivelRisco.MEDIO,NivelRisco.ALTO,NivelRisco.CRITICO]
_LIM=[(0.8,NivelRisco.CRITICO),(0.6,NivelRisco.ALTO),(0.35,NivelRisco.MEDIO),(0.,NivelRisco.BAIXO)]
def _nivel(s):
    for t,n in _LIM:
        if s>=t: return n
    return NivelRisco.BAIXO

class MotorFusaoMultimodal:
    def fundir(self, paciente_id, video=None, audio=None, vitais=None) -> ResultadoFusao:
        sinais={
            "video": {} if video is None else {CategoriaRisco.COMPLICACAO_CIRURGICA:video.sangramento_score,CategoriaRisco.VIOLENCIA_DOMESTICA:video.sinais_violencia_score,CategoriaRisco.SAUDE_PSICOLOGICA:video.sinais_desconforto_score,CategoriaRisco.ANOMALIA_GINECOLOGICA:video.sangramento_score},
            "audio": {} if audio is None else {CategoriaRisco.SAUDE_MATERNA:audio.score_ansiedade,CategoriaRisco.VIOLENCIA_DOMESTICA:audio.score_indicio_violencia,CategoriaRisco.SAUDE_PSICOLOGICA:max(audio.score_depressao_pos_parto,audio.score_ansiedade)},
            "vitais":{} if vitais is None else {CategoriaRisco.SAUDE_MATERNA:_ORD.index(vitais.nivel_risco)/3,CategoriaRisco.ANOMALIA_GINECOLOGICA:_ORD.index(vitais.nivel_risco)/3*.6},
        }
        scores=[]
        for cat,pesos in PESOS.items():
            s=0.; orig=[]
            for mod,p in pesos.items():
                v=sinais[mod].get(cat,0.)
                if v>0: orig.append(mod)
                s+=p*v
            scores.append(ScoreCategoria(categoria=cat,score=round(s,3),nivel=_nivel(s),origem=orig))
        geral=max(scores,key=lambda x:_ORD.index(x.nivel)).nivel
        return ResultadoFusao(paciente_id=paciente_id,scores=scores,nivel_risco_geral=geral,requer_intervencao_humana=geral in(NivelRisco.ALTO,NivelRisco.CRITICO))
