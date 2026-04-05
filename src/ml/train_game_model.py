"""
Train a game-scale ML model for the Boardroom Simulator.

Features derived entirely from actual GameState values:
  quarter, runway_months, funding_stage, revenue_monthly_k,
  burn_rate_monthly_k, founder_experience, founder_background,
  sector, milestones_completed, staff_count, equity_given

Outcome: 1 = startup succeeds (survives to Series A/B or strong Q8),
         0 = startup fails (runs out of cash or stagnates)

Run with: uv run python -m src.ml.train_game_model
"""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ─────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────

MODEL_PATH = Path(__file__).parent / "models" / "startup_best_model.pkl"

NUMERIC_FEATURES = [
    "quarter",
    "runway_months",
    "revenue_monthly_k",
    "burn_rate_monthly_k",
    "founder_experience",
    "milestones_completed",
    "staff_count",
    "equity_given",
]
CATEGORICAL_FEATURES = ["funding_stage", "founder_background", "sector"]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

FUNDING_STAGE_ORDER = ["bootstrap", "angels", "seed", "series_a", "series_b"]
FUNDING_STAGE_NUM = {s: i for i, s in enumerate(FUNDING_STAGE_ORDER)}

# ─────────────────────────────────────────────────────────────────────
# Synthetic data generation calibrated to game scale
# ─────────────────────────────────────────────────────────────────────

def generate_game_data(n: int = 4000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Quarter (1–8), weighted toward later quarters (more info)
    quarter = rng.integers(1, 9, n)

    # Funding stage — earlier stages more common
    funding_stage = rng.choice(
        FUNDING_STAGE_ORDER,
        n,
        p=[0.35, 0.25, 0.20, 0.12, 0.08],
    )
    funding_num = np.array([FUNDING_STAGE_NUM[s] for s in funding_stage])

    # Revenue ($K/month): starts low (~8K), right-skewed, max ~500K
    # Higher funding stage → higher expected revenue
    rev_base = 8 + funding_num * 30
    revenue_k = rng.exponential(scale=rev_base + 20, size=n)
    revenue_k = np.clip(revenue_k, 0, 500)

    # Burn rate ($K/month): 25K–150K, grows with stage
    burn_base = 35 + funding_num * 15
    burn_rate_k = rng.normal(loc=burn_base, scale=15, size=n)
    burn_rate_k = np.clip(burn_rate_k, 20, 180)

    # Runway: cash / net_burn, clipped
    net_burn = np.maximum(burn_rate_k - revenue_k, 1)
    # Cash pool varies by stage
    cash_k = rng.uniform(50, 500, n) + funding_num * 400
    runway = cash_k / net_burn
    runway = np.clip(runway, 0, 36)

    # Founder experience (1–15 years)
    founder_experience = rng.integers(1, 16, n)

    # Founder background
    founder_background = rng.choice(["first_time", "business", "technical"], n)

    # Sector
    sector = rng.choice(["AI", "Fintech", "SaaS", "Healthtech", "E-commerce"], n)

    # Milestones completed (0–3), more likely at later quarters/stages
    milestone_prob = np.clip((quarter / 8 + funding_num / 4) / 2, 0.05, 0.9)
    milestones_completed = np.array([
        rng.binomial(3, p) for p in milestone_prob
    ])

    # Staff count (0–4 execs)
    staff_prob = np.clip(funding_num / 5 + 0.2, 0.1, 0.8)
    staff_count = np.array([
        rng.binomial(4, p) for p in staff_prob
    ])

    # Equity given (%) — accumulates with each round
    equity_given = rng.uniform(0, 5, n) + funding_num * 10
    equity_given = np.clip(equity_given, 0, 55)

    # ── Outcome: logistic model of success ──────────────────────────
    # Designed so even the best realistic game outcome tops out ~88–92%
    # and a struggling bootstrap sits at 15–30%
    net_burn_ratio = (burn_rate_k - revenue_k) / np.maximum(burn_rate_k, 1)  # 1=pure burn, 0=breakeven, <0=profitable
    revenue_score = np.log1p(revenue_k) / np.log1p(500)  # 0–1, log-scaled diminishing returns

    log_odds = (
        -2.0                                             # base
        + 0.25 * np.log1p(runway)                        # log-scaled runway: 6mo→+0.49, 12mo→+0.64, 36mo→+0.90
        + 0.40 * funding_num                             # stage: bootstrap=0, Series B=+1.6 max
        - 1.00 * net_burn_ratio                          # burn>revenue is penalised; profitable adds ~+0.2
        + 1.20 * revenue_score                           # revenue: max ~+1.2 at $500K/mo
        + 0.03 * founder_experience                      # minor
        + 0.35 * milestones_completed                    # execution proof: max +1.05
        + 0.12 * staff_count                             # team: max +0.48
        - 0.010 * equity_given                           # dilution: 63% → −0.63
        - 0.12 * np.maximum(0, (quarter - funding_num * 2 - 1))  # late quarter + low stage = danger
        + rng.normal(0, 1.5, n)                          # high noise: even great companies can fail (~10-15%)
    )

    prob = 1.0 / (1.0 + np.exp(-log_odds))
    outcome = (rng.uniform(0, 1, n) < prob).astype(int)

    return pd.DataFrame({
        "quarter": quarter,
        "runway_months": np.round(runway, 1),
        "funding_stage": funding_stage,
        "revenue_monthly_k": np.round(revenue_k, 2),
        "burn_rate_monthly_k": np.round(burn_rate_k, 2),
        "founder_experience": founder_experience,
        "founder_background": founder_background,
        "sector": sector,
        "milestones_completed": milestones_completed,
        "staff_count": staff_count,
        "equity_given": np.round(equity_given, 1),
        "outcome": outcome,
    })


# ─────────────────────────────────────────────────────────────────────
# Build pipeline
# ─────────────────────────────────────────────────────────────────────

def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
    ])
    # Logistic Regression: probability is sigmoid(Xβ), so it naturally
    # respects the log-odds structure of the training data and won't
    # saturate at 100% the way tree models do.
    model = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    return Pipeline([("prep", preprocessor), ("model", model)])


# ─────────────────────────────────────────────────────────────────────
# Train and save
# ─────────────────────────────────────────────────────────────────────

def main():
    print("Generating game-scale training data...")
    df = generate_game_data(n=4000)
    print(f"  {len(df)} rows | success rate: {df['outcome'].mean():.1%}")

    DATA_PATH = Path(__file__).parent.parent.parent / "data" / "game_training_data.csv"
    df.to_csv(DATA_PATH, index=False)
    print(f"  Dataset saved to {DATA_PATH}")

    X = df[ALL_FEATURES]
    y = df["outcome"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    pipeline = build_pipeline()

    print("Cross-validating...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_auc = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="roc_auc", n_jobs=-1)
    print(f"  CV ROC-AUC: {cv_auc.mean():.3f} ± {cv_auc.std():.3f}")

    pipeline.fit(X_train, y_train)
    test_auc = roc_auc_score(y_test, pipeline.predict_proba(X_test)[:, 1])
    print(f"  Test ROC-AUC: {test_auc:.3f}")
    print(classification_report(y_test, pipeline.predict(X_test), target_names=["Failure", "Success"]))

    # Refit on full dataset before saving
    pipeline.fit(X, y)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "features": ALL_FEATURES}, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
