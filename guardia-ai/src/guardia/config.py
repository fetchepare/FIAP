"""Configuração central. Tudo sobrescrevível por variáveis de ambiente."""
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("GUARDIA_DATA_DIR", ROOT / "data"))
MODEL_DIR = Path(os.getenv("GUARDIA_MODEL_DIR", ROOT / "models"))
KB_DIR = Path(os.getenv("GUARDIA_KB_DIR", ROOT / "data" / "kb"))
REPORT_DIR = ROOT / "reports"
DB_PATH = Path(os.getenv("GUARDIA_DB", DATA_DIR / "guardia.db"))

LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-5-5")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "30"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

JWT_ALG = "HS256"
JWT_TTL_MIN = int(os.getenv("GUARDIA_JWT_TTL_MIN", "30"))
SESSION_IDLE_MIN = int(os.getenv("GUARDIA_SESSION_IDLE_MIN", "30"))
MAX_FAILED = int(os.getenv("GUARDIA_MAX_FAILED", "5"))
LOCK_MIN = int(os.getenv("GUARDIA_LOCK_MIN", "15"))
RAG_MIN_SCORE = float(os.getenv("GUARDIA_RAG_MIN_SCORE", "0.08"))


def get_secret() -> str:
    """Segredo para JWT/HMAC. Se não vier por env, é gerado e persistido (0600)."""
    env = os.getenv("GUARDIA_SECRET")
    if env:
        return env
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    f = DATA_DIR / ".secret"
    if not f.exists():
        f.write_text(secrets.token_hex(32))
        os.chmod(f, 0o600)
    return f.read_text().strip()
