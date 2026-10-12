"""Gera o relatório técnico (PDF) a partir de models/metrics.json, rag_eval.json e figuras."""
import json, sys
from pathlib import Path
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports/figures"
M = json.load(open(ROOT / "models/metrics.json")); R = json.load(open(ROOT / "models/rag_eval.json"))
D = Path("/usr/share/fonts/truetype/dejavu")
for n, f in [("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"), ("DV-BI", "DejaVuSans-BoldOblique.ttf")]:
    target = D / f if (D / f).exists() else D / "DejaVuSans.ttf"
    pdfmetrics.registerFont(TTFont(n, str(target)))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")
BLUE, PINK = colors.HexColor("#1f4e79"), colors.HexColor("#c2185b")
S = dict(
    body=ParagraphStyle("b", fontName="DV", fontSize=9, leading=13.2, alignment=TA_JUSTIFY, spaceAfter=5),
    h1=ParagraphStyle("h1", fontName="DV-B", fontSize=14, leading=18, textColor=BLUE, spaceBefore=10, spaceAfter=6),
    h2=ParagraphStyle("h2", fontName="DV-B", fontSize=10.5, leading=14, textColor=PINK, spaceBefore=6, spaceAfter=3),
    cap=ParagraphStyle("c", fontName="DV-I", fontSize=7.8, leading=10, textColor=colors.HexColor("#555"), spaceAfter=8, alignment=1),
    bul=ParagraphStyle("bu", fontName="DV", fontSize=9, leading=13, leftIndent=14, bulletIndent=3, spaceAfter=2.5),
    cell=ParagraphStyle("ce", fontName="DV", fontSize=7.8, leading=10),
    cellb=ParagraphStyle("cb", fontName="DV-B", fontSize=7.8, leading=10, textColor=colors.white),
    box=ParagraphStyle("bx", fontName="DV", fontSize=8.6, leading=12.4, backColor=colors.HexColor("#f4f8fb"), borderColor=BLUE,
                       borderWidth=0.6, borderPadding=6, spaceBefore=4, spaceAfter=10),
    box_leigo=ParagraphStyle("bxl", fontName="DV", fontSize=8.5, leading=12.2, backColor=colors.HexColor("#fff9c4"), borderColor=colors.HexColor("#f57f17"),
                             borderWidth=0.6, borderPadding=6, spaceBefore=4, spaceAfter=8),
)
story = []
P = lambda t, s="body": story.append(Paragraph(t, S[s]))
def L(text):
    story.append(Paragraph(f"<b>💡 Tradução para Leigos:</b> {text}", S["box_leigo"]))
def B(items):
    for i in items: story.append(Paragraph(i, S["bul"], bulletText="•"))
    story.append(Spacer(1, 4))
def FIGR(name, cap, w=15):
    im = PILImage.open(FIG / name); h = w * im.size[1] / im.size[0]
    story.append(KeepTogether([Image(str(FIG / name), width=w * cm, height=h * cm), Paragraph(cap, S["cap"])]))
def TBL(rows, widths, head=True):
    data = [[Paragraph(str(c), S["cellb"] if (head and i == 0) else S["cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
    st = [("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bbb")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f8fb")])]
    if head: st.append(("BACKGROUND", (0, 0), (-1, 0), BLUE))
    t.setStyle(TableStyle(st)); story.append(t); story.append(Spacer(1, 8))
pc = lambda v: f"{v:.1%}".replace(".", ",")
f3 = lambda v: f"{v:.3f}".replace(".", ",")
E, F, TF, CI = M["eda"], M["final"], M["test_final"], M["ci"]
res = M["results"]; ch = F["chosen"]

# ---------------- CAPA ----------------
story += [Spacer(1, 4 * cm), Paragraph("Guardiã AI", ParagraphStyle("t", fontName="DV-B", fontSize=34, textColor=BLUE, leading=40)),
          Paragraph("Inteligência Artificial para Saúde e Segurança da Mulher", ParagraphStyle("t2", fontName="DV", fontSize=15, textColor=PINK, leading=20, spaceAfter=14)),
          Paragraph("<b>Relatório técnico</b> — Tech Challenge Fase 5 · PosTech IA para Devs", ParagraphStyle("t3", fontName="DV", fontSize=11, leading=16)),
          Paragraph("Cenário principal: triagem de risco de câncer de mama (Machine Learning + SHAP + RAG + LLM + LangGraph)", ParagraphStyle("t4", fontName="DV", fontSize=10, leading=15, spaceAfter=30)),
          Paragraph("Grupo: <b>[inserir nomes dos integrantes]</b><br/>Repositório: <b>[inserir link do Git]</b><br/>Vídeo: <b>[inserir link YouTube/Vimeo]</b>", ParagraphStyle("t5", fontName="DV", fontSize=10, leading=16)),
          Spacer(1, 2 * cm),
          Paragraph("⚠ A Guardiã AI é um sistema de apoio ao profissional. Não faz diagnóstico definitivo, não prescreve medicamentos e não toma decisões automáticas. "
                    "Os dados usados são públicos e anonimizados (UCI WDBC). O modelo tem finalidade educacional e não foi validado clinicamente.", S["box"]),
          PageBreak()]

# ---------------- 1 RESUMO ----------------
P("1. Resumo executivo", "h1")
P(f"A Guardiã AI recebe os dados de um atendimento (30 medidas citológicas, relato em texto livre e identificador pseudonimizado), estima o risco de "
  f"malignidade com Machine Learning, explica a predição com SHAP, consulta uma base de protocolos via RAG, gera uma análise em linguagem natural com LLM e "
  f"passa tudo por guardrails antes de apresentar ao profissional, que registra a decisão final. Todo o fluxo é orquestrado com LangGraph, protegido por "
  f"login com perfis de acesso e registrado em uma trilha de auditoria com hash encadeado.")
B([f"<b>Modelos:</b> 4 algoritmos comparados com GridSearch + validação cruzada estratificada de 5 folds; escolhido: <b>{ch}</b> (maior PR-AUC em CV: {f3(res[ch]['cv']['pr_auc'])}).",
   f"<b>Operação:</b> limiar de segurança <b>{F['t_low']:.2f}</b> definido só com predições out-of-fold do treino para priorizar recall; no teste: recall <b>{pc(TF['recall'])}</b> "
   f"(IC95% bootstrap {pc(CI['recall'][0])}–{pc(CI['recall'][1])}), precisão {pc(TF['precision'])}, {TF['fn']} falso negativo e {TF['fp']} falsos positivos em 114 casos.",
   f"<b>RAG:</b> {R['chunks']} trechos de 7 documentos; hit@1 = {pc(R['hit1'])} e hit@3 = {pc(R['hit3'])} em {R['n']} perguntas (ressalvas na seção 8).",
   "<b>Segurança:</b> bcrypt, bloqueio por tentativas, JWT com expiração, RBAC (admin, profissional, auditor), pseudonimização por HMAC, mascaramento de CPF/e-mail/telefone, "
   "defesa básica contra injeção de prompt e trilha de auditoria verificável.",
   "<b>Qualidade:</b> 13 testes automatizados (pytest) e teste ponta a ponta da interface (Streamlit AppTest)."])
L("A Guardiã AI funciona como um assistente virtual inteligente para profissionais de saúde. Ela analisa medições de exames de mama, estima se há risco, explica quais características celulares chamaram mais atenção, busca orientações nos manuais do Ministério da Saúde e gera um resumo claro. No final, a palavra final é sempre dada pelo médico ou enfermeiro humano.")

# ---------------- 2 PROBLEMA ----------------
P("2. Problema e escopo", "h1")
P("Profissionais que atendem mulheres recebem dados cadastrais, clínicos, relatos e exames que precisam ser analisados rapidamente para identificar casos que exigem "
  "atenção, orientar os próximos passos e consultar protocolos. Escolhemos o cenário de <b>saúde da mulher – câncer de mama</b> porque há dado público de qualidade, "
  "métricas bem definidas (o custo de errar é assimétrico) e protocolos nacionais públicos para o RAG. O contexto de segurança da mulher não foi implementado "
  "(o enunciado pede um cenário principal); a arquitetura permite acrescentá-lo trocando a base de conhecimento e as regras de achados.")
P("<b>Fronteiras do produto (design for safety):</b> (i) a IA nunca fecha um caso: a revisão humana é registrada na trilha; (ii) a saída da LLM é bloqueada se contiver diagnóstico "
  "definitivo, prescrição ou dispensa de avaliação; (iii) quando não há documento relevante, o sistema diz que não há base suficiente em vez de inventar; "
  "(iv) \"baixo risco\" nunca é apresentado como exclusão de doença.", "box")
L("O sistema foi feito para ajudar a organizar e agilizar a triagem de pacientes em postos de saúde ou hospitais. Como um erro de avaliação pode custar caro, o programa atua apenas como um 'sinal de alerta' para o médico, sem nunca dar diagnósticos ou receitas sozinho.")

# ---------------- 3 DADOS ----------------
P("3. Dados e análise exploratória", "h1")
P(f"Usamos o <i>Breast Cancer Wisconsin (Diagnostic)</i> (UCI; Street, Wolberg e Mangasarian), público e anonimizado: <b>{E['n']} amostras</b>, "
  f"<b>{E['n_malignant']} malignas ({pc(E['n_malignant']/E['n'])})</b> e {E['n_benign']} benignas, {E['n_features']} variáveis numéricas, "
  f"{E['nulls']} valores nulos e {E['duplicates']} duplicatas. As variáveis são calculadas por análise computacional de imagens de punção aspirativa por agulha fina: dez "
  f"características do núcleo celular (raio, textura, perímetro, área, suavidade, compacidade, concavidade, pontos côncavos, simetria, dimensão fractal), cada uma como média, "
  f"erro padrão e pior valor.")
FIGR("01_classes.png", "Figura 1 – Desbalanceamento moderado (63/37): justifica estratificar os splits e olhar além da acurácia.", 7)
FIGR("02_correlacao.png", "Figura 2 – Raio, perímetro e área são quase redundantes (correlação ≈ 1); concavidade e pontos côncavos também. Isso afeta a leitura de importâncias (seção 6).", 10)
FIGR("03_boxplots.png", "Figura 3 – As variáveis de maior influência separam bem as classes, mas com sobreposição — por isso o modelo não é trivial e há erros.", 15.5)
L("Usamos uma base de dados pública com 569 exames reais (anônimos). O robô aprendeu examinando detalhes do formato, tamanho e textura das células para diferenciar casos benignos (sem câncer) de casos malignos.")

# ---------------- 4 PREPARAÇÃO ----------------
P("4. Preparação dos dados e prevenção de vazamento", "h1")
B(["<b>Alvo explícito:</b> no scikit-learn o rótulo vem invertido (0 = maligno). Convertemos para 1 = maligno logo na leitura, para que recall e precisão se refiram à classe que importa.",
   "<b>Split estratificado 80/20</b> (455 treino / 114 teste, semente 42). O teste só é usado ao final; nenhuma decisão de hiperparâmetro ou limiar o consulta.",
   "<b>Padronização dentro do Pipeline</b> (StandardScaler ajustado só no treino de cada fold) — evita vazamento de estatísticas do conjunto de validação.",
   "<b>Validação cruzada estratificada de 5 folds</b> com GridSearch pelo critério PR-AUC (average precision), independente de limiar.",
   "<b>Validação de entrada em produção:</b> valores ausentes, não numéricos ou negativos são rejeitados; valores muito fora da faixa vista no treino geram o alerta FORA_DA_DISTRIBUICAO."])
L("Para evitar que a IA 'decore' as respostas (o famoso efeito 'cola na prova'), separamos 20% dos exames em um cofre e só os usamos no final para testar se a inteligência artificial aprendeu de verdade a avaliar casos novos.")

# ---------------- 5 MODELOS ----------------
P("5. Modelos, métricas e impacto dos erros", "h1")
P("<b>Por que accuracy não basta.</b> Com 63% de benignos, um modelo que sempre dissesse \"benigno\" teria 63% de acurácia e zero utilidade. Aqui o erro mais grave é o "
  "<b>falso negativo</b> (caso maligno classificado como baixo risco): atrasa investigação e tratamento. O <b>falso positivo</b> gera ansiedade, exames e custo, mas é corrigido "
  "pela investigação complementar. Por isso priorizamos <b>recall</b> da classe maligna, controlando a <b>precisão</b> para não sobrecarregar o serviço, e acompanhamos F1, ROC-AUC, "
  "PR-AUC e Brier (calibração).")
rows = [["Modelo", "Melhores hiperparâmetros", "Recall CV", "Precisão CV", "F1 CV", "PR-AUC CV", "Recall teste (0,5)", "FN teste"]]
for n, v in res.items():
    hp = ", ".join(f"{k.split('__')[-1]}={int(x) if isinstance(x, float) and x == int(x) else x}" for k, x in v["best_params"].items())
    rows.append([n, hp, f3(v["cv"]["recall"]), f3(v["cv"]["precision"]), f3(v["cv"]["f1"]), f3(v["cv"]["pr_auc"]), f3(v["test_default"]["recall"]), v["test_default"]["fn"]])
TBL(rows, [3.0, 4.6, 1.6, 1.8, 1.3, 1.7, 1.9, 1.2])
FIGR("04_modelos_cv.png", "Figura 4 – Os quatro modelos ficam muito próximos em validação cruzada (limiar 0,5); o eixo foi truncado em 0,85 para evidenciar as diferenças.", 13.5)
P(f"<b>Escolha do modelo.</b> A diferença entre os modelos é pequena (PR-AUC {f3(min(v['cv']['pr_auc'] for v in res.values()))}–{f3(max(v['cv']['pr_auc'] for v in res.values()))}). "
  f"Como a <b>{ch}</b> teve o maior PR-AUC e é a mais simples e interpretável (coeficientes e SHAP exatos), escolhemos ela — um caso em que a complexidade extra de "
  f"árvores/boosting não se pagou nesse conjunto.")
FIGR("05_roc_pr.png", "Figura 5 – Curvas ROC e Precisão–Recall no conjunto de teste (valores de ROC-AUC na legenda).", 14.5)
P("<b>Limiar de decisão.</b> Em vez de usar 0,5, escolhemos dois pontos de operação a partir das probabilidades <i>out-of-fold</i> do treino: o <b>limiar de segurança</b> "
  f"({F['t_low']:.2f}) é o maior limiar que mantém recall ≥ 99%; abaixo dele o caso é \"baixo risco\". O <b>limiar de alta suspeita</b> ({F['t_high']:.2f}) é o menor que atinge "
  "precisão ≥ 97%. Entre os dois, \"intermediário\". Assim o sistema comunica incerteza em vez de uma resposta binária.")
FIGR("06_limiar.png", "Figura 6 – Trade-off recall × precisão no treino (OOF) e os limiares escolhidos.", 11)
tn, fp, fn, tp = TF["tn"], TF["fp"], TF["fn"], TF["tp"]
P(f"<b>Resultado no teste (limiar {F['t_low']:.2f}):</b> recall {pc(TF['recall'])}, precisão {pc(TF['precision'])}, F1 {pc(TF['f1'])}, acurácia {pc(TF['accuracy'])}, "
  f"ROC-AUC {f3(TF['roc_auc'])}, Brier {f3(TF['brier'])}. Matriz: VP={tp}, FN={fn}, FP={fp}, VN={tn}. Em relação ao limiar 0,5 (3 falsos negativos), o limiar de segurança "
  f"evitou 2 falsos negativos ao custo de mais falsos positivos (de 1 para {fp}) — o trade-off que escolhemos conscientemente.")
FIGR("07_confusao.png", "Figura 7 – Matriz de confusão no teste: limiar padrão vs. limiar operacional.", 12)
P(f"<b>Incerteza.</b> O teste tem só {tp+fn} casos malignos; um único erro muda o recall em ≈2,4 pontos. Por isso reportamos IC95% por bootstrap (2.000 reamostragens): "
  f"recall {pc(CI['recall'][0])}–{pc(CI['recall'][1])} e precisão {pc(CI['precision'][0])}–{pc(CI['precision'][1])}. Não devemos tratar 97,6% como garantia.")
FIGR("08_calibracao.png", "Figura 8 – Calibração no teste: probabilidades próximas da diagonal indicam que o número pode ser lido como risco estimado (amostra pequena).", 7)
L("Na área da saúde, dizer que uma pessoa doente está saudável (falso negativo) é perigoso. Por isso, ajustamos o sistema para ser ultra cauteloso: é preferível pedir um exame de confirmação a mais do que deixar passar um caso suspeito sem atenção.")

# ---------------- 6 SHAP ----------------
P("6. Interpretabilidade (SHAP)", "h1")
P("Usamos SHAP (<i>LinearExplainer</i> para a regressão logística; TreeExplainer é usado automaticamente se o modelo vencedor for de árvores). Globalmente (Figuras 9–10) "
  "mostramos quais variáveis mais pesam; localmente (Figura 11 e na interface) mostramos, para <i>cada</i> análise, o que empurrou a probabilidade para cima ou para baixo.")
FIGR("09_shap_global.png", "Figura 9 – Importância global média |SHAP| no teste.", 11)
FIGR("10_shap_beeswarm.png", "Figura 10 – Cada ponto é um caso; cor = valor da variável. Valores altos de textura/simetria/concavidade (vermelho) empurram para maligno.", 11.5)
FIGR("11_shap_local.png", "Figura 11 – Explicação local de um caso do teste classificado incorretamente no limiar operacional.", 12)
P("<b>Leitura crítica.</b> A variável nº 1 é \"textura (pior valor)\", e não perímetro/pontos côncavos, que costumam aparecer no topo na literatura sobre esse dataset. "
  "Como raio, perímetro e área são colineares (Figura 2), a regressão logística distribui o peso entre elas de forma instável, e alguns coeficientes têm sinal contraintuitivo "
  "(por exemplo, o erro padrão da compacidade reduz a suspeita). Concluímos que o SHAP explica <b>o modelo</b>, não a biologia: serve para auditar a predição, não para inferir causalidade clínica. "
  "Deixamos isso explícito para o profissional na interface.", "box")
L("O sistema não é uma 'caixa preta misteriosa'. Através de gráficos visuais (SHAP), ele mostra exatamente quais medições celulares fizeram a IA considerar o caso mais ou menos suspeito, permitindo que o médico valide o raciocínio.")

# ---------------- 7 LLM ----------------
P("7. Integração com a LLM", "h1")
P("A LLM (Claude, via API da Anthropic) recebe um prompt estruturado com quatro blocos delimitados: <i>resultado_modelo</i> (faixa, probabilidade, limiar, variáveis mais influentes), "
  "<i>relato</i>, <i>sinais_no_relato</i> e <i>documentos</i> recuperados. Ela produz resumo do caso, leitura do resultado, próximos passos sugeridos (sem decidir) e fontes citadas.")
B(["<b>Prompt de sistema</b> impõe os limites (sem diagnóstico/prescrição), obriga a usar apenas o contexto fornecido, a citar o arquivo-fonte e a tratar o conteúdo do relato como <b>dado, não instrução</b>.",
   "<b>Temperatura 0,2</b>, limite de tokens, timeout e novas tentativas automáticas.",
   "<b>Fallback offline determinístico:</b> sem chave de API, ou se a chamada falhar, o sistema gera a explicação por template com os mesmos dados (provedor registrado como <i>offline</i> ou <i>offline(fallback)</i>). O produto nunca fica fora do ar por causa do provedor e a demonstração é reprodutível.",
   "<b>Guardrails de entrada:</b> mascara CPF, e-mail e telefone antes de qualquer envio; sinaliza padrões de injeção de prompt (ex.: \"ignore as instruções\").",
   "<b>Guardrails de saída:</b> se o texto contiver diagnóstico definitivo, prescrição, dispensa de avaliação ou exclusão de doença, é substituído pelo texto seguro e o evento é registrado; o aviso de decisão final humana é sempre anexado.",
   "<b>Regra de precedência:</b> se o modelo indica baixo risco, mas o relato traz sinal clínico forte (nódulo, secreção, retração, linfonodo), a análise destaca a divergência e orienta avaliação clínica."])
P("<b>Limitação importante de validação:</b> no ambiente de desenvolvimento deste relatório não havia chave de API, então o caminho com a LLM real foi implementado e protegido por fallback, "
  "mas <b>os testes automatizados e as demonstrações cobrem o modo offline</b>. Antes de gravar o vídeo com a LLM real, rode alguns casos com ANTHROPIC_API_KEY configurada e confira "
  "se os guardrails de saída continuam adequados ao estilo do texto gerado.", "box")
L("Usamos Inteligência Artificial gerativa para escrever pareceres em texto simples para os médicos. Colocamos travas rígidas de segurança para esconder dados pessoais (CPF/telefone) e garantir que o texto gerado jamais dê receitas de remédios ou diagnósticos precipitados.")

# ---------------- 8 RAG ----------------
P("8. RAG – funcionamento e avaliação", "h1")
P(f"A base de conhecimento tem 7 documentos em Markdown (rastreamento, sinais de alerta, BI-RADS, variáveis do dataset, limites da IA/LGPD, fluxo de encaminhamento e fatores de risco), "
  f"resumos didáticos de fontes públicas (INCA/Ministério da Saúde, ACR, UCI, LGPD) — <b>devem ser validados contra as versões oficiais antes de uso real</b>. "
  f"Os documentos são divididos por seção em {R['chunks']} trechos; indexamos com TF-IDF (1–2-gramas, sem acentos, stopwords em português) e recuperamos por similaridade do cosseno, "
  f"devolvendo <b>arquivo, seção, trecho e pontuação</b> — a interface mostra de onde veio cada informação. Abaixo de uma pontuação mínima, nada é devolvido e o sistema responde que não há base suficiente.")
P("<b>Por que TF-IDF e não embeddings?</b> Para uma base pequena e em português, TF-IDF é rápido, determinístico, sem download de modelos e sem dependência externa — "
  "ideal para a imagem Docker e para reprodutibilidade. A interface do recuperador permite trocar por embeddings (por exemplo, um modelo multilíngue + FAISS/Chroma) sem mudar o grafo.")
FIGR("12_rag_eval.png", f"Figura 12 – Avaliação do recuperador. Hit@k = o documento esperado está entre os k primeiros trechos.", 8)
miss = 1 - R["ood_rejected"]
P(f"<b>Ressalvas honestas:</b> as {R['n']} perguntas foram escritas pela própria equipe com conhecimento do conteúdo, então hit@1 de {pc(R['hit1'])} é otimista; "
  f"em perguntas fora de escopo, o recuperador rejeitou {pc(R['ood_rejected'])} (uma das três, sobre futebol, ainda recuperou trechos por casar com palavras genéricas como \"resultado\"). "
  f"Elevar a pontuação mínima corrigiria esse caso, mas aumentaria o risco de rejeitar perguntas legítimas e curtas — é um ajuste de produto, não só técnico.")
L("Antes de responder, a IA faz uma busca instantânea nos manuais oficiais do Ministério da Saúde. Se a informação não constar nos livros oficiais, a IA declara abertamente que não possui a informação, em vez de inventar respostas falsas.")

# ---------------- 9 ARQUITETURA ----------------
P("9. Arquitetura e orquestração (LangGraph)", "h1")
FIGR("13_arquitetura.png", "Figura 13 – Visão geral. O grafo tem 8 nós e uma aresta condicional: entrada inválida encerra o fluxo e registra a rejeição.", 15.5)
TBL([["Nó", "Função", "Falha / segurança"],
     ["validate", "Valida 30 variáveis, faixa e OOD; sanitiza o relato (PII, injeção)", "Entrada inválida → END + auditoria"],
     ["model", "Probabilidade, faixa de risco, contribuições SHAP", "Modelo versionado registrado"],
     ["findings", "Regras de sinais de alerta no relato", "Determinístico e auditável"],
     ["retrieve", "RAG: consulta montada com faixa + sinais; top-4 trechos", "Sem base suficiente → declara"],
     ["generate", "LLM (Claude) ou template offline", "Timeout/erro → fallback offline"],
     ["guard", "Bloqueia diagnóstico/prescrição; anexa aviso", "Evento registrado como flag"],
     ["persist", "Grava análise e evento de auditoria", "ID do caso pseudonimizado (HMAC)"]], [2.2, 8.0, 6.0])
P("Além do fluxo de análise, há o assistente de perguntas sobre protocolos (RAG + LLM + guardrails) e a API REST (FastAPI) com os mesmos controles de acesso. "
  "A aplicação roda em Streamlit (interface) e Uvicorn (API); o Dockerfile treina o modelo no build com semente fixa, e o docker-compose sobe UI e API compartilhando o volume de dados.")
L("O programa funciona como uma linha de montagem automatizada dividida em 8 passos. Se algum dado vier corrompido ou suspeito em qualquer etapa, o processo para imediatamente e notifica os administradores.")

# ---------------- 10 SEGURANÇA ----------------
P("10. Segurança, privacidade e governança", "h1")
TBL([["Controle", "Implementação", "Verificado por teste"],
     ["Autenticação", "bcrypt (custo 12); política de senha ≥10 caracteres com letras e números; erro genérico (não revela se o usuário existe)", "test_senha_fraca, test_hash_nao_expoe_senha"],
     ["Anti força bruta", "Bloqueio de 15 min após 5 falhas (configurável)", "test_lockout"],
     ["Sessão / token", "Sessão Streamlit expira por inatividade; JWT HS256 com expiração; usuário reconferido no banco a cada requisição", "test_jwt_roundtrip_e_adulteracao"],
     ["RBAC", "admin (usuários, auditoria), profissional (analisa e revisa), auditor (somente leitura de histórico e auditoria)", "test_rbac, test_api (403)"],
     ["Privacidade", "Identificador do caso vira HMAC; CPF/e-mail/telefone mascarados no relato; dados do dataset são públicos", "test_fluxo_completo, test_guardrails_entrada"],
     ["Auditoria", "Cada login, análise, pergunta, revisão e acesso negado grava evento; hash SHA-256 encadeado; verificação de integridade na interface", "test_auditoria_integra_e_detecta_adulteracao"],
     ["Human-in-the-loop", "Decisão (concordo / discordo / mais informações) + observação gravadas por revisor", "Fluxo na interface e API"]], [2.8, 9.0, 4.4])
P("<b>O que ainda falta para produção:</b> HTTPS/terminação TLS, MFA, rotação de segredos, migração para banco gerenciado (PostgreSQL) com criptografia em repouso, ancoragem externa do hash de auditoria, "
  "política de retenção/eliminação (LGPD) e DPIA. O SQLite e o segredo local servem ao propósito do desafio, não a um ambiente clínico.", "box")
L("O sistema foi construído respeitando as leis de privacidade (LGPD). Todos os nomes e CPFs são ocultados automaticamente, e cada ação realizada fica registrada em um 'diário de bordo digital' que não pode ser alterado por ninguém.")

# ---------------- 11 TESTES ----------------
P("11. Testes e como executar", "h1")
P("<b>13 testes automatizados passando</b> (pytest): autenticação, política de senha, bloqueio, JWT, RBAC, fluxo completo para um caso maligno e um benigno, divergência modelo × relato, "
  "entradas inválidas, guardrails de entrada e saída, RAG (acerto e rejeição), integridade e adulteração da auditoria e a API ponta a ponta. A interface foi exercitada com o "
  "<i>AppTest</i> do Streamlit (login → exemplo maligno → análise → resultado ALTO, 99,8%).")
P("<font name='DV'>pip install -r requirements.txt<br/>PYTHONPATH=src python -m guardia.ml.train &nbsp;# treina e gera figuras<br/>"
  "PYTHONPATH=src streamlit run app/streamlit_app.py<br/>PYTHONPATH=src uvicorn guardia.api:app &nbsp;# API em :8000/docs<br/>docker compose up --build &nbsp;# UI :8501 + API :8000</font>", "box")
P("<b>Não validado neste ambiente:</b> a construção da imagem Docker (não havia Docker disponível) — o Dockerfile e o compose foram escritos seguindo o mesmo fluxo que funcionou localmente, "
  "mas precisam de um <i>docker compose up --build</i> antes da entrega.")
L("Executamos 13 testes simulados no sistema antes de liberá-lo. Testamos desde tentativas de invasão com senhas erradas até simulações de casos clínicos complexos para assegurar a estabilidade do programa.")

# ---------------- 12 DIFICULDADES ----------------
P("12. Dificuldades encontradas", "h1")
B(["<b>Alvo invertido no scikit-learn.</b> No dataset embutido 0 significa maligno. Se não fosse tratado, \"recall\" mediria a classe errada. Resolvido convertendo na leitura e testando os casos de exemplo.",
   "<b>Escolher o limiar sem contaminar o teste.</b> A tentação é ajustar o limiar olhando o teste. Usamos predições out-of-fold do treino e só então avaliamos no teste.",
   "<b>Teste pequeno, métricas instáveis.</b> Com 42 casos malignos, um erro mexe 2,4 pontos de recall. Trocamos \"um número\" por IC bootstrap e evitamos comparar modelos pelo teste (a comparação é feita em CV).",
   "<b>Modelos praticamente empatados.</b> Os quatro algoritmos ficaram a menos de 1 ponto de PR-AUC. Escolhemos pelo critério de CV + simplicidade/interpretabilidade, não pelo \"melhor número\" no teste.",
   "<b>Colinearidade e SHAP.</b> Raio, perímetro e área são redundantes; a importância individual ficou instável e com sinais contraintuitivos (seção 6). Passamos a apresentar o SHAP como explicação do modelo, não da biologia.",
   "<b>Divergência modelo × relato.</b> No primeiro teste de fumaça, um caso benigno com relato de \"nódulo palpável\" recebeu \"seguir o fluxo de rotina\" — correto para o modelo, inseguro para o atendimento. Criamos a regra de precedência do relato e um teste para ela.",
   "<b>RAG com consulta ruidosa.</b> A primeira versão repetia o mesmo documento na lista de fontes (um por trecho) e recuperava trechos para perguntas sem relação. Deduplicamos fontes e adotamos pontuação mínima; ainda sobra um falso positivo fora de escopo.",
   "<b>LLM não determinística e sem como testar offline.</b> Não dá para testar texto livre de forma exata. Separamos o que é determinístico (modelo, regras, guardrails, fallback) do que não é (texto da LLM) e colocamos a barreira de segurança <i>depois</i> da LLM.",
   "<b>Chave de API e Docker indisponíveis no ambiente de desenvolvimento.</b> Por isso a LLM real e a imagem Docker não foram executadas aqui (declarado nas seções 7 e 11).",
   "<b>Descompasso entre o dado e o uso real.</b> As 30 variáveis vêm de análise de imagens de citologia: um profissional na triagem inicial normalmente não as tem. Mantivemos o dataset por exigência de dados públicos, mas documentamos que o modelo representa a etapa posterior à coleta da amostra."])
L("Durante o desenvolvimento, enfrentamos desafios como evitar que o sistema desse alarmes falsos em excesso e garantir respostas úteis mesmo quando a internet estivesse fora do ar. Resolvemos todos criando camadas extras de proteção e simulação offline.")

# ---------------- 13 PONTOS POSITIVOS ----------------
P("13. Pontos positivos", "h1")
B(["<b>Modelo simples venceu.</b> A regressão logística igualou o boosting, com explicação exata, treino em segundos e comportamento previsível.",
   f"<b>Recall alto sem esconder o custo.</b> {pc(TF['recall'])} no teste com o limiar de segurança, mostrando explicitamente o aumento de falsos positivos.",
   "<b>Três faixas de risco</b> (baixo/intermediário/alto) em vez de resposta binária, o que comunica incerteza ao profissional.",
   "<b>Sistema útil sem internet nem chave de API</b> graças ao modo offline — demonstrações reprodutíveis e custo zero.",
   "<b>Guardrails testados</b> e posicionados depois da LLM; o produto respeita a regra de não diagnosticar nem prescrever mesmo se o texto gerado fugir do script.",
   "<b>Auditoria que se verifica sozinha:</b> o teste altera um registro e a cadeia de hashes aponta exatamente qual.",
   "<b>Rastreabilidade ponta a ponta:</b> cada análise guarda dados, versão do modelo, fontes, flags, provedor e decisão humana.",
   "<b>Base reaproveitável:</b> trocar a base de conhecimento e o modelo permite adaptar para risco materno ou segurança da mulher sem reescrever o fluxo."])
L("Os maiores pontos fortes do projeto foram sua velocidade, transparência na explicação do raciocínio e a garantia de funcionamento mesmo sem sinal de internet ou chaves pagas de API.")

# ---------------- 14 LIMITES / FUTURO ----------------
P("14. Limitações e trabalhos futuros", "h1")
B(["Dataset pequeno (569), de uma única origem e sem informações clínicas ou demográficas; sem validação externa e sem estudo de viés por subgrupos.",
   "Modelo educacional; qualquer uso clínico exigiria validação prospectiva, aprovação regulatória e governança de dados.",
   "RAG por TF-IDF e base de 7 documentos resumidos; evoluir para embeddings, reranking, documentos oficiais completos e avaliação com perguntas de especialistas.",
   "Relato interpretado por regras simples e pela LLM; futuro: extração estruturada com validação e avaliação com relatos reais anonimizados.",
   "Cenário de segurança da mulher (relatos, protocolos de acolhimento e encaminhamento) fica como extensão; a arquitetura já comporta.",
   "Multimodal (laudos em imagem/áudio, Fase 4) como diferencial futuro; monitoramento de deriva e retreino periódico."])
L("Esta versão é um protótipo educacional de laboratório. Antes de ser implementado em hospitais reais, precisará ser testado com milhares de exames adicionais e aprovado pelas autoridades de saúde pública.")

P("15. Referências", "h1")
B(["Wolberg, W. H.; Street, W. N.; Mangasarian, O. L. <i>Breast Cancer Wisconsin (Diagnostic) Data Set</i>. UCI Machine Learning Repository (Dua &amp; Graff).",
   "Street, W. N.; Wolberg, W. H.; Mangasarian, O. L. Nuclear feature extraction for breast tumor diagnosis. IS&amp;T/SPIE, 1993.",
   "Lundberg, S. M.; Lee, S.-I. A Unified Approach to Interpreting Model Predictions. NeurIPS, 2017 (SHAP).",
   "Pedregosa, F. et al. Scikit-learn: Machine Learning in Python. JMLR 12, 2011.",
   "INCA / Ministério da Saúde. Diretrizes para a detecção precoce do câncer de mama no Brasil.",
   "American College of Radiology. BI-RADS Atlas.",
   "Brasil. Lei nº 13.709/2018 (LGPD). LangGraph e LangChain (documentação oficial). Anthropic API (documentação oficial)."])

def foot(c, d):
    c.saveState(); c.setFont("DV", 7.5); c.setFillColor(colors.HexColor("#777"))
    c.drawString(2 * cm, 1.1 * cm, "Guardiã AI · Relatório técnico · Tech Challenge Fase 5"); c.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Página {d.page}"); c.restoreState()
out = ROOT / "reports/Relatorio_Tecnico_Guardia_AI.pdf"
SimpleDocTemplate(str(out), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                  title="Guardiã AI – Relatório técnico", author="Grupo Guardiã AI").build(story, onFirstPage=lambda c, d: None, onLaterPages=foot)
print("ok", out)
