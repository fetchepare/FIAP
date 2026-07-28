from __future__ import annotations
import logging, os
import numpy as np
logger=logging.getLogger(__name__)
CLASSES_INSTRUMENTOS=["pinca_ginecologica","especulo","sugador","bisturi","porta_agulha","tesoura_cirurgica"]
CLASSES_AREAS_CRITICAS=["utero","ovario","mama"]
PESOS_CUSTOMIZADOS=os.getenv("YOLO_GINECOLOGIA_WEIGHTS","pesos/ginecologia-yolov8.pt")
MODELO_BASE="yolov8n.pt"

from dataclasses import dataclass
@dataclass
class DeteccaoFrame:
    classe: str; confianca: float; bbox: tuple[float,float,float,float]

class DetectorCirurgicoGinecologico:
    def __init__(self):
        self._modelo=None
        try:
            from ultralytics import YOLO
            if os.path.exists(PESOS_CUSTOMIZADOS): self._modelo=YOLO(PESOS_CUSTOMIZADOS)
            else:
                logger.warning("Pesos customizados não encontrados — usando modelo base '%s'.",MODELO_BASE)
                self._modelo=YOLO(MODELO_BASE)
        except ImportError:
            logger.warning("ultralytics não instalado — detector YOLO desabilitado.")

    def detectar(self, frame: np.ndarray) -> list[DeteccaoFrame]:
        if self._modelo is None: return []
        res=self._modelo.predict(frame,verbose=False)
        return [DeteccaoFrame(r.names.get(int(b.cls[0]),str(int(b.cls[0]))),float(b.conf[0]),tuple(float(v) for v in b.xyxyn[0])) for r in res for b in r.boxes]

    def estimar_score_sangramento(self, frame: np.ndarray, roi=None) -> float:
        try: import cv2
        except ImportError: return 0.0
        h,w=frame.shape[:2]
        rec=frame[int(roi[1]*h):int(roi[3]*h),int(roi[0]*w):int(roi[2]*w)] if roi else frame
        if rec.size==0: return 0.0
        hsv=cv2.cvtColor(rec,cv2.COLOR_BGR2HSV)
        m=cv2.bitwise_or(cv2.inRange(hsv,(0,90,60),(10,255,255)),cv2.inRange(hsv,(170,90,60),(180,255,255)))
        return float(np.count_nonzero(m))/float(m.size)
