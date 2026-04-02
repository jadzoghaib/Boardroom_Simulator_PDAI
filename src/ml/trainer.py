import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data(filepath: str) -> pd.DataFrame:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at {filepath}")
    return pd.read_csv(filepath)

def preprocess_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict]:
    target_col = 'outcome'
    if target_col not in df.columns:
        raise ValueError(f"Dataset must contain an '{target_col}' predictor column.")
    
    df = df.dropna(subset=[target_col])
    
    def map_outcome(val):
        val = str(val).lower()
        if val in ['ipo', 'acquisition', 'success', '1', 'operating']:
            return 1
        return 0
    
    y = df[target_col].apply(map_outcome)
    drop_cols = [target_col, 'status', 'exact_date', 'founded_at']
    X = df.drop(columns=[col for col in df.columns if col in drop_cols])
    
    label_encoders = {}
    for col in X.select_dtypes(include=['object', 'category']).columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        label_encoders[col] = le
        
    X = X.fillna(X.median(numeric_only=True))
    
    if 'revenue' in X.columns and 'burn_rate' in X.columns:
        X['burn_to_revenue_ratio'] = np.where(X['revenue'] == 0, 0, X['burn_rate'] / X['revenue'])
        
    X = X.select_dtypes(include=[np.number])
    return X, y, label_encoders

def train_model(X: pd.DataFrame, y: pd.Series) -> GradientBoostingClassifier:
    logger.info("Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Using the parameters from timsletap/startup-analysis
    model = GradientBoostingClassifier(
        n_estimators=100, learning_rate=0.1, max_depth=4,
        min_samples_split=50, min_samples_leaf=20, subsample=0.8, random_state=42
    )
    
    logger.info("Stratified 5-Fold Cross-Validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='accuracy')
    logger.info(f"CV Mean Accuracy: {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    logger.info(f"Test Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
    logger.info(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")
    return model

def save_model(model: GradientBoostingClassifier, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(model, output_path)

if __name__ == '__main__':
    data_path = 'data/startup_funding_and_outcome.csv'
    model_output_path = 'src/ml/models/gb_startup_model.pkl'
    try:
        df = load_data(data_path)
        X, y, encoders = preprocess_data(df)
        model = train_model(X, y)
        save_model(model, model_output_path)
    except FileNotFoundError as e:
        logger.error(e)
