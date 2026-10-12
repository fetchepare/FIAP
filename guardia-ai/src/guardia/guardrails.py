"""Guardrails de entrada e de saída (LGPD, injeção de prompt, limites de atuação da IA)."""
import re

DISCLAIMER = ("⚠️ Apoio à decisão: esta análise é automatizada, não é diagnóstico nem prescrição. "
              "A decisão final sempre deverá permanecer com uma pessoa responsável pelo atendimento.")

PII = [(re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF]"),
       (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
       (re.compile(r"\(?\b\d{2}\)?[\s-]?9?\d{4}[\s-]?\d{4}\b"), "[TELEFONE]")]
INJECTION = re.compile(r"(ignore|desconsidere|esque[çc]a).{0,40}(instru|regras|prompt)|system prompt|you are now|aja como|"
                       r"ignore (all|previous)", re.I)
FORBIDDEN = [
    (re.compile(r"\b(voc[eê]|a paciente|ela)\s+(tem|possui|est[aá] com)\s+(um\s+)?c[aâ]ncer\b", re.I), "diagnóstico definitivo"),
    (re.compile(r"diagn[oó]stico\s+(definitivo|confirmado)", re.I), "diagnóstico definitivo"),
    (re.compile(r"\b(prescrev\w+|receit\w+|tome|administre|inicie)\b.{0,40}\b(mg|comprimido|dose|quimioterapia|tamoxifeno)\b", re.I), "prescrição"),
    (re.compile(r"\b(n[aã]o\s+(precisa|h[aá] necessidade)\s+de\s+(exame|consulta|avalia))", re.I), "dispensa de avaliação"),
    (re.compile(r"\bdescarta(r|do)?\s+(totalmente\s+)?(a\s+)?(possibilidade\s+de\s+)?c[aâ]ncer\b", re.I), "exclusão de doença"),
]


def sanitize_text(text: str, max_len: int = 4000) -> tuple[str, list[str]]:
    flags = []
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text or "")[:max_len].strip()
    for rx, tag in PII:
        if rx.search(text):
            text = rx.sub(tag, text); flags.append("PII_MASCARADO")
    if INJECTION.search(text):
        flags.append("POSSIVEL_INJECAO_DE_PROMPT")
    return text, sorted(set(flags))


def check_output(text: str, fallback: str) -> tuple[str, list[str]]:
    flags = [tag for rx, tag in FORBIDDEN if rx.search(text)]
    if flags:
        text = fallback
    if "decisão final" not in text.lower():
        text = f"{text.rstrip()}\n\n{DISCLAIMER}"
    return text, sorted(set(flags))


RED_FLAG_RULES = {
    "nódulo/caroço palpável": r"n[oó]dulo|caro[cç]o|massa palp",
    "secreção papilar": r"secre[cç][aã]o|sangr\w+ (pelo|do) mamilo|descarga papilar",
    "retração/alteração de pele ou mamilo": r"retra[cç][aã]o|casca de laranja|vermelhid[aã]o|pele (da mama )?(enrugada|espessada)|mamilo invertido",
    "linfonodo axilar aumentado": r"l[ií]nfon|[ií]ngua|g[âa]nglio",
    "histórico familiar relevante": r"(m[aã]e|irm[aã]|av[oó]|tia|filha).{0,40}c[aâ]ncer|brca|hist[oó]rico familiar",
    "dor mamária": r"\bdor\b|dolor",
    "perda de peso inexplicada": r"perda de peso|emagrec",
}


def extract_red_flags(relato: str) -> list[str]:
    return [k for k, rx in RED_FLAG_RULES.items() if re.search(rx, relato or "", re.I)]
