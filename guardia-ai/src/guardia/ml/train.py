"""Treino e comparação de modelos (WDBC – UCI/scikit-learn). Gera models/ e figuras do relatório.

Decisões-chave:
- classe positiva = MALIGNO (no scikit-learn o alvo vem invertido: 0=maligno);
- split estratificado 80/20; padronização DENTRO do Pipeline (sem vazamento);
- seleção de modelo por PR-AUC em validação cruzada (independe de limiar);
- limiar escolhido só com predições out-of-fold do treino (teste fica intocado até o fim).
"""
import json
import warnings

import joblib
import matplotlib
import numpy as np
import pandas as pd
import shap
from sklearn.calibration import calibration_curve
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss, confusion_matrix,
                             f1_score, precision_recall_curve, precision_score, recall_score, roc_auc_score,
                             roc_curve)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from .. import config
from .features import feature_names, label_pt

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

warnings.filterwarnings("ignore")
SEED = 42
FIG = config.REPORT_DIR / "figures"
C = {"blue": "#1f4e79", "pink": "#c2185b", "grey": "#7f8c8d", "green": "#2e7d32", "orange": "#e67e22"}
plt.rcParams.update({"figure.dpi": 150, "axes.spines.top": False, "axes.spines.right": False, "font.size": 9})


def load_data():
    d = load_breast_cancer(as_frame=True)
    X = d.data.copy()
    X.columns = feature_names()
    y = (d.target == 0).astype(int)  # 1 = maligno
    return X, y


def metrics_at(y, p, t):
    pred = (p >= t).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    return dict(accuracy=accuracy_score(y, pred), precision=precision_score(y, pred), recall=recall_score(y, pred),
                f1=f1_score(y, pred), roc_auc=roc_auc_score(y, p), pr_auc=average_precision_score(y, p),
                brier=brier_score_loss(y, p), tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp))


def candidates():
    return {
        "Regressão Logística": (Pipeline([("sc", StandardScaler()), ("clf", LogisticRegression(max_iter=5000, random_state=SEED))]),
                                {"clf__C": [0.01, 0.1, 1, 10]}),
        "Random Forest": (RandomForestClassifier(random_state=SEED, n_jobs=-1),
                          {"n_estimators": [200, 400], "max_depth": [None, 6], "min_samples_leaf": [1, 3]}),
        "Gradient Boosting": (GradientBoostingClassifier(random_state=SEED),
                              {"n_estimators": [100, 200], "learning_rate": [0.05, 0.1], "max_depth": [2, 3]}),
        "XGBoost": (XGBClassifier(random_state=SEED, eval_metric="logloss", n_jobs=2),
                    {"n_estimators": [150, 300], "learning_rate": [0.05, 0.1], "max_depth": [2, 3]}),
    }


def main():
    config.MODEL_DIR.mkdir(exist_ok=True, parents=True)
    FIG.mkdir(parents=True, exist_ok=True)
    X, y = load_data()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)

    eda = dict(n=len(X), n_malignant=int(y.sum()), n_benign=int((1 - y).sum()), n_features=X.shape[1],
               nulls=int(X.isna().sum().sum()), duplicates=int(X.duplicated().sum()))
    results, fitted, oof, test_p = {}, {}, {}, {}
    for name, (est, grid) in candidates().items():
        gs = GridSearchCV(est, grid, scoring="average_precision", cv=cv, n_jobs=1).fit(Xtr, ytr)
        best = gs.best_estimator_
        p_oof = cross_val_predict(best, Xtr, ytr, cv=cv, method="predict_proba")[:, 1]
        fitted[name], oof[name] = best, p_oof
        test_p[name] = best.predict_proba(Xte)[:, 1]
        results[name] = dict(best_params={k: (v if v is None or isinstance(v, str) else float(v)) for k, v in gs.best_params_.items()},
                             cv=metrics_at(ytr, p_oof, 0.5), test_default=metrics_at(yte, test_p[name], 0.5))
        print(name, {k: round(v, 3) for k, v in results[name]["cv"].items() if k in ("recall", "precision", "pr_auc")})

    chosen = max(results, key=lambda n: results[n]["cv"]["pr_auc"])
    model, p_oof = fitted[chosen], oof[chosen]

    # ---- limiares a partir do OOF do treino ----
    grid_t = np.linspace(0.01, 0.99, 197)
    rec = np.array([recall_score(ytr, p_oof >= t) for t in grid_t])
    prec = np.array([precision_score(ytr, p_oof >= t, zero_division=0) for t in grid_t])
    t_low = float(grid_t[np.where(rec >= 0.99)[0].max()]) if (rec >= 0.99).any() else 0.05  # maior limiar com recall>=99%
    ok_hi = np.where(prec >= 0.97)[0]
    t_high = float(grid_t[ok_hi.min()]) if len(ok_hi) else 0.9  # menor limiar com precisão>=97%
    t_high = max(t_high, t_low)
    final = dict(chosen=chosen, t_low=t_low, t_high=t_high)
    test_final = metrics_at(yte, test_p[chosen], t_low)

    # IC bootstrap (teste) para recall/precisão no limiar operacional
    rng = np.random.default_rng(SEED)
    boots = []
    yv, pv = yte.values, test_p[chosen]
    for _ in range(2000):
        i = rng.integers(0, len(yv), len(yv))
        if yv[i].sum() == 0:
            continue
        pr = (pv[i] >= t_low).astype(int)
        boots.append((recall_score(yv[i], pr), precision_score(yv[i], pr, zero_division=0)))
    b = np.array(boots)
    ci = dict(recall=[float(np.percentile(b[:, 0], 2.5)), float(np.percentile(b[:, 0], 97.5))],
              precision=[float(np.percentile(b[:, 1], 2.5)), float(np.percentile(b[:, 1], 97.5))])

    # casos errados no teste
    pred = (pv >= t_low).astype(int)
    wrong = Xte.index[pred != yv].tolist()

    # ---- SHAP ----
    pre = model[:-1] if isinstance(model, Pipeline) else None
    clf = model[-1] if isinstance(model, Pipeline) else model
    Xte_in = pre.transform(Xte) if pre else Xte.values
    Xtr_in = pre.transform(Xtr) if pre else Xtr.values
    expl = shap.LinearExplainer(clf, Xtr_in) if isinstance(clf, LogisticRegression) else shap.TreeExplainer(clf)
    sv = expl.shap_values(Xte_in)
    sv = sv[1] if isinstance(sv, list) else np.asarray(sv)
    if sv.ndim == 3:
        sv = sv[:, :, 1]
    imp = pd.Series(np.abs(sv).mean(0), index=Xte.columns).sort_values(ascending=False)

    joblib.dump(dict(model=model, features=list(X.columns), chosen=chosen, t_low=t_low, t_high=t_high,
                     lo=Xtr.min().to_dict(), hi=Xtr.max().to_dict(), bg=Xtr.sample(100, random_state=SEED),
                     version=f"wdbc-{chosen.lower().replace(' ', '-')}-v1"), config.MODEL_DIR / "model.joblib")
    json.dump(dict(eda=eda, results=results, final=final, test_final=test_final, ci=ci, wrong_test_idx=[int(i) for i in wrong],
                   shap_top=[(k, float(v)) for k, v in imp.head(10).items()]),
              open(config.MODEL_DIR / "metrics.json", "w"), indent=2, ensure_ascii=False)

    # ================= FIGURAS =================
    # 1 distribuição de classes
    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    ax.bar(["Benigno", "Maligno"], [eda["n_benign"], eda["n_malignant"]], color=[C["blue"], C["pink"]])
    for i, v in enumerate([eda["n_benign"], eda["n_malignant"]]):
        ax.text(i, v + 5, f"{v} ({v / eda['n']:.0%})", ha="center")
    ax.set_ylabel("Amostras"); ax.set_title("Distribuição das classes"); fig.tight_layout(); fig.savefig(FIG / "01_classes.png"); plt.close()
    # 2 correlação
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    mean_cols = [c for c in X.columns if c.startswith("mean")]
    cm = X[mean_cols].corr()
    im = ax.imshow(cm, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(10)); ax.set_yticks(range(10))
    ax.set_xticklabels([label_pt(c).split(" (")[0] for c in mean_cols], rotation=60, ha="right"); ax.set_yticklabels([label_pt(c).split(" (")[0] for c in mean_cols])
    fig.colorbar(im, shrink=0.8); ax.set_title("Correlação entre variáveis (grupo 'média')"); fig.tight_layout(); fig.savefig(FIG / "02_correlacao.png"); plt.close()
    # 3 boxplots top-4
    top4 = list(imp.index[:4])
    fig, axs = plt.subplots(1, 4, figsize=(8.2, 2.7))
    for a, f in zip(axs, top4):
        a.boxplot([X.loc[y == 0, f], X.loc[y == 1, f]], tick_labels=["Benigno", "Maligno"], patch_artist=True,
                  boxprops=dict(facecolor="#dfe9f3"), medianprops=dict(color=C["pink"]))
        a.set_title(label_pt(f), fontsize=7.5)
    fig.suptitle("Distribuição das 4 variáveis mais influentes por classe", fontsize=9); fig.tight_layout(); fig.savefig(FIG / "03_boxplots.png"); plt.close()
    # 4 comparação de modelos (CV)
    names = list(results)
    mets = ["recall", "precision", "f1", "pr_auc"]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    w = 0.2
    cols = [C["pink"], C["blue"], C["green"], C["orange"]]
    for j, m in enumerate(mets):
        vals = [results[n]["cv"][m] for n in names]
        ax.bar(np.arange(len(names)) + j * w, vals, w, label=m.replace("pr_auc", "PR-AUC").capitalize(), color=cols[j])
    ax.set_xticks(np.arange(len(names)) + 1.5 * w); ax.set_xticklabels(names)
    ax.set_ylim(0.85, 1.0); ax.legend(ncol=4, loc="lower center", fontsize=7); ax.set_title("Modelos – validação cruzada 5-fold (limiar 0,5)")
    fig.tight_layout(); fig.savefig(FIG / "04_modelos_cv.png"); plt.close()
    # 5 ROC + PR (teste)
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.2))
    for n, col in zip(names, cols):
        fpr, tpr, _ = roc_curve(yte, test_p[n]); axs[0].plot(fpr, tpr, color=col, label=f"{n} ({results[n]['test_default']['roc_auc']:.3f})")
        pp, rr, _ = precision_recall_curve(yte, test_p[n]); axs[1].plot(rr, pp, color=col, label=f"{n}")
    axs[0].plot([0, 1], [0, 1], "--", color=C["grey"]); axs[0].set_xlabel("1 - Especificidade"); axs[0].set_ylabel("Recall"); axs[0].set_title("Curva ROC (teste)"); axs[0].legend(fontsize=6.5, loc="lower right")
    axs[1].set_xlabel("Recall"); axs[1].set_ylabel("Precisão"); axs[1].set_title("Curva Precisão–Recall (teste)"); axs[1].set_ylim(0.8, 1.01)
    fig.tight_layout(); fig.savefig(FIG / "05_roc_pr.png"); plt.close()
    # 6 limiar
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    ax.plot(grid_t, rec, color=C["pink"], label="Recall (OOF treino)"); ax.plot(grid_t, prec, color=C["blue"], label="Precisão (OOF treino)")
    ax.axvline(t_low, color=C["grey"], ls="--"); ax.text(t_low + 0.01, 0.55, f"limiar operacional\n{t_low:.2f}", fontsize=7)
    ax.axvline(t_high, color=C["green"], ls=":"); ax.text(t_high + 0.01, 0.4, f"alto risco\n{t_high:.2f}", fontsize=7)
    ax.set_xlabel("Limiar de decisão"); ax.set_ylim(0.3, 1.02); ax.legend(loc="lower left", fontsize=7); ax.set_title(f"Trade-off recall × precisão – {chosen}")
    fig.tight_layout(); fig.savefig(FIG / "06_limiar.png"); plt.close()
    # 7 matriz de confusão
    fig, axs = plt.subplots(1, 2, figsize=(6.4, 2.9))
    for a, t, ttl in zip(axs, [0.5, t_low], ["Limiar 0,50", f"Limiar operacional {t_low:.2f}"]):
        m = confusion_matrix(yte, (test_p[chosen] >= t).astype(int)); a.imshow(m, cmap="Blues")
        for (i, j), v in np.ndenumerate(m): a.text(j, i, v, ha="center", va="center", color="white" if v > m.max() / 2 else "black", fontsize=12)
        a.set_xticks([0, 1]); a.set_yticks([0, 1]); a.set_xticklabels(["Benigno", "Maligno"]); a.set_yticklabels(["Benigno", "Maligno"])
        a.set_xlabel("Predito"); a.set_ylabel("Real"); a.set_title(ttl, fontsize=8.5)
    fig.suptitle(f"Matriz de confusão no teste – {chosen}", fontsize=9); fig.tight_layout(); fig.savefig(FIG / "07_confusao.png"); plt.close()
    # 8 calibração
    fig, ax = plt.subplots(figsize=(3.8, 3.4))
    fo, mp = calibration_curve(yte, test_p[chosen], n_bins=6, strategy="quantile")
    ax.plot([0, 1], [0, 1], "--", color=C["grey"]); ax.plot(mp, fo, "o-", color=C["pink"])
    ax.set_xlabel("Probabilidade prevista"); ax.set_ylabel("Fração de malignos"); ax.set_title(f"Calibração (Brier={test_final['brier']:.3f})"); fig.tight_layout(); fig.savefig(FIG / "08_calibracao.png"); plt.close()
    # 9 SHAP global
    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    t10 = imp.head(10)[::-1]
    ax.barh([label_pt(i) for i in t10.index], t10.values, color=C["blue"]); ax.set_xlabel("|SHAP| médio"); ax.set_title("Importância global (SHAP, conjunto de teste)")
    fig.tight_layout(); fig.savefig(FIG / "09_shap_global.png"); plt.close()
    # 10 SHAP beeswarm
    plt.figure(figsize=(6.2, 4.2))
    shap.summary_plot(sv, pd.DataFrame(Xte_in, columns=[label_pt(c) for c in Xte.columns]), max_display=10, show=False, plot_size=None)
    plt.title("SHAP – direção do efeito (vermelho = valor alto)", fontsize=9); plt.tight_layout(); plt.savefig(FIG / "10_shap_beeswarm.png"); plt.close()
    # 11 SHAP local: caso errado ou mais incerto
    idx = int(np.argmin(np.abs(test_p[chosen] - 0.5))) if not wrong else list(Xte.index).index(wrong[0])
    s = pd.Series(sv[idx], index=Xte.columns); s = s.reindex(s.abs().sort_values(ascending=False).index).head(8)[::-1]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.barh([label_pt(i) for i in s.index], s.values, color=[C["pink"] if v > 0 else C["blue"] for v in s.values])
    ax.axvline(0, color="k", lw=0.6); ax.set_xlabel("Contribuição (+ aumenta suspeita)")
    ax.set_title(f"Explicação local – caso de teste #{Xte.index[idx]} (p={test_p[chosen][idx]:.2f}, real={'maligno' if yv[idx] else 'benigno'})", fontsize=8.5)
    fig.tight_layout(); fig.savefig(FIG / "11_shap_local.png"); plt.close()
    print("modelo escolhido:", chosen, "| t_low", round(t_low, 3), "| t_high", round(t_high, 3))
    print("teste @t_low:", {k: round(v, 3) if isinstance(v, float) else v for k, v in test_final.items()}, "IC", ci)


if __name__ == "__main__":
    main()
