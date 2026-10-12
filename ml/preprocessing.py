import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS = [
    "sleep_hours",
    "sleep_quality",
    "activity_level",
    "mood_score",
    "social_engagement",
    "sleep_deviation",
    "activity_deviation",
    "mood_deviation"
]

def clean_and_impute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values with domain-appropriate defaults and calculate deviations."""
    cleaned = df.copy()
    
    # Fill optional mood/social if missing with neutral median values (e.g. 6.0)
    if "mood_score" in cleaned.columns:
        cleaned["mood_score"] = cleaned["mood_score"].fillna(6.0)
    if "social_engagement" in cleaned.columns:
        cleaned["social_engagement"] = cleaned["social_engagement"].fillna(6.0)
        
    for col in FEATURE_COLUMNS:
        if col not in cleaned.columns:
            cleaned[col] = 0.0
        cleaned[col] = pd.to_numeric(cleaned[col], errors='coerce').fillna(0.0)
        
    return cleaned[FEATURE_COLUMNS]

def get_preprocessor():
    """Return standard scaler fit for features."""
    return StandardScaler()
