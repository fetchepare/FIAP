# 🛡️ Guardiã AI — triagem de risco de câncer de mama (Tech Challenge Fase 5)

Aplicação de **apoio ao profissional**: Dados → Machine Learning → SHAP → RAG → LLM → guardrails → **decisão médica final**.
**"A decisão final sempre deverá permanecer com uma pessoa responsável pelo atendimento."** Não faz diagnóstico definitivo, não prescreve e não decide automaticamente. Dados públicos/anonimizados (UCI WDBC). Uso educacional.

## Problema
Profissionais precisam analisar rapidamente dados e relatos de atendimento para identificar casos que exigem atenção. A Guardiã AI estima o risco de malignidade (30 medidas citológicas),
explica a predição, consulta protocolos com citação de fonte e gera uma análise em linguagem natural; **o(a) médico(a) ou profissional de saúde registra a conduta e a decisão final soberana**.

## Arquitetura (LangGraph)
`validar/sanitizar → modelo ML → SHAP → achados do relato → RAG → LLM → guardrails de saída → persistir + auditoria → decisão médica final`
- **ML:** Regressão Logística, Random Forest, Gradient Boosting e XGBoost (GridSearch + CV 5-fold); métricas: accuracy, precision, recall, F1, ROC-AUC, PR-AUC, Brier; limiar de segurança por recall.
- **RAG:** 7 documentos em `data/kb/` → trechos → TF-IDF + cosseno; devolve arquivo/seção/trecho.
- **LLM:** Google Gemini (`GEMINI_API_KEY`) ou Claude (`ANTHROPIC_API_KEY`); senão, modo offline determinístico (mesmos dados, texto por template). Falha de API → fallback offline.
- **Segurança & Governança:** login (bcrypt), bloqueio por tentativas, sessão com expiração, JWT na API, RBAC (`admin`, `profissional`, `auditor`), pseudonimização HMAC, mascaramento de CPF/e-mail/telefone, filtro de injeção de prompt, trilha de auditoria com hash encadeado (SHA-256) registrando cada análise e homologação de decisão médica.

## Executar
```bash
cp .env.example .env            # defina GUARDIA_ADMIN_PASSWORD (e, opcionalmente, GEMINI_API_KEY)
docker compose up --build       # UI: http://localhost:8501   API: http://localhost:8000/docs
```
Sem Docker:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
python -m guardia.ml.train                    # treina, salva models/ e figuras em reports/figures
streamlit run app/streamlit_app.py            # primeiro acesso: usuário admin (senha de GUARDIA_ADMIN_PASSWORD ou exibida na tela)
uvicorn guardia.api:app --port 8000           # API opcional
python -m guardia.cli create-user maria "Maria Silva" profissional
```
Testes: `PYTHONPATH=src pytest -q` (14 testes). Relatório: `python scripts/eval_rag.py && python scripts/make_arch.py && python scripts/make_report.py`.

## Perfis
| Perfil | Pode |
|---|---|
| admin | criar usuários, analisar, ver histórico geral e auditoria |
| profissional | analisar, perguntar ao assistente, registrar decisão, ver o próprio histórico |
| auditor | somente leitura: histórico geral e auditoria |

## Estrutura
`src/guardia/` (auth, db, graph, predictor, rag, llm, guardrails, api, cli, ml/train) · `app/streamlit_app.py` · `data/kb/` · `models/` · `reports/` · `tests/` · `scripts/`

## Limitações
Dataset pequeno, sem validação externa/clínica; variáveis vêm de análise de imagem de citologia; documentos da base são resumos didáticos a validar com fontes oficiais; SQLite e segredo local não são adequados a produção clínica.
