from __future__ import annotations
from collections import defaultdict, deque
from src.models.schemas import LeituraVital, NivelRisco, ResultadoVitais

PA_SIST_HIPER=140.; PA_DIAST_HIPER=90.; PA_SIST_CRIT=160.; PA_DIAST_CRIT=110.
BCF_BRAD=110.; BCF_TAQUI=160.; BCF_BRAD_CRIT=100.; BCF_TAQUI_CRIT=180.
JANELA=5
_ORDEM=[NivelRisco.BAIXO,NivelRisco.MEDIO,NivelRisco.ALTO,NivelRisco.CRITICO]

def _maior(a,b): return a if _ORDEM.index(a)>=_ORDEM.index(b) else b

class DetectorAnomaliasVitais:
    def __init__(self): self._hist=defaultdict(lambda: deque(maxlen=JANELA))

    def avaliar(self, l: LeituraVital) -> ResultadoVitais:
        anomalias=[]; nivel=NivelRisco.BAIXO
        if l.pressao_sistolica and l.pressao_diastolica:
            s,d=l.pressao_sistolica,l.pressao_diastolica
            if s>=PA_SIST_CRIT or d>=PA_DIAST_CRIT:
                anomalias.append(f"Pressão arterial em nível crítico ({s:.0f}/{d:.0f} mmHg) — risco de pré-eclâmpsia grave/eclâmpsia, avaliação imediata.")
                nivel=_maior(nivel,NivelRisco.CRITICO)
            elif s>=PA_SIST_HIPER or d>=PA_DIAST_HIPER:
                msg=f"Hipertensão gestacional detectada ({s:.0f}/{d:.0f} mmHg)."
                if l.proteinuria: msg+=" Associada a proteinúria — suspeita de pré-eclâmpsia."; nivel=_maior(nivel,NivelRisco.ALTO)
                else: nivel=_maior(nivel,NivelRisco.MEDIO)
                anomalias.append(msg)
            h=self._hist[l.paciente_id]; h.append(s)
            if len(h)>=3:
                vals=list(h)
                if all(vals[i]<vals[i+1] for i in range(len(vals)-1)) and vals[-1]-vals[0]>=15:
                    anomalias.append(f"Tendência de aumento progressivo da pressão sistólica nas últimas {len(vals)} leituras ({vals[0]:.0f} → {vals[-1]:.0f} mmHg).")
                    nivel=_maior(nivel,NivelRisco.MEDIO)
        if l.bcf_bpm:
            b=l.bcf_bpm
            if b<=BCF_BRAD_CRIT or b>=BCF_TAQUI_CRIT:
                anomalias.append(f"Batimento cardíaco fetal em nível crítico ({b:.0f} bpm) — avaliação obstétrica imediata.")
                nivel=_maior(nivel,NivelRisco.CRITICO)
            elif b<BCF_BRAD:
                anomalias.append(f"Bradicardia fetal ({b:.0f} bpm)."); nivel=_maior(nivel,NivelRisco.ALTO)
            elif b>BCF_TAQUI:
                anomalias.append(f"Taquicardia fetal ({b:.0f} bpm)."); nivel=_maior(nivel,NivelRisco.ALTO)
        if l.prescricao_hormonal and l.dose_mg:
            limites={"estradiol":4.0,"progesterona":400.0,"levonorgestrel":1.5}
            lim=limites.get(l.prescricao_hormonal.lower())
            if lim and l.dose_mg>lim:
                anomalias.append(f"Dose de {l.prescricao_hormonal} ({l.dose_mg}mg) acima do limite ({lim}mg) — revisar prescrição.")
                nivel=_maior(nivel,NivelRisco.MEDIO)
        return ResultadoVitais(paciente_id=l.paciente_id, anomalias=anomalias, nivel_risco=nivel)
