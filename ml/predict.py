import os
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import joblib

from ml.preprocessing import clean_and_impute_features, FEATURE_COLUMNS
from ml.train_model import train_and_export_models

MODEL_DIR = Path(__file__).resolve().parent / "saved_models"
MODEL_PATH = MODEL_DIR / "wellbeing_model.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

_loaded_model = None

def get_or_load_model():
    """Retrieve cached trained model pipeline, or train on the fly if missing."""
    global _loaded_model
    if _loaded_model is not None:
        return _loaded_model
        
    if not MODEL_PATH.exists():
        train_and_export_models()
        
    try:
        _loaded_model = joblib.load(MODEL_PATH)
    except Exception:
        # Re-train if corrupted or version mismatch
        train_and_export_models()
        _loaded_model = joblib.load(MODEL_PATH)
        
    return _loaded_model

def get_model_metadata() -> Dict[str, Any]:
    """Retrieve model training evaluation metadata."""
    if not METADATA_PATH.exists():
        train_and_export_models()
    with open(METADATA_PATH, "r") as f:
        return json.load(f)

def evaluate_checkin_risk(
    checkin_data: Dict[str, Any],
    baseline: Dict[str, Any]
) -> Dict[str, Any]:
    """Assess early warning support signals using model probabilities and safety rules.
    Returns:
    - indicator_status: 'Stable', 'Preliminary', 'Needs Review', 'Elevated Concern'
    - confidence: float
    - reason_codes: List[str]
    - requires_human_review: bool
    """
    reasons: List[str] = []
    obs_count = baseline.get("observation_count", 0)
    
    # Check 1: Explicit student request takes precedence
    requested_counsellor = bool(checkin_data.get("requested_counsellor", False))
    if requested_counsellor:
        reasons.append("student_explicitly_requested_counsellor")

    # Check 2: Minimum history requirement
    is_preliminary = obs_count < 3
    if is_preliminary:
        reasons.append("insufficient_historical_observations_preliminary_assessment")

    # Prepare feature dataframe
    feature_row = {
        "sleep_hours": checkin_data.get("sleep_hours", 7.0),
        "sleep_quality": checkin_data.get("sleep_quality", 7),
        "activity_level": checkin_data.get("activity_level", 7),
        "mood_score": checkin_data.get("mood_score") if checkin_data.get("mood_score") is not None else 7,
        "social_engagement": checkin_data.get("social_engagement") if checkin_data.get("social_engagement") is not None else 7,
        "sleep_deviation": checkin_data.get("sleep_deviation", 0.0),
        "activity_deviation": checkin_data.get("activity_deviation", 0.0),
        "mood_deviation": checkin_data.get("mood_deviation", 0.0)
    }
    
    # Specific signal checks for explainable reason codes
    if feature_row["sleep_deviation"] <= -2.0:
        reasons.append("significant_negative_sleep_deviation")
    if feature_row["activity_deviation"] <= -2.5:
        reasons.append("significant_activity_drop")
    if feature_row["mood_deviation"] <= -2.5:
        reasons.append("self_reported_mood_decline")
    if feature_row["sleep_hours"] < 5.0:
        reasons.append("acute_sleep_duration_under_5_hours")

    # Machine learning model probability
    model = get_or_load_model()
    df_feat = pd.DataFrame([feature_row])
    cleaned_feat = clean_and_impute_features(df_feat)
    
    prob = float(model.predict_proba(cleaned_feat)[0, 1])
    
    # Determine Status
    if requested_counsellor:
        indicator_status = "Elevated Concern"
        requires_review = True
    elif is_preliminary:
        indicator_status = "Preliminary"
        requires_review = False
    elif prob >= 0.70:
        indicator_status = "Elevated Concern"
        requires_review = True
    elif prob >= 0.45:
        indicator_status = "Needs Review"
        requires_review = True
    else:
        indicator_status = "Stable"
        requires_review = False
        
    if not reasons and indicator_status == "Stable":
        reasons.append("wellbeing_indicators_within_typical_baseline")

    return {
        "indicator_status": indicator_status,
        "model_confidence": round(prob, 3),
        "model_version": "v1.0-simulated-rf",
        "reason_codes": reasons,
        "requires_human_review": requires_review
    }
