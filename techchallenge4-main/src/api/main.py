"""
API FastAPI — entrada da aplicação.
Compatível com Azure App Service (Python 3.12).
"""
from __future__ import annotations
import logging
import shutil
import tempfile
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # carrega .env localmente; no Azure usa App Settings

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from src.api.dashboard import router as dashboard_router
from src.audio.audio_pipeline import PipelineAudio
from src.database.db import init_db
from src.database.seed import seed
from src.fusion.alert_engine import MotorDeAlertas
from src.fusion.multimodal_fusion import MotorFusaoMultimodal
from src.models.schemas import ContextoClinico, LeituraVital, ResultadoAudio, ResultadoFusao, ResultadoVideo, ResultadoVitais
from src.vitals.anomaly_detector import DetectorAnomaliasVitais
from src.video.video_pipeline import PipelineVideo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IA Multimodal — Saúde da Mulher",
    description="Fusão de vídeo, áudio e sinais vitais para detecção precoce de riscos em saúde feminina.",
    version="0.2.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(dashboard_router)

FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "index.html"

_pipeline_video  = PipelineVideo()
_pipeline_audio  = PipelineAudio()
_detector_vitais = DetectorAnomaliasVitais()
_motor_fusao     = MotorFusaoMultimodal()
_motor_alertas   = MotorDeAlertas()
_CACHE: dict[str, dict] = {}


@app.on_event("startup")
async def startup():
    init_db()
    seed()
    logger.info("Banco inicializado. DB: %s", __import__('src.database.db', fromlist=['DB_PATH']).DB_PATH)


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(FRONTEND) if FRONTEND.exists() else {"status": "frontend não encontrado"}


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.2.0"}


@app.post("/analyze/video", response_model=ResultadoVideo)
async def analisar_video(paciente_id: str, contexto: ContextoClinico, arquivo: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(arquivo.filename).suffix) as tmp:
        shutil.copyfileobj(arquivo.file, tmp)
    try:
        resultado = _pipeline_video.processar(tmp.name, paciente_id, contexto)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    _CACHE.setdefault(paciente_id, {})["video"] = resultado
    return resultado


@app.post("/analyze/audio", response_model=ResultadoAudio)
async def analisar_audio(paciente_id: str, contexto: ContextoClinico, arquivo: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(arquivo.filename).suffix) as tmp:
        shutil.copyfileobj(arquivo.file, tmp)
    try:
        resultado = _pipeline_audio.processar(tmp.name, paciente_id, contexto)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    _CACHE.setdefault(paciente_id, {})["audio"] = resultado
    return resultado


@app.post("/vitals/reading", response_model=ResultadoVitais)
async def registrar_vital(leitura: LeituraVital):
    resultado = _detector_vitais.avaliar(leitura)
    _CACHE.setdefault(leitura.paciente_id, {})["vitais"] = resultado
    return resultado


@app.post("/fusion/{paciente_id}", response_model=ResultadoFusao)
async def fundir(paciente_id: str):
    dados = _CACHE.get(paciente_id, {})
    if not dados:
        raise HTTPException(status_code=404, detail="Sem dados em cache para este paciente.")
    fusao = _motor_fusao.fundir(paciente_id=paciente_id, **{k: v for k, v in dados.items()})
    _motor_alertas.despachar(_motor_alertas.gerar_alertas(fusao))
    return fusao
