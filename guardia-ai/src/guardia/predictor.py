"""Inferência + explicabilidade (SHAP) + validação de entrada (faixa/OOD)."""
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from . import config
from .ml.features import label_pt


class InputError(ValueError):
    pass


class Predictor:
    def __init__(self):
        a = joblib.load(config.MODEL_DIR / "model.joblib")
        self.model, self.features, self.version = a["model"], a["features"], a["version"]
        self.t_low, self.t_high, self.lo, self.hi, self.chosen = a["t_low"], a["t_high"], a["lo"], a["hi"], a["chosen"]
        self.pre = self.model[:-1] if isinstance(self.model, Pipeline) else None
        self.clf = self.model[-1] if isinstance(self.model, Pipeline) else self.model
        bg = a["bg"][self.features]
        bg_in = self.pre.transform(bg) if self.pre else bg.values
        self.expl = (shap.LinearExplainer(self.clf, bg_in) if isinstance(self.clf, LogisticRegression)
                     else shap.TreeExplainer(self.clf))

    def validate(self, feats: dict) -> tuple[dict, list[str]]:
        missing = [f for f in self.features if f not in feats or feats[f] in (None, "")]
        if missing:
            raise InputError(f"Variáveis ausentes: {', '.join(label_pt(m) for m in missing[:5])}…")
        clean, warns = {}, []
        for f in self.features:
            try:
                v = float(feats[f])
            except (TypeError, ValueError):
                raise InputError(f"Valor não numérico em {label_pt(f)}.")
            if not np.isfinite(v) or v < 0:
                raise InputError(f"Valor inválido em {label_pt(f)} (deve ser ≥ 0).")
            span = self.hi[f] - self.lo[f]
            if v > self.hi[f] + 0.5 * span or v < self.lo[f] - 0.5 * span:
                warns.append(f"FORA_DA_DISTRIBUICAO:{f}")
            clean[f] = v
        return clean, warns

    def predict(self, clean: dict) -> dict:
        X = pd.DataFrame([clean])[self.features]
        p = float(self.model.predict_proba(X)[0, 1])
        Xin = self.pre.transform(X) if self.pre else X.values
        sv = self.expl.shap_values(Xin)
        sv = sv[1] if isinstance(sv, list) else np.asarray(sv)
        sv = sv[:, :, 1] if sv.ndim == 3 else sv
        contrib = sorted(((f, float(v)) for f, v in zip(self.features, sv[0])), key=lambda t: -abs(t[1]))
        band = "baixo" if p < self.t_low else ("alto" if p >= self.t_high else "intermediário")
        return dict(probability=p, threshold=self.t_low, band=band,
                    contributions=[dict(feature=f, label=label_pt(f), value=clean[f], shap=v) for f, v in contrib[:10]])


@lru_cache(maxsize=1)
def get_predictor() -> Predictor:
    return Predictor()
