from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

def compute_deviations(
    current_checkin: Dict[str, Any],
    baseline: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """Calculate the deviation of today's checkin from the student's personal baseline.
    Negative sleep_deviation means less sleep than personal average.
    Negative activity_deviation means less active than personal average.
    """
    if not baseline or baseline.get("observation_count", 0) < 3:
        # Default baseline if insufficient history
        base_sleep = 7.5
        base_act = 6.5
        base_mood = 6.5
    else:
        base_sleep = baseline.get("avg_sleep_hours", 7.5)
        base_act = baseline.get("avg_activity_level", 6.5)
        base_mood = baseline.get("avg_mood_score", 6.5)

    sleep_dev = float(current_checkin.get("sleep_hours", 7.0)) - base_sleep
    act_dev = float(current_checkin.get("activity_level", 6.0)) - base_act
    
    current_mood = current_checkin.get("mood_score")
    mood_dev = (float(current_mood) - base_mood) if current_mood is not None else 0.0

    return {
        "sleep_deviation": round(sleep_dev, 2),
        "activity_deviation": round(act_dev, 2),
        "mood_deviation": round(mood_dev, 2)
    }

def update_baseline_metrics(
    current_baseline: Dict[str, Any],
    new_checkin: Dict[str, Any]
) -> Dict[str, Any]:
    """Update running average baseline values incrementally."""
    n = current_baseline.get("observation_count", 0)
    new_n = n + 1
    
    def update_avg(old_avg, new_val):
        if new_val is None:
            return old_avg
        return ((old_avg * n) + float(new_val)) / new_n

    return {
        "avg_sleep_hours": round(update_avg(current_baseline.get("avg_sleep_hours", 7.0), new_checkin.get("sleep_hours")), 2),
        "avg_sleep_quality": round(update_avg(current_baseline.get("avg_sleep_quality", 7.0), new_checkin.get("sleep_quality")), 2),
        "avg_activity_level": round(update_avg(current_baseline.get("avg_activity_level", 6.5), new_checkin.get("activity_level")), 2),
        "avg_mood_score": round(update_avg(current_baseline.get("avg_mood_score", 6.5), new_checkin.get("mood_score")), 2),
        "avg_social_engagement": round(update_avg(current_baseline.get("avg_social_engagement", 6.5), new_checkin.get("social_engagement")), 2),
        "observation_count": new_n
    }
