from __future__ import annotations
import logging
import numpy as np
from collections import deque
from dataclasses import dataclass, field
logger=logging.getLogger(__name__)

@dataclass
class EstadoTemporal:
    janela: deque = field(default_factory=lambda: deque(maxlen=10))

class AnalisadorNaoVerbal:
    def __init__(self):
        self._ok=False; self._estado=EstadoTemporal()
        try:
            import mediapipe as mp
            self._face=mp.solutions.face_mesh.FaceMesh(static_image_mode=False,max_num_faces=1,refine_landmarks=True)
            self._pose=mp.solutions.pose.Pose(static_image_mode=False); self._ok=True
        except ImportError:
            logger.warning("mediapipe não instalado — AnalisadorNaoVerbal retornará scores zero.")

    def processar_frame(self, frame_rgb: np.ndarray) -> dict[str,float]:
        if not self._ok: return {"desconforto":0.,"autoprotecao":0.,"evitacao_olhar":0.,"sobressalto":0.}
        scores={"desconforto":0.,"autoprotecao":0.,"evitacao_olhar":0.,"sobressalto":0.}
        r=self._pose.process(frame_rgb)
        if r.pose_landmarks:
            lm=r.pose_landmarks.landmark
            p1=np.array([lm[15].x,lm[15].y]); p2=np.array([lm[16].x,lm[16].y])
            o1=np.array([lm[11].x,lm[11].y]); o2=np.array([lm[12].x,lm[12].y])
            scores["autoprotecao"]=float(np.clip(1-min(np.linalg.norm(p1-o2),np.linalg.norm(p2-o1))*4,0,1))
            nariz=np.array([lm[0].x,lm[0].y]); self._estado.janela.append(nariz)
            if len(self._estado.janela)>=3:
                pos=np.array(self._estado.janela); acc=np.diff(np.diff(pos,axis=0),axis=0)
                scores["sobressalto"]=float(np.clip(np.max(np.linalg.norm(acc,axis=1))*50,0,1))
        r2=self._face.process(frame_rgb)
        if r2.multi_face_landmarks:
            fl=r2.multi_face_landmarks[0].landmark
            sb1=np.array([fl[55].x,fl[55].y]); sb2=np.array([fl[285].x,fl[285].y])
            scores["desconforto"]=float(np.clip(1-np.linalg.norm(sb1-sb2)*8,0,1))
            nariz=np.array([fl[1].x,fl[1].y]); centro=(np.array([fl[234].x,fl[234].y])+np.array([fl[454].x,fl[454].y]))/2
            scores["evitacao_olhar"]=float(np.clip(np.linalg.norm(nariz-centro)*6,0,1))
        return scores
