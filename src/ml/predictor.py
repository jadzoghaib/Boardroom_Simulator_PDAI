import joblib
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

class MarketPredictor:
    def __init__(self, model_path: str = "src/ml/models/gb_startup_model.pkl"):
        self.model_path = model_path
        self.model = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            logger.info("Model loaded successfully.")
        else:
            logger.warning(f"Model not found at {self.model_path}. Train the model first.")

    def predict_success_probability(self, burn_rate: float, revenue: float, founder_experience: int, sector: str) -> float:
        if not self.model:
            return 0.5 
            
        # We need to map the backend UI inputs to the ACTUAL columns the model was trained on
        # (which were loaded from your custom startup_success_dataset.csv!)
        
        sector_encoded = hash(sector) % 10 # Fallback 
        
        features = pd.DataFrame([{
            'funding_rounds': 1,                    # Default assumption
            'founder_experience_years': founder_experience,
            'team_size': 5,                         # Default assumption
            'market_size_billion': 10.0,            # Default assumption
            'product_traction_users': 1000,         # Default assumption
            'burn_rate_million': burn_rate / 1000000.0, 
            'revenue_million': revenue / 1000000.0,
            'investor_type': 0,                     # Default encoded value
            'sector': sector_encoded, 
            'founder_background': 0                 # Default encoded value
        }])
        
        prob = self.model.predict_proba(features)[0][1]
        return round(float(prob), 2)

    def calculate_runway(self, budget: float, burn_rate: float, revenue: float) -> int:
        """Calculates survival months before bankruptcy."""
        net_burn = burn_rate - revenue
        if net_burn <= 0:
            return 999 # Infinite runway / Profitable
        return int(budget / net_burn)
