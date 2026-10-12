"""API REST (FastAPI) com JWT e RBAC. Execução: uvicorn guardia.api:app"""
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from . import auth, db, graph
from .ml.features import feature_names
from .predictor import InputError, get_predictor

app = FastAPI(title="Guardiã AI", version="1.0", description="Apoio à triagem de risco de câncer de mama (uso por profissionais).")
auth.bootstrap_admin()


def current_user(authorization: str = Header(default="")) -> dict:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Token ausente.")
    try:
        return auth.user_from_token(authorization[7:])
    except auth.AuthError as e:
        raise HTTPException(401, str(e))


def _wrap(fn, *a, **k):
    try:
        return fn(*a, **k)
    except auth.Forbidden as e:
        raise HTTPException(403, str(e))
    except (InputError, auth.AuthError) as e:
        raise HTTPException(422, str(e))


class Login(BaseModel):
    username: str
    password: str


class AnalysisIn(BaseModel):
    case_identifier: str = Field(min_length=1, max_length=64)
    features: dict[str, float]
    relato: str = Field(default="", max_length=4000)


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=600)


class ReviewIn(BaseModel):
    decision: str
    notes: str = ""
    crm: str = ""


class UserIn(BaseModel):
    username: str
    full_name: str
    password: str
    role: str


@app.get("/health")
def health():
    return {"status": "ok", "model": get_predictor().version}


@app.post("/auth/login")
def login(b: Login):
    try:
        u = auth.authenticate(b.username, b.password)
    except auth.AuthError as e:
        raise HTTPException(401, str(e))
    return {"access_token": auth.issue_token(u), "token_type": "bearer", "role": u["role"]}


@app.get("/model/features")
def features(u: dict = Depends(current_user)):
    return feature_names()


@app.post("/analyses")
def create_analysis(b: AnalysisIn, u: dict = Depends(current_user)):
    o = _wrap(graph.run_analysis, u, b.case_identifier, b.features, b.relato)
    return {"analysis_id": o["analysis_id"], "risk_band": o["pred"]["band"], "probability": o["pred"]["probability"],
            "contributions": o["pred"]["contributions"], "sources": [d["source"] for d in o["docs"]],
            "explanation": o["explanation"], "flags": o["flags"], "provider": o["provider"]}


@app.get("/analyses")
def analyses(u: dict = Depends(current_user)):
    return [{k: r[k] for k in ("id", "created_at", "username", "case_ref", "risk_band", "probability", "decision")}
            for r in _wrap(graph.list_analyses, u)]


@app.post("/analyses/{aid}/review")
def review(aid: int, b: ReviewIn, u: dict = Depends(current_user)):
    _wrap(graph.review, u, aid, b.decision, b.notes, b.crm)
    return {"ok": True}


@app.post("/ask")
def ask(b: AskIn, u: dict = Depends(current_user)):
    return _wrap(graph.ask, u, b.question)


@app.get("/audit")
def audit(u: dict = Depends(current_user)):
    _wrap(auth.require, u, "view_audit")
    ok, bad = db.verify_audit_chain()
    with db.conn() as c:
        rows = [dict(r) for r in c.execute("SELECT id,ts,actor,action,detail FROM audit ORDER BY id DESC LIMIT 200")]
    return {"chain_ok": ok, "first_bad_id": bad, "events": rows}


@app.post("/users")
def new_user(b: UserIn, u: dict = Depends(current_user)):
    _wrap(auth.require, u, "manage_users")
    return {"id": _wrap(auth.create_user, b.username, b.full_name, b.password, b.role, u["username"])}
