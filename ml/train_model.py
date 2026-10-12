import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, average_precision_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.preprocessing import FEATURE_COLUMNS

def generate_synthetic_wellbeing_dataset(n_samples: int = 1200, random_state: int = 42) -> pd.DataFrame:
    """Generate synthetic, simulated campus wellbeing checkin dataset for technical training and validation.
    DISCLAIMER: This dataset contains synthetic simulated signals and is not clinical diagnostic data.
    """
    np.random.seed(random_state)
    
    # Normal profile (approx 80%)
    n_normal = int(n_samples * 0.8)
    sleep_normal = np.random.normal(7.5, 1.0, n_normal).clip(5, 10)
    sleep_qual_normal = np.random.normal(7.5, 1.2, n_normal).clip(4, 10)
    activity_normal = np.random.normal(6.8, 1.4, n_normal).clip(4, 10)
    mood_normal = np.random.normal(7.2, 1.3, n_normal).clip(4, 10)
    social_normal = np.random.normal(7.0, 1.3, n_normal).clip(3, 10)
    sleep_dev_normal = np.random.normal(0.0, 0.8, n_normal).clip(-2.5, 2.5)
    act_dev_normal = np.random.normal(0.0, 1.0, n_normal).clip(-2.5, 2.5)
    mood_dev_normal = np.random.normal(0.0, 0.9, n_normal).clip(-2.5, 2.5)
    target_normal = np.zeros(n_normal, dtype=int)
    
    # Wellbeing distress profile (approx 20%): severe sleep drop, low activity, low mood, high negative deviations
    n_distress = n_samples - n_normal
    sleep_distress = np.random.normal(4.2, 1.2, n_distress).clip(1, 6.5)
    sleep_qual_distress = np.random.normal(3.8, 1.2, n_distress).clip(1, 6)
    activity_distress = np.random.normal(3.5, 1.3, n_distress).clip(1, 6)
    mood_distress = np.random.normal(3.4, 1.2, n_distress).clip(1, 6)
    social_distress = np.random.normal(3.2, 1.4, n_distress).clip(1, 6)
    sleep_dev_distress = np.random.normal(-2.8, 0.9, n_distress).clip(-5.0, -0.5)
    act_dev_distress = np.random.normal(-3.0, 1.1, n_distress).clip(-5.0, -0.5)
    mood_dev_distress = np.random.normal(-2.9, 1.0, n_distress).clip(-5.0, -0.5)
    target_distress = np.ones(n_distress, dtype=int)
    
    data = {
        "sleep_hours": np.concatenate([sleep_normal, sleep_distress]),
        "sleep_quality": np.concatenate([sleep_qual_normal, sleep_qual_distress]),
        "activity_level": np.concatenate([activity_normal, activity_distress]),
        "mood_score": np.concatenate([mood_normal, mood_distress]),
        "social_engagement": np.concatenate([social_normal, social_distress]),
        "sleep_deviation": np.concatenate([sleep_dev_normal, sleep_dev_distress]),
        "activity_deviation": np.concatenate([act_dev_normal, act_dev_distress]),
        "mood_deviation": np.concatenate([mood_dev_normal, mood_dev_distress]),
        "needs_support": np.concatenate([target_normal, target_distress])
    }
    
    df = pd.DataFrame(data)
    # Shuffle dataset
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return df

def train_and_export_models():
    """Train Logistic Regression and Random Forest models on simulated data and export the best pipeline."""
    print("Generating synthetic wellbeing dataset...")
    df = generate_synthetic_wellbeing_dataset()
    
    X = df[FEATURE_COLUMNS]
    y = df["needs_support"]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    
    print("\nTraining Logistic Regression baseline...")
    lr_pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(random_state=42, max_iter=500))
    ])
    lr_pipe.fit(X_train, y_train)
    lr_preds = lr_pipe.predict(X_test)
    lr_probs = lr_pipe.predict_proba(X_test)[:, 1]
    
    print("\nTraining Random Forest model...")
    rf_pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42))
    ])
    rf_pipe.fit(X_train, y_train)
    rf_preds = rf_pipe.predict(X_test)
    rf_probs = rf_pipe.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    rf_roc_auc = float(roc_auc_score(y_test, rf_probs))
    rf_pr_auc = float(average_precision_score(y_test, rf_probs))
    lr_roc_auc = float(roc_auc_score(y_test, lr_probs))
    lr_pr_auc = float(average_precision_score(y_test, lr_probs))
    
    rf_report = classification_report(y_test, rf_preds, output_dict=True)
    lr_report = classification_report(y_test, lr_preds, output_dict=True)
    
    print(f"Random Forest ROC-AUC: {rf_roc_auc:.4f}, PR-AUC: {rf_pr_auc:.4f}")
    print(f"Logistic Regression ROC-AUC: {lr_roc_auc:.4f}, PR-AUC: {lr_pr_auc:.4f}")
    
    output_dir = Path(__file__).resolve().parent / "saved_models"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_save_path = output_dir / "wellbeing_model.joblib"
    joblib.dump(rf_pipe, model_save_path)
    
    metadata = {
        "model_type": "RandomForestClassifier with StandardScaler",
        "version": "1.0.0-synthetic-trained",
        "features": FEATURE_COLUMNS,
        "n_samples": len(df),
        "random_forest": {
            "roc_auc": round(rf_roc_auc, 4),
            "pr_auc": round(rf_pr_auc, 4),
            "f1_score": round(rf_report["1"]["f1-score"], 4),
            "precision": round(rf_report["1"]["precision"], 4),
            "recall": round(rf_report["1"]["recall"], 4)
        },
        "logistic_regression": {
            "roc_auc": round(lr_roc_auc, 4),
            "pr_auc": round(lr_pr_auc, 4),
            "f1_score": round(lr_report["1"]["f1-score"], 4),
            "precision": round(lr_report["1"]["precision"], 4),
            "recall": round(lr_report["1"]["recall"], 4)
        },
        "disclaimer": "Models trained on synthetic simulated data to demonstrate early warning technical pipeline. Not intended for clinical diagnosis."
    }
    
    with open(output_dir / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"\nModel and metadata successfully saved to: {model_save_path}")
    return metadata

if __name__ == "__main__":
    train_and_export_models()
