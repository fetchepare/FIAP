from __future__ import annotations
import logging, numpy as np
logger = logging.getLogger(__name__)

def extrair_features(caminho_audio: str) -> dict[str, float]:
    try: import librosa
    except ImportError:
        logger.warning("librosa não instalado — features prosódicas indisponíveis.")
        return {}
    y, sr = librosa.load(caminho_audio, sr=None, mono=True)
    if y.size == 0: return {}
    f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"))
    f0_voz = f0[voiced_flag] if voiced_flag is not None else np.array([])
    rms = librosa.feature.rms(y=y)[0]
    limiar = float(np.percentile(rms, 20))
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    return {
        "f0_media_hz":   float(np.nanmean(f0_voz)) if f0_voz.size else 0.0,
        "f0_desvio_hz":  float(np.nanstd(f0_voz))  if f0_voz.size else 0.0,
        "f0_faixa_hz":   float(np.nanmax(f0_voz)-np.nanmin(f0_voz)) if f0_voz.size else 0.0,
        "energia_media": float(np.mean(rms)),
        "energia_desvio":float(np.std(rms)),
        "razao_pausas":  float(np.mean(rms < limiar)),
        "taxa_fala_proxy":float(np.mean(zcr)),
        "duracao_s":     float(len(y)/sr),
    }
