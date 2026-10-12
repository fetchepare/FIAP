import sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
out = Path(__file__).resolve().parents[1] / "reports/figures/13_arquitetura.png"
fig, ax = plt.subplots(figsize=(9, 4.6)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 52)
def box(x, y, w, h, t, c="#dfe9f3", ec="#1f4e79", fs=7.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=c, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")
def arr(x1, y1, x2, y2): ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="->", color="#444", lw=1.2))
box(1, 40, 20, 9, "Profissional\n(login · RBAC)", "#fde7ef", "#c2185b", bold=True)
box(26, 40, 22, 9, "Streamlit UI  /  API FastAPI\n(JWT · sessão com expiração)", "#fff3e0", "#e67e22")
arr(21, 44.5, 26, 44.5)
ax.text(50, 35.2, "Fluxo LangGraph", fontsize=8.5, fontweight="bold", color="#1f4e79", ha="center")
steps = ["1. Validar\n+ sanitizar\n(PII, injeção)", "2. Modelo ML\nRegressão Log.\n+ limiar", "3. SHAP\n(explicação)", "4. Achados\ndo relato\n(regras)", "5. RAG\nTF-IDF\n7 docs", "6. LLM\nClaude /\noffline", "7. Guardrails\nde saída", "8. Persistir\n+ auditoria"]
for i, s in enumerate(steps):
    x = 2 + i * 12.2
    box(x, 21, 10.6, 12, s, "#e8f5e9" if i in (1, 2) else "#dfe9f3", "#2e7d32" if i in (1, 2) else "#1f4e79", fs=6.6)
    if i: arr(x - 1.6, 27, x, 27)
arr(37, 40, 37, 33.3)
box(2, 3, 22, 12, "SQLite\nusuários (bcrypt) · análises\nrevisões humanas", "#f3e5f5", "#6a1b9a", fs=7)
box(28, 3, 22, 12, "Trilha de auditoria\nhash SHA-256 encadeado\n(detecta adulteração)", "#f3e5f5", "#6a1b9a", fs=7)
box(54, 3, 20, 12, "Base de conhecimento\n(markdown + fontes)", "#fffde7", "#f9a825", fs=7)
box(78, 3, 20, 12, "Decisão humana\n(concordo / discordo /\nmais informações)", "#fde7ef", "#c2185b", fs=7, bold=True)
arr(93, 21, 88, 15.3); ax.text(93.5, 17.2, "resultado", fontsize=6.5)
arr(13, 21, 13, 15.3); arr(39, 21, 39, 15.3); arr(64, 21, 64, 15.3)
fig.suptitle("Arquitetura da Guardiã AI", fontsize=10, fontweight="bold"); fig.tight_layout(); fig.savefig(out, dpi=170)
