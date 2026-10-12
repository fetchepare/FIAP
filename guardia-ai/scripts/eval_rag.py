"""Avalia o recuperador (hit@1/hit@3) com perguntas rotuladas e gera figura + JSON."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from guardia import config
from guardia.rag import Retriever

Q = [("Com que frequência devo fazer mamografia aos 55 anos?", "01_rastreamento_mama.md"),
     ("mamografia entre 40 e 49 anos deve ser indicada?", "01_rastreamento_mama.md"),
     ("autoexame substitui a mamografia?", "01_rastreamento_mama.md"),
     ("paciente com BRCA1 precisa de acompanhamento diferente?", "01_rastreamento_mama.md"),
     ("saída de secreção pelo mamilo é sinal de alerta?", "02_sinais_alerta.md"),
     ("nódulo palpável na axila o que fazer", "02_sinais_alerta.md"),
     ("pele com aspecto de casca de laranja", "02_sinais_alerta.md"),
     ("o que significa BI-RADS 3?", "03_birads.md"),
     ("BI-RADS 4 indica biópsia?", "03_birads.md"),
     ("categoria 0 avaliação incompleta", "03_birads.md"),
     ("o que são pontos côncavos e raio do núcleo celular?", "04_citologia_wdbc.md"),
     ("de onde vêm as 30 variáveis do dataset?", "04_citologia_wdbc.md"),
     ("a IA pode prescrever medicamentos?", "05_limites_ia_governanca.md"),
     ("por que falso negativo é mais grave?", "05_limites_ia_governanca.md"),
     ("como proteger dados pessoais sensíveis LGPD", "05_limites_ia_governanca.md"),
     ("quais etapas após biópsia até o tratamento", "06_fluxo_encaminhamento.md"),
     ("como conversar com a paciente sem diagnóstico confirmado", "06_fluxo_encaminhamento.md"),
     ("álcool e obesidade aumentam o risco?", "07_fatores_risco.md"),
     ("menarca precoce e menopausa tardia", "07_fatores_risco.md")]
OOD = ["receita de bolo de chocolate", "resultado do jogo de futebol", "como instalar o linux"]
r = Retriever()
h1 = h3 = 0; rows = []
for q, src in Q:
    res = r.search(q, k=3, min_score=0)
    ok1 = res[0]["source"] == src; ok3 = src in [x["source"] for x in res]
    h1 += ok1; h3 += ok3; rows.append((q, src, res[0]["source"], round(res[0]["score"], 3)))
ood_rej = sum(1 for q in OOD if not r.search(q))
out = dict(n=len(Q), hit1=h1 / len(Q), hit3=h3 / len(Q), ood_n=len(OOD), ood_rejected=ood_rej / len(OOD),
           chunks=len(r.chunks), misses=[x for x in rows if x[1] != x[2]])
json.dump(out, open(config.MODEL_DIR / "rag_eval.json", "w"), ensure_ascii=False, indent=2)
fig, ax = plt.subplots(figsize=(4.2, 2.6))
ax.bar(["hit@1", "hit@3", "rejeição\nfora de escopo"], [out["hit1"], out["hit3"], out["ood_rejected"]], color=["#1f4e79", "#2e7d32", "#c2185b"])
for i, v in enumerate([out["hit1"], out["hit3"], out["ood_rejected"]]): ax.text(i, v + .02, f"{v:.0%}", ha="center")
ax.set_ylim(0, 1.15); ax.set_title(f"Avaliação do RAG ({len(Q)} perguntas, {out['chunks']} trechos)", fontsize=8.5)
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(config.REPORT_DIR / "figures/12_rag_eval.png", dpi=150)
print(json.dumps(out, ensure_ascii=False, indent=1))
