from __future__ import annotations
import numpy as np

PALAVRAS_DEPRESSAO=["não sinto vontade","não consigo cuidar","sem energia","vazio","tristeza","chorando","não durmo"]
PALAVRAS_ANSIEDADE=["medo de perder","preocupada","não consigo parar de pensar","coração acelerado","nervosa","pânico"]
PALAVRAS_VIOLENCIA=["ele não deixa","tenho medo dele","não posso sair","ele controla","machucou","ameaçou"]
PALAVRAS_FADIGA=["cansaço","sem disposição","ganho de peso","queda de cabelo","alteração de humor","ondas de calor"]

def _score_palavras(texto, vocab):
    t=texto.lower(); return float(np.clip(sum(1 for w in vocab if w in t)/3.,0,1))

def _prosodico_depressao(f):
    if not f: return 0.
    return float(np.clip((1-np.clip(f.get("f0_desvio_hz",0)/40,0,1)+1-np.clip(f.get("energia_media",0)*20,0,1)+np.clip(f.get("razao_pausas",0),0,1))/3,0,1))

def _prosodico_ansiedade(f):
    if not f: return 0.
    return float(np.clip((np.clip(f.get("f0_desvio_hz",0)/60,0,1)+np.clip(f.get("taxa_fala_proxy",0)*8,0,1))/2,0,1))

def _prosodico_violencia(f):
    if not f: return 0.
    return float(np.clip((1-np.clip(f.get("energia_media",0)*20,0,1)+np.clip(f.get("razao_pausas",0),0,1))/2,0,1))

class ClassificadorRiscoVocal:
    def classificar(self, transcricao: str, features: dict, entidades: list) -> dict:
        return {
            "score_depressao_pos_parto": round(.6*_score_palavras(transcricao,PALAVRAS_DEPRESSAO)+.4*_prosodico_depressao(features),3),
            "score_ansiedade":           round(.5*_score_palavras(transcricao,PALAVRAS_ANSIEDADE)+.5*_prosodico_ansiedade(features),3),
            "score_indicio_violencia":   round(.6*_score_palavras(transcricao,PALAVRAS_VIOLENCIA)+.4*_prosodico_violencia(features),3),
            "score_fadiga_hormonal":     round(min(1.,_score_palavras(transcricao,PALAVRAS_FADIGA)+(.3 if any("fadiga" in e.lower() for e in entidades) else 0)),3),
        }
