"""Reproducible synthetic testing-data generator for the predictive-maintenance project."""

from pathlib import Path
import numpy as np
import pandas as pd


def generate_synthetic_testing_data(
    training_df: pd.DataFrame,
    models: dict,
    thresholds: dict,
    output_path: str | Path,
    ground_truth_path: str | Path,
    n_rows: int = 8000,
    seed: int = 42,
):
    """Generate a deterministic test set with normal, Alert, Error and recovery scenarios.

    The normal portion is bootstrapped from training rows to preserve the original
    schema and operating-value metadata. Axis #2 receives two controlled sustained
    deviations: one between MinC and MaxC and one above MaxC.
    """
    rng = np.random.default_rng(seed)
    sample_idx = rng.integers(0, len(training_df), size=n_rows)
    test = training_df.iloc[sample_idx].copy().reset_index(drop=True)

    start_time = pd.to_datetime(training_df["Time"], utc=True).min()
    intervals = rng.uniform(1.5, 2.5, size=n_rows)
    elapsed = np.r_[0.0, np.cumsum(intervals[:-1])]
    test["Time"] = start_time + pd.to_timedelta(elapsed, unit="s")
    test["Synthetic_Event"] = "NORMAL"

    axis = "Axis #2"
    minc = float(thresholds[axis]["MinC"])
    maxc = float(thresholds[axis]["MaxC"])

    # The models use elapsed seconds from the training start.
    prediction = models[axis].predict(elapsed.reshape(-1, 1))

    alert_start, alert_end = 2200, 2207
    error_start, error_end = 5000, 5007
    alert_target = (minc + maxc) / 2.0
    error_target = maxc * 1.20

    test.loc[alert_start:alert_end, axis] = prediction[alert_start:alert_end + 1] + alert_target
    test.loc[error_start:error_end, axis] = prediction[error_start:error_end + 1] + error_target
    test.loc[alert_start:alert_end, "Synthetic_Event"] = "KNOWN_ALERT"
    test.loc[error_start:error_end, "Synthetic_Event"] = "KNOWN_ERROR"
    if alert_end + 1 < n_rows:
        test.loc[alert_end + 1, "Synthetic_Event"] = "RECOVERY"
    if error_end + 1 < n_rows:
        test.loc[error_end + 1, "Synthetic_Event"] = "RECOVERY"

    output_path = Path(output_path)
    ground_truth_path = Path(ground_truth_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ground_truth_path.parent.mkdir(parents=True, exist_ok=True)
    test.to_csv(output_path, index=False)

    ground_truth = pd.DataFrame([
        {
            "event_type": "ALERT",
            "axis": axis,
            "start_index": alert_start,
            "end_index": alert_end,
            "duration_seconds": float(elapsed[alert_end] - elapsed[alert_start]),
            "residual_target": alert_target,
        },
        {
            "event_type": "ERROR",
            "axis": axis,
            "start_index": error_start,
            "end_index": error_end,
            "duration_seconds": float(elapsed[error_end] - elapsed[error_start]),
            "residual_target": error_target,
        },
    ])
    ground_truth.to_csv(ground_truth_path, index=False)
    return test, ground_truth
