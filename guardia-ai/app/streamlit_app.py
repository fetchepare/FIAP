"""Guardiã AI – interface Streamlit (login, RBAC, análise, assistente RAG, histórico, administração, auditoria)."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
import pandas as pd
import streamlit as st

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from guardia import auth, config, db, graph  # noqa: E402
from guardia.guardrails import DISCLAIMER  # noqa: E402
from guardia.ml.features import BASE, BASE_PT, GROUPS, feature_names, label_pt  # noqa: E402
from guardia.ml.train import load_data  # noqa: E402
from guardia.predictor import InputError, get_predictor  # noqa: E402

st.set_page_config(page_title="Guardiã AI", page_icon="🛡️", layout="wide")


@st.cache_resource
def _boot():
    return auth.bootstrap_admin()


first_pw = _boot()


@st.cache_data
def _examples():
    X, y = load_data()
    return X, y


def logout():
    for k in ("user", "last_seen", "result"):
        st.session_state.pop(k, None)


def login_view():
    st.title("🛡️ Guardiã AI")
    st.caption("Apoio à triagem de risco de câncer de mama — uso restrito a profissionais autorizados.")
    if first_pw:
        st.warning(f"Primeiro acesso: usuário **admin**, senha gerada **{first_pw}** (anote e troque criando outros usuários).")
    with st.form("login"):
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar", type="primary"):
            try:
                st.session_state.user = auth.authenticate(u, p)
                st.session_state.last_seen = time.time()
                st.rerun()
            except auth.AuthError as e:
                st.error(str(e))
    st.info(DISCLAIMER)


def band_badge(band):
    return {"baixo": "🟢 BAIXO", "intermediário": "🟡 INTERMEDIÁRIO", "alto": "🔴 ALTO"}[band]


def plot_contrib(contribs, title="Contribuição de cada variável (SHAP)"):
    c = contribs[:8][::-1]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.barh([x["label"] for x in c], [x["shap"] for x in c], color=["#c2185b" if x["shap"] > 0 else "#1f4e79" for x in c])
    ax.axvline(0, color="k", lw=0.6); ax.set_xlabel("← reduz suspeita | aumenta suspeita →"); ax.set_title(title, fontsize=9)
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)
    st.caption("O SHAP explica o comportamento do modelo, não a causa clínica. Variáveis correlacionadas dividem a contribuição.")


def show_result(o):
    p = o["pred"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Faixa de risco", band_badge(p["band"]))
    c2.metric("Probabilidade estimada", f"{p['probability']:.1%}")
    c3.metric("Limiar de segurança", f"{p['threshold']:.2f}")
    if o.get("flags"):
        st.warning("Alertas de qualidade/segurança: " + ", ".join(o["flags"]))
    left, right = st.columns([1, 1])
    with left:
        plot_contrib(p["contributions"])
    with right:
        st.markdown("#### Análise assistida (LLM + RAG)")
        st.markdown(o["explanation"])
        st.caption(f"Provedor: {o['provider']} · Modelo: {get_predictor().version} · Análise #{o['analysis_id']}")
    with st.expander("📚 Trechos recuperados (fontes do RAG)"):
        for d in o["docs"]:
            st.markdown(f"**{d['source']}** — _{d['section']}_ (similaridade {d['score']})\n\n{d['text']}")


def view_new(user):
    pred = get_predictor()
    X, y = _examples()
    st.header("Nova análise")
    st.info(DISCLAIMER)
    ex = st.radio("Preencher com exemplo do dataset público (WDBC)?", ["Não", "Exemplo benigno", "Exemplo maligno"], horizontal=True)
    base = {f: float(X[f].median()) for f in X.columns}
    if ex != "Não":
        idx = int(y[y == (1 if "maligno" in ex else 0)].index[3]) if ex else 0
        base = X.loc[idx].to_dict()
    cid = st.text_input("Identificador pseudonimizado do caso (não use nome/CPF)", max_chars=64)
    vals = {}
    tabs = st.tabs([f"{gp.capitalize()}" for _, gp in GROUPS])
    for (g, _), tab in zip(GROUPS, tabs):
        with tab:
            cols = st.columns(5)
            for i, (b, bp) in enumerate(zip(BASE, BASE_PT)):
                f = f"{g} {b}"
                vals[f] = cols[i % 5].number_input(bp.capitalize(), min_value=0.0, value=round(float(base[f]), 5), format="%.5f", key=f"{f}-{ex}")
    relato = st.text_area("Relato do atendimento (texto livre; CPF/e-mail/telefone são mascarados automaticamente)", height=110, max_chars=4000)
    if st.button("Analisar", type="primary"):
        try:
            with st.spinner("Executando fluxo: modelo → SHAP → RAG → LLM → guardrails…"):
                st.session_state.result = graph.run_analysis(user, cid, vals, relato)
        except (InputError, auth.Forbidden) as e:
            st.error(str(e))
    o = st.session_state.get("result")
    if o:
        st.divider(); show_result(o)
        if auth.can(user["role"], "review"):
            st.markdown("---")
            st.markdown("### ⚖️ Decisão Final do(a) Médico(a) / Responsável pelo Atendimento")
            st.info(
                "📌 **Diretriz de Segurança e Governança:**  \n"
                "**\"A decisão final sempre deverá permanecer com uma pessoa responsável pelo atendimento.\"**  \n\n"
                "A Guardiã AI funciona estritamente como um sistema de suporte à triagem. "
                "A avaliação clínica, a definição diagnóstica e a conduta terapêutica são de responsabilidade "
                "exclusiva e indelegável do(a) médico(a) ou profissional de saúde responsável."
            )
            with db.conn() as _c:
                existing_rev = _c.execute(
                    "SELECT r.*, u.full_name FROM reviews r JOIN users u ON u.id=r.user_id WHERE r.analysis_id=? ORDER BY r.id DESC LIMIT 1",
                    (o["analysis_id"],)
                ).fetchone()

            if existing_rev:
                st.success(
                    f"✅ **Decisão médica já homologada para este caso:**  \n"
                    f"• **Parecer Clínico:** `{existing_rev['decision']}`  \n"
                    f"• **Profissional Responsável:** {existing_rev['full_name']} em {existing_rev['created_at']}  \n"
                    f"• **Conduta Registrada:** {existing_rev['notes'] or 'Sem observações adicionais.'}"
                )
            else:
                with st.form("form_decisao_medica"):
                    col_d1, col_d2 = st.columns([2, 1])
                    with col_d1:
                        d_tipo = st.selectbox(
                            "Parecer / Decisão Clínica do(a) Profissional:",
                            [
                                "Concordo com a análise — Investigação prioritária (Alto Risco)",
                                "Concordo com a análise — Seguimento de rotina (Baixo Risco)",
                                "Discordo da análise — Reclassificação clínica pelo(a) médico(a)",
                                "Solicitação de exames complementares (Mamografia / USG / Biópsia)",
                                "Preciso de mais informações — Avaliação presencial complementar",
                                "Concordo com a análise",
                                "Discordo da análise",
                                "Outra conduta personalizada",
                            ],
                            key="dec_tipo",
                        )
                        d_custom = ""
                        if d_tipo == "Outra conduta personalizada":
                            d_custom = st.text_input("Especifique a conduta clínica:", key="dec_custom")
                    with col_d2:
                        crm = st.text_input("CRM / Registro Profissional:", placeholder="Ex.: CRM/SP 123456", key="crm_input")

                    n = st.text_area(
                        "Conduta médica, justificativa e orientações ao paciente:",
                        placeholder="Ex.: Paciente acolhida. Indicado encaminhamento prioritário ao mastologista para biópsia e mamografia diagnóstica bilateral...",
                        key="notes",
                        max_chars=1000,
                        height=90,
                    )
                    term_ack = st.checkbox(
                        "Declaro que revisei os achados e que a decisão final sempre deverá permanecer com uma pessoa responsável pelo atendimento.",
                        value=True,
                        key="term_ack",
                    )
                    sub = st.form_submit_button("🩺 Gravar Decisão Médica Final", type="primary")
                    if sub:
                        if not term_ack:
                            st.error("É obrigatório confirmar a ciência de que a decisão final permanece com o profissional responsável.")
                        else:
                            d_final = d_custom.strip() if d_tipo == "Outra conduta personalizada" and d_custom.strip() else d_tipo
                            graph.review(user, o["analysis_id"], d_final, n, crm=crm)
                            st.success("✅ Decisão médica registrada com sucesso e gravada na trilha de auditoria encadeada!")
                            st.rerun()


def view_ask(user):
    st.header("Assistente de protocolos (RAG)")
    q = st.text_input("Pergunte sobre rastreamento, sinais de alerta, BI-RADS, limites da IA…")
    if q:
        try:
            r = graph.ask(user, q)
            st.markdown(r["answer"]); st.caption(f"Provedor: {r['provider']}")
            with st.expander("Fontes"):
                for d in r["docs"]:
                    st.markdown(f"**{d['source']}** — {d['section']} ({d['score']})")
        except InputError as e:
            st.error(str(e))


def view_history(user):
    st.header("Histórico de análises")
    rows = graph.list_analyses(user)
    if not rows:
        st.write("Nenhuma análise registrada."); return
    for row in rows:
        row["status_decisao"] = f"✅ {row['decision']}" if row.get("decision") else "⏳ Pendente de decisão médica"
    df = pd.DataFrame(rows)[["id", "created_at", "username", "case_ref", "risk_band", "probability", "status_decisao", "llm_provider"]]
    df = df.rename(columns={"status_decisao": "Decisão Médica", "created_at": "Data/Hora", "risk_band": "Faixa", "probability": "Probabilidade"})
    st.dataframe(df, use_container_width=True, hide_index=True)
    sel = st.selectbox("Abrir análise #", [r["id"] for r in rows])
    r = next(x for x in rows if x["id"] == sel)
    
    st.markdown("---")
    st.markdown(f"### Detalhes do Caso #{r['id']} (Ref: `{r['case_ref']}`)")
    if r.get("decision"):
        st.success(
            f"**✅ Decisão Médica Registrada:** {r['decision']}  \n"
            f"**Conduta / Notas:** {r.get('review_notes') or 'Nenhuma observação.'}  \n"
            f"**Data da Homologação:** {r.get('reviewed_at')}"
        )
    else:
        st.warning("⚠️ **Caso pendente de decisão médica:** A decisão final sempre deverá permanecer com uma pessoa responsável pelo atendimento.")
        if auth.can(user["role"], "review"):
            with st.expander("🩺 Registrar Decisão Médica para este caso"):
                with st.form(f"form_hist_rev_{r['id']}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        d_tipo_h = st.selectbox(
                            "Decisão Clínica:",
                            [
                                "Concordo com a análise — Investigação prioritária (Alto Risco)",
                                "Concordo com a análise — Seguimento de rotina (Baixo Risco)",
                                "Discordo da análise — Reclassificação clínica pelo(a) médico(a)",
                                "Solicitação de exames complementares (Mamografia / USG / Biópsia)",
                                "Preciso de mais informações — Avaliação presencial complementar",
                                "Concordo com a análise",
                                "Discordo da análise",
                            ],
                            key=f"dec_h_{r['id']}",
                        )
                    with c2:
                        crm_h = st.text_input("CRM / Registro:", placeholder="Ex: CRM/SP 123456", key=f"crm_h_{r['id']}")
                    nh = st.text_area("Conduta clínica e justificativa:", key=f"notes_h_{r['id']}")
                    if st.form_submit_button("Salvar Decisão Médica"):
                        graph.review(user, r["id"], d_tipo_h, nh, crm=crm_h)
                        st.success("Decisão gravada na trilha de auditoria!")
                        st.rerun()

    st.markdown(r["explanation"]); plot_contrib(json.loads(r["contributions_json"]))
    st.caption(f"Flags: {r['flags_json']} · Fontes: {r['sources_json']} · Modelo {r['model_version']}")


def view_admin(user):
    auth.require(user, "manage_users")
    st.header("Administração de usuários")
    with st.form("nu"):
        c = st.columns(4)
        un, fn, pw, rl = c[0].text_input("Usuário"), c[1].text_input("Nome"), c[2].text_input("Senha", type="password"), c[3].selectbox("Perfil", ["profissional", "auditor", "admin"])
        if st.form_submit_button("Criar"):
            try:
                auth.create_user(un, fn, pw, rl, actor=user["username"]); st.success("Usuário criado.")
            except auth.AuthError as e:
                st.error(str(e))
    with db.conn() as cn:
        st.dataframe(pd.DataFrame([dict(r) for r in cn.execute("SELECT username,full_name,role,active,created_at FROM users")]), hide_index=True)


def view_audit(user):
    auth.require(user, "view_audit")
    st.header("Trilha de auditoria")
    ok, bad = db.verify_audit_chain()
    st.success("Cadeia de hashes íntegra ✔") if ok else st.error(f"Cadeia ADULTERADA a partir do registro {bad}")
    with db.conn() as cn:
        st.dataframe(pd.DataFrame([dict(r) for r in cn.execute("SELECT id,ts,actor,action,detail FROM audit ORDER BY id DESC LIMIT 300")]), use_container_width=True, hide_index=True)


def view_model(user):
    st.header("Modelo e métricas")
    m = json.loads((config.MODEL_DIR / "metrics.json").read_text())
    st.write(f"Modelo em produção: **{m['final']['chosen']}** · limiar de segurança {m['final']['t_low']:.2f} · alto risco ≥ {m['final']['t_high']:.2f}")
    st.dataframe(pd.DataFrame({k: v["cv"] for k, v in m["results"].items()}).T[["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]].round(3))
    t = m["test_final"]; st.write(f"Teste no limiar operacional → recall {t['recall']:.3f} · precisão {t['precision']:.3f} · FN={t['fn']} · FP={t['fp']}")
    for f in ("04_modelos_cv", "07_confusao", "09_shap_global"):
        p = config.REPORT_DIR / "figures" / f"{f}.png"
        if p.exists():
            st.image(str(p))


# ---------------- main ----------------
user = st.session_state.get("user")
if user and time.time() - st.session_state.get("last_seen", 0) > config.SESSION_IDLE_MIN * 60:
    db.audit(user["username"], "SESSION_EXPIRED"); logout(); user = None; st.warning("Sessão expirada por inatividade.")
if not user:
    login_view(); st.stop()
st.session_state.last_seen = time.time()

pages = {}
if auth.can(user["role"], "analyze"): pages["🩺 Nova análise"] = view_new
if auth.can(user["role"], "ask"): pages["💬 Assistente"] = view_ask
pages["🗂️ Histórico"] = view_history
pages["📈 Modelo & métricas"] = view_model
if auth.can(user["role"], "manage_users"): pages["👥 Usuários"] = view_admin
if auth.can(user["role"], "view_audit"): pages["🔍 Auditoria"] = view_audit
with st.sidebar:
    st.markdown(f"**{user['full_name']}**  \n`{user['role']}`")
    page = st.radio("Menu", list(pages))
    if st.button("Sair"):
        db.audit(user["username"], "LOGOUT"); logout(); st.rerun()
    st.caption(DISCLAIMER)
pages[page](user)
