"""Fluxo principal em LangGraph:
validar → modelo (ML+SHAP) → achados do relato → RAG → LLM → guardrails de saída → persistir (auditoria)."""
import hashlib
import hmac
import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from . import auth, config, db, guardrails
from .llm import get_llm
from .predictor import InputError, get_predictor
from .rag import get_retriever

BAND_TXT = {"baixo": "BAIXO (abaixo do limiar de segurança do modelo)",
            "intermediário": "INTERMEDIÁRIO (acima do limiar de segurança, abaixo do limiar de alta suspeita)",
            "alto": "ALTO (acima do limiar de alta suspeita)"}


class State(TypedDict, total=False):
    user: dict
    case_ref: str
    features: dict
    relato: str
    errors: list
    flags: list
    pred: dict
    red_flags: list
    docs: list
    prompt: str
    offline: str
    explanation: str
    provider: str
    analysis_id: int


def pseudonymize(identifier: str) -> str:
    """HMAC do identificador informado: o sistema nunca guarda o identificador em claro."""
    return hmac.new(config.get_secret().encode(), identifier.strip().lower().encode(), hashlib.sha256).hexdigest()[:16]


def n_validate(s: State) -> State:
    p = get_predictor()
    flags = list(s.get("flags", []))
    try:
        clean, warns = p.validate(s["features"])
    except InputError as e:
        return {"errors": [str(e)]}
    relato, f2 = guardrails.sanitize_text(s.get("relato", ""))
    return {"features": clean, "relato": relato, "flags": flags + warns + f2, "errors": []}


def n_model(s: State) -> State:
    return {"pred": get_predictor().predict(s["features"])}


def n_findings(s: State) -> State:
    return {"red_flags": guardrails.extract_red_flags(s.get("relato", ""))}


def _query(s: State) -> str:
    q = ["avaliação risco câncer de mama limites da IA decisão final", f"risco {s['pred']['band']}"]
    q += [r for r in s.get("red_flags", [])]
    if s["pred"]["band"] != "baixo":
        q.append("priorizar encaminhamento exame de imagem biópsia")
    return " ".join(q)


def n_retrieve(s: State) -> State:
    return {"docs": get_retriever().search(_query(s), k=4)}


def _offline_text(s: State) -> str:
    p = s["pred"]
    top = "; ".join(f"{c['label']} ({'↑' if c['shap'] > 0 else '↓'})" for c in p["contributions"][:4])
    lines = [f"**Resultado do modelo:** risco {BAND_TXT[p['band']]}; probabilidade estimada de {p['probability']:.1%} "
             f"(limiar de segurança {p['threshold']:.2f}).",
             f"**Variáveis que mais influenciaram:** {top}."]
    if s.get("red_flags"):
        lines.append("**Sinais de atenção no relato:** " + ", ".join(s["red_flags"]) + ".")
    else:
        lines.append("**Relato:** nenhum sinal de alerta identificado automaticamente (isso não exclui achados clínicos).")
    strong = [r for r in s.get("red_flags", []) if r not in ("dor mamária", "histórico familiar relevante")]
    if p["band"] == "baixo" and strong:
        lines.append("**Atenção – divergência modelo × relato:** o modelo indica baixo risco, mas o relato contém sinal de alerta clínico. "
                     "O relato deve prevalecer: considerar avaliação clínica e exame de imagem conforme protocolo.")
    elif p["band"] == "baixo":
        lines.append("**Sugestão de apoio:** seguir o fluxo de rotina, ressalvando que baixo risco não exclui doença; "
                     "reavaliar se houver sinais clínicos.")
    else:
        lines.append("**Sugestão de apoio:** considerar priorizar a investigação complementar (exame de imagem e, se indicado, biópsia) "
                     "conforme protocolo local.")
    if s.get("docs"):
        lines.append("**Fontes consultadas:** " + ", ".join(f"[{x}]" for x in dict.fromkeys(d["source"] for d in s["docs"])) + ".")
    else:
        lines.append("**Fontes:** não há base de conhecimento suficiente para sustentar uma orientação adicional.")
    if "POSSIVEL_INJECAO_DE_PROMPT" in s.get("flags", []):
        lines.append("**Atenção:** o relato continha trechos que parecem instruções; foram tratados apenas como texto.")
    return "\n\n".join(lines)


def n_generate(s: State) -> State:
    docs = "\n".join(f"[{d['source']} – {d['section']}] {d['text']}" for d in s.get("docs", [])) or "(nenhum documento relevante)"
    p = s["pred"]
    prompt = (f"<resultado_modelo>risco={p['band']}; probabilidade={p['probability']:.3f}; limiar={p['threshold']:.2f}; "
              f"variáveis_mais_influentes={[(c['label'], round(c['shap'], 2)) for c in p['contributions'][:5]]}</resultado_modelo>\n"
              f"<relato>{s.get('relato') or '(sem relato)'}</relato>\n<sinais_no_relato>{s.get('red_flags')}</sinais_no_relato>\n"
              f"<documentos>\n{docs}\n</documentos>\n\nProduza: 1) resumo do caso; 2) leitura do resultado do modelo; "
              f"3) sugestões de próximos passos para o profissional (sem decidir); 4) fontes citadas.")
    off = _offline_text(s)
    txt, prov = get_llm().generate(prompt, off)
    return {"prompt": prompt, "offline": off, "explanation": txt, "provider": prov}


def n_guard(s: State) -> State:
    txt, f = guardrails.check_output(s["explanation"], s["offline"])
    return {"explanation": txt, "flags": s.get("flags", []) + [f"SAIDA_BLOQUEADA:{x}" for x in f]}


def n_persist(s: State) -> State:
    p, u = s["pred"], s["user"]
    with db.conn() as c:
        cur = c.execute(
            """INSERT INTO analyses(created_at,user_id,case_ref,input_json,relato,probability,threshold,risk_band,
               contributions_json,sources_json,explanation,llm_provider,model_version,flags_json)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (db.now(), u["id"], s["case_ref"], json.dumps(s["features"]), s.get("relato", ""), p["probability"], p["threshold"],
             p["band"], json.dumps(p["contributions"], ensure_ascii=False),
             json.dumps([{k: d[k] for k in ("source", "section", "score")} for d in s.get("docs", [])]),
             s["explanation"], s["provider"], get_predictor().version, json.dumps(s.get("flags", []))))
        aid = cur.lastrowid
    db.audit(u["username"], "ANALYSIS_CREATED", {"analysis_id": aid, "case_ref": s["case_ref"], "band": p["band"],
                                                   "model": get_predictor().version, "provider": s["provider"],
                                                   "sources": [d["source"] for d in s.get("docs", [])], "flags": s.get("flags", [])})
    return {"analysis_id": aid}


def _build():
    g = StateGraph(State)
    for name, fn in [("validate", n_validate), ("model", n_model), ("findings", n_findings), ("retrieve", n_retrieve),
                     ("generate", n_generate), ("guard", n_guard), ("persist", n_persist)]:
        g.add_node(name, fn)
    g.set_entry_point("validate")
    g.add_conditional_edges("validate", lambda s: "stop" if s.get("errors") else "go", {"stop": END, "go": "model"})
    for a, b in [("model", "findings"), ("findings", "retrieve"), ("retrieve", "generate"), ("generate", "guard"),
                 ("guard", "persist"), ("persist", END)]:
        g.add_edge(a, b)
    return g.compile()


_GRAPH = None


def run_analysis(user: dict, case_identifier: str, features: dict, relato: str = "") -> dict[str, Any]:
    global _GRAPH
    auth.require(user, "analyze")
    if not case_identifier.strip():
        raise InputError("Informe um identificador (pseudônimo) do caso.")
    _GRAPH = _GRAPH or _build()
    out = _GRAPH.invoke({"user": user, "case_ref": pseudonymize(case_identifier), "features": features, "relato": relato})
    if out.get("errors"):
        db.audit(user["username"], "ANALYSIS_REJECTED", {"errors": out["errors"]})
        raise InputError(" ".join(out["errors"]))
    return out


def ask(user: dict, question: str) -> dict:
    """Assistente de perguntas sobre protocolos (RAG + LLM + guardrails)."""
    auth.require(user, "ask")
    q, f = guardrails.sanitize_text(question, 600)
    if not q:
        raise InputError("Pergunta vazia.")
    docs = get_retriever().search(q, k=3)
    if docs:
        ctx = "\n".join(f"[{d['source']} – {d['section']}] {d['text']}" for d in docs)
        off = "**Com base nos documentos cadastrados:**\n\n" + "\n\n".join(f"• {d['text']}  \n  _Fonte: [{d['source']}] – {d['section']}_" for d in docs[:2])
    else:
        ctx = "(nenhum documento relevante)"
        off = "Não encontrei base suficiente nos documentos cadastrados para responder. Consulte o protocolo oficial ou um especialista."
    prompt = f"<pergunta>{q}</pergunta>\n<documentos>\n{ctx}\n</documentos>\nResponda só com base nos documentos e cite as fontes."
    txt, prov = get_llm().generate(prompt, off) if docs else (off, "offline")
    txt, bf = guardrails.check_output(txt, off)
    db.audit(user["username"], "QUESTION_ASKED", {"q": q[:200], "sources": [d["source"] for d in docs], "provider": prov, "flags": f + bf})
    return {"answer": txt, "docs": docs, "provider": prov, "flags": f + bf}


def review(user: dict, analysis_id: int, decision: str, notes: str = "", crm: str = "") -> None:
    auth.require(user, "review")
    decision = (decision or "").strip()
    if not decision or len(decision) > 150:
        raise InputError("Decisão inválida.")
    notes_clean = (notes or "").strip()[:1000]
    if crm and crm.strip():
        notes_clean = f"[Responsável: {crm.strip()}] {notes_clean}".strip()
    with db.conn() as c:
        if not c.execute("SELECT 1 FROM analyses WHERE id=?", (analysis_id,)).fetchone():
            raise InputError("Análise inexistente.")
        c.execute("INSERT INTO reviews(analysis_id,user_id,decision,notes,created_at) VALUES(?,?,?,?,?)",
                  (analysis_id, user["id"], decision, notes_clean, db.now()))
    db.audit(user["username"], "HUMAN_REVIEW", {
        "analysis_id": analysis_id,
        "decision": decision,
        "crm": crm.strip() if crm else "",
        "principle": "A decisão final sempre deverá permanecer com uma pessoa responsável pelo atendimento."
    })


def list_analyses(user: dict, limit: int = 100) -> list[dict]:
    with db.conn() as c:
        query_cols = """a.*, u.username,
                        (SELECT decision FROM reviews r WHERE r.analysis_id=a.id ORDER BY r.id DESC LIMIT 1) decision,
                        (SELECT notes FROM reviews r WHERE r.analysis_id=a.id ORDER BY r.id DESC LIMIT 1) review_notes,
                        (SELECT created_at FROM reviews r WHERE r.analysis_id=a.id ORDER BY r.id DESC LIMIT 1) reviewed_at"""
        if auth.can(user["role"], "view_all"):
            rows = c.execute(f"SELECT {query_cols} FROM analyses a JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT ?", (limit,)).fetchall()
        else:
            auth.require(user, "view_own")
            rows = c.execute(f"SELECT {query_cols} FROM analyses a JOIN users u ON u.id=a.user_id WHERE a.user_id=? ORDER BY a.id DESC LIMIT ?",
                             (user["id"], limit)).fetchall()
    return [dict(r) for r in rows]
