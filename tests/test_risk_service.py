import pytest
from ml.feature_engineering import compute_deviations, update_baseline_metrics
from ml.predict import evaluate_checkin_risk

def test_compute_deviations():
    baseline = {
        "avg_sleep_hours": 7.5,
        "avg_activity_level": 7.0,
        "avg_mood_score": 7.0,
        "observation_count": 5
    }
    checkin = {
        "sleep_hours": 4.5,
        "activity_level": 3.0,
        "mood_score": 4.0
    }
    devs = compute_deviations(checkin, baseline)
    assert devs["sleep_deviation"] == -3.0
    assert devs["activity_deviation"] == -4.0
    assert devs["mood_deviation"] == -3.0

def test_update_baseline_metrics():
    baseline = {
        "avg_sleep_hours": 7.0,
        "avg_sleep_quality": 7.0,
        "avg_activity_level": 7.0,
        "avg_mood_score": 7.0,
        "avg_social_engagement": 7.0,
        "observation_count": 1
    }
    checkin = {
        "sleep_hours": 9.0,
        "sleep_quality": 9.0,
        "activity_level": 9.0,
        "mood_score": 9.0,
        "social_engagement": 9.0
    }
    updated = update_baseline_metrics(baseline, checkin)
    assert updated["observation_count"] == 2
    assert updated["avg_sleep_hours"] == 8.0

def test_evaluate_checkin_risk_normal():
    baseline = {
        "avg_sleep_hours": 7.5,
        "avg_activity_level": 7.0,
        "avg_mood_score": 7.0,
        "observation_count": 5
    }
    checkin = {
        "sleep_hours": 7.5,
        "sleep_quality": 8,
        "activity_level": 7,
        "mood_score": 8,
        "social_engagement": 8,
        "sleep_deviation": 0.0,
        "activity_deviation": 0.0,
        "mood_deviation": 0.0,
        "requested_counsellor": False
    }
    result = evaluate_checkin_risk(checkin, baseline)
    assert result["indicator_status"] in ["Stable", "Preliminary"]
    assert result["requires_human_review"] is False

def test_evaluate_checkin_risk_explicit_counsellor_request():
    baseline = {
        "avg_sleep_hours": 7.5,
        "observation_count": 5
    }
    checkin = {
        "sleep_hours": 7.0,
        "sleep_quality": 7,
        "activity_level": 7,
        "sleep_deviation": -0.5,
        "activity_deviation": 0.0,
        "mood_deviation": 0.0,
        "requested_counsellor": True
    }
    result = evaluate_checkin_risk(checkin, baseline)
    assert result["indicator_status"] == "Elevated Concern"
    assert result["requires_human_review"] is True
    assert "student_explicitly_requested_counsellor" in result["reason_codes"]
