import joblib
import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "models" / "startup_best_model.pkl"


class MarketPredictor:
    def __init__(self):
        self._pipeline = None
        self._features = None
        self._load_model()

    def _load_model(self):
        if not MODEL_PATH.exists():
            print(f"[ML] No model found at {MODEL_PATH}. Run: uv run python -m src.ml.train_game_model")
            return
        try:
            artifact = joblib.load(MODEL_PATH)
            if isinstance(artifact, dict) and "pipeline" in artifact:
                self._pipeline = artifact["pipeline"]
                self._features = artifact["features"]
                print(f"[ML] Model loaded OK. Features: {self._features}")
            else:
                print("[ML] Old model format — retraining required. Run: uv run python -m src.ml.train_game_model")
        except Exception as e:
            print(f"[ML] Failed to load model: {e}")

    def predict_with_full_features(self, ml_features: dict) -> float:
        """
        Predict success probability from a GameState feature dict.
        Returns 0.5 if model is not loaded.
        """
        if self._pipeline is None:
            return 0.5

        row = {
            "quarter":             ml_features.get("quarter", 1),
            "runway_months":       min(float(ml_features.get("runway_months", 6.0)), 36.0),
            "funding_stage":       ml_features.get("funding_stage", "bootstrap"),
            "revenue_monthly_k":   ml_features.get("revenue_monthly_k", 8.0),
            "burn_rate_monthly_k": ml_features.get("burn_rate_monthly_k", 35.0),
            "founder_experience":  ml_features.get("founder_experience", 3),
            "founder_background":  ml_features.get("founder_background", "first_time"),
            "sector":              ml_features.get("sector", "AI"),
            "milestones_completed": ml_features.get("milestones_completed", 0),
            "staff_count":         ml_features.get("staff_count", 0),
            "equity_given":        ml_features.get("equity_given", 0.0),
        }

        try:
            raw = self._pipeline.predict_proba(pd.DataFrame([row]))[0][1]
            # Compress to [0.12, 0.92] — prevents false certainty in either direction
            prob = 0.12 + (0.92 - 0.12) * raw
            return round(float(prob), 2)
        except Exception as e:
            logger.warning(f"Prediction failed: {e}")
            return 0.5

    def calculate_runway(self, budget: float, burn_rate: float, revenue: float) -> int:
        """Months of cash remaining before bankruptcy."""
        net_burn = burn_rate - revenue
        if net_burn <= 0:
            return 999  # profitable
        return int(budget / net_burn)
