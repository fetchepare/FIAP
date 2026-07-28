from __future__ import annotations
import logging, numpy as np
logger=logging.getLogger(__name__)
AMPLITUDE_ESPERADA={"elevacao_perna":80.,"flexao_quadril":100.,"rotacao_tronco":45.}

class AnalisadorMovimento:
    def __init__(self):
        self._ok=False
        try:
            import mediapipe as mp; self._pose=mp.solutions.pose.Pose(static_image_mode=False); self._ok=True
        except ImportError: logger.warning("mediapipe não instalado.")

    @staticmethod
    def _angulo(a,b,c):
        ba=a-b; bc=c-b
        return float(np.degrees(np.arccos(np.clip(np.dot(ba,bc)/(np.linalg.norm(ba)*np.linalg.norm(bc)+1e-9),-1,1))))

    def angulo_quadril_joelho(self, frame_rgb):
        if not self._ok: return None
        r=self._pose.process(frame_rgb)
        if not r.pose_landmarks: return None
        lm=r.pose_landmarks.landmark
        return self._angulo(np.array([lm[11].x,lm[11].y]),np.array([lm[23].x,lm[23].y]),np.array([lm[25].x,lm[25].y]))

    def avaliar_sessao(self, angulos, exercicio):
        esp=AMPLITUDE_ESPERADA.get(exercicio,90.)
        if not angulos: return {"amplitude_maxima":0.,"percentual_recuperacao":0.}
        mx=float(max(angulos))
        return {"amplitude_maxima":mx,"percentual_recuperacao":round(float(np.clip(mx/esp,0,1.5))*100,1)}
