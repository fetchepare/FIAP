"""Nomes das variáveis (WDBC) e rótulos em português."""
BASE = ["radius", "texture", "perimeter", "area", "smoothness", "compactness",
        "concavity", "concave points", "symmetry", "fractal dimension"]
BASE_PT = ["raio", "textura", "perímetro", "área", "suavidade", "compacidade",
           "concavidade", "pontos côncavos", "simetria", "dimensão fractal"]
GROUPS = [("mean", "média"), ("error", "erro padrão"), ("worst", "pior valor")]


def feature_names() -> list[str]:
    return [f"{g} {b}" for g, _ in GROUPS for b in BASE]


def label_pt(name: str) -> str:
    g, b = name.split(" ", 1)
    gp = dict(GROUPS)[g]
    return f"{BASE_PT[BASE.index(b)]} ({gp})"
