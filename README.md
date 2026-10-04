# Manufacturing Robot Predictive Maintenance — Individual Project

## 1. Project Overview

This individual project extends the **Data Stream Visualization Workshop** into a regression-based predictive-maintenance workflow for manufacturing robot current data.

The project combines data streaming, cloud database storage, Linear Regression, residual analysis, data-driven thresholds, synthetic testing, and continuous Alert/Error detection.

### End-to-end workflow

```text
Robot CSV data
      ↓
StreamingSimulator
      ↓
Neon PostgreSQL
      ↓
Training data retrieval
      ↓
Linear Regression (Time → Axis #1–#8)
      ↓
Residual analysis
      ↓
MinC / MaxC / T discovery
      ↓
Synthetic testing data
      ↓
Continuous anomaly detection
      ↓
Alert / Error events
      ↓
Event log + visualizations
```

## 2. Project Objective

The objective is to identify unusual current consumption by comparing observed robot-axis current with the current expected from Linear Regression models.

Separate models are trained for:

- Time → Axis #1
- Time → Axis #2
- Time → Axis #3
- Time → Axis #4
- Time → Axis #5
- Time → Axis #6
- Time → Axis #7
- Time → Axis #8

The resulting residuals are used to establish evidence-based thresholds for sustained abnormal behaviour.

This is an **early-warning predictive-maintenance approach**. The dataset does not contain confirmed equipment-failure labels, so the project does not claim to predict a specific mechanical failure.

## 3. Project Structure

```text
DataStreamVIsual/
├── Predictive_Maintenance_Individual_Project_Simplified.ipynb
├── data/
│   └── robot_data.csv
├── src/
│   ├── __init__.py
│   ├── database_service.py
│   ├── dashboard.py
│   ├── streaming_simulator.py
│   └── synthetic_data_generator.py
├── results/
│   ├── regression_results.csv
│   ├── residual_threshold_analysis.csv
│   ├── final_thresholds.csv
│   ├── synthetic_testing_data.csv
│   ├── synthetic_ground_truth.csv
│   ├── synthetic_standardization_check.csv
│   ├── synthetic_normalization_check.csv
│   ├── anomaly_events.csv
│   ├── regression_all_axes.png
│   ├── residual_distributions.png
│   └── axis2_alert_error_detection.png
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

> **Submission note:** `.env` contains private database credentials and should not be included in the submitted repository. The local `.venv312/` environment should also not be submitted.

## 4. Dataset

The training dataset is stored in `data/robot_data.csv`.

The project uses the `Time` column and Axis #1–#8 for the regression analysis. The data is streamed through `StreamingSimulator` and can be stored in PostgreSQL before being retrieved for model training.

Synthetic testing data is generated separately from the training data using training-data metadata and controlled anomaly scenarios.

## 5. Database Integration

The project uses PostgreSQL/Neon as the cloud database component.

When `DATABASE_URL` is configured, the notebook:

1. Connects to PostgreSQL.
2. Creates the dedicated `predictive_maintenance_robot_data` table.
3. Inserts the training records.
4. Retrieves the stored records with the database service.
5. Uses the retrieved DataFrame as the authoritative training source.

For reproducibility, the local CSV remains available as a fallback when database credentials are not configured.

### Environment variable

Create a local `.env` file containing:

```text
DATABASE_URL=your_neon_connection_string
```

Do **not** commit `.env` or expose the connection string.

## 6. Streaming Simulation

`StreamingSimulator` reproduces a time-based data-streaming workflow by returning robot observations one record at a time through `nextDataPoint()`.

The streaming layer provides the connection between the CSV training data and the database ingestion workflow.

## 7. Regression Method

Each of the eight robot axes is modelled independently using Linear Regression:

```text
Axis current = slope × elapsed time + intercept
```

For every model, the project records:

- Slope
- Intercept
- R²
- MAE
- RMSE

The regression visualization shows the observed current values and fitted regression lines for all eight axes.

## 8. Residual Analysis

Residuals are calculated as:

```text
Residual = Actual current − Predicted current
```

Positive residuals represent observations above the regression estimate. Because the assignment focuses on unusually high current consumption, positive residuals are used to establish the deviation thresholds.

The project analyzes residual distributions and produces:

- Residual summary statistics
- Residual threshold analysis
- Residual distribution visualization

## 9. Threshold Discovery

The thresholds are **data-driven** rather than arbitrary constants.

### MinC — Alert threshold

**MinC is the 95th percentile of positive training residuals.**

A positive residual at or above this level represents unusually high current relative to the regression baseline and is treated as a potential warning when sustained.

### MaxC — Error threshold

**MaxC is the 99th percentile of positive training residuals.**

This represents a more extreme deviation from expected current behaviour and is treated as an Error when sustained.

### T — Minimum continuous duration

**T = 6 seconds.**

The observed normal sampling interval is approximately 1.9 seconds. Therefore, six seconds represents roughly three consecutive abnormal observations. This reduces the likelihood that a single short-lived spike generates an Alert/Error while still allowing sustained abnormal behaviour to be detected.

The notebook also compares candidate persistence windows before selecting the final six-second value.

### Example: Axis #2

| Threshold | Value |
|---|---:|
| MinC | 22.0584 |
| MaxC | 34.8640 |
| T | 6 seconds |

The final thresholds for all eight axes are saved in `results/final_thresholds.csv`.

## 10. Synthetic Testing

Synthetic testing data is generated reproducibly using `src/synthetic_data_generator.py` and training-data metadata.

The testing dataset preserves the structure and operating characteristics of the training data while introducing controlled abnormal behaviour.

The test scenarios include:

1. **Normal operation** — expected behaviour without an injected anomaly.
2. **Alert scenario** — sustained Axis #2 deviation above MinC but below MaxC.
3. **Error scenario** — sustained Axis #2 deviation above MaxC.
4. **Recovery** — return to normal behaviour after the abnormal scenarios.

The regression models are trained using the training data and are **not retrained on the synthetic testing data**.

## 11. Normalization and Standardization

Synthetic testing data is validated using preprocessing statistics derived from the training data only.

The project uses:

- `StandardScaler` for standardization.
- `MinMaxScaler` for normalization.

The scalers are fitted on the training-axis values and then applied to the synthetic testing data. The testing data is never used to fit the preprocessing statistics.

Validation outputs are saved as:

- `results/synthetic_standardization_check.csv`
- `results/synthetic_normalization_check.csv`

## 12. Alert and Error Detection

### Alert rule

An Alert is generated when:

```text
Deviation >= MinC
AND
Deviation remains above MinC continuously for >= T seconds
```

### Error rule

An Error is generated when:

```text
Deviation >= MaxC
AND
Deviation remains above MaxC continuously for >= T seconds
```

Error takes priority when a sustained event reaches the MaxC threshold.

Timestamp gaps greater than three seconds break continuity so irregular/missing observations are not incorrectly treated as continuous abnormal operation.

The detector records the event information required for analysis, including axis, event type, timestamps, deviation, threshold, and duration.

## 13. Event Logging

Detected Alert and Error events are saved to:

```text
results/anomaly_events.csv
```

The log provides a structured record of detected abnormal behaviour for further analysis or maintenance investigation.

## 14. Visualizations

The project generates the following main visualizations:

### Regression models

[Regression plots — all eight axes](results/regression_all_axes.png)

### Residual analysis

[Residual distributions](results/residual_distributions.png)

### Alert/Error detection

[Axis #2 Alert/Error detection](results/axis2_alert_error_detection.png)

The Axis #2 visualization shows the observed current, regression prediction, threshold boundaries, and detected sustained Alert/Error events.

## 15. Results

The main result files are stored in `results/`:

| File | Purpose |
|---|---|
| `regression_results.csv` | Regression metrics for Axis #1–#8 |
| `residual_threshold_analysis.csv` | Residual and candidate-threshold analysis |
| `final_thresholds.csv` | Final MinC, MaxC and T values |
| `synthetic_testing_data.csv` | Generated testing dataset |
| `synthetic_ground_truth.csv` | Known synthetic Alert/Error scenarios |
| `anomaly_events.csv` | Detected Alert/Error events |
| `synthetic_standardization_check.csv` | Standardization validation |
| `synthetic_normalization_check.csv` | Normalization validation |

The controlled testing scenarios demonstrate that the detector can identify sustained abnormal current behaviour and distinguish Alert and Error conditions.

## 16. Predictive-Maintenance Interpretation

The system follows this early-warning process:

```text
Normal current behaviour
        ↓
Regression establishes expected behaviour
        ↓
Actual current deviates from expected current
        ↓
Residual increases
        ↓
MinC / MaxC threshold is exceeded
        ↓
Deviation persists for T seconds
        ↓
Alert or Error is generated
        ↓
Maintenance investigation can be initiated
```

The system therefore provides an abnormal-behaviour warning that can support predictive-maintenance decisions. It should not be interpreted as proof that a mechanical failure will occur.

## 17. Installation

Use Python 3.12 or another compatible Python environment.

Create a virtual environment if required:

```bash
python3.12 -m venv .venv312
```

Activate it and install the dependencies:

```bash
pip install -r requirements.txt
```

The virtual environment is for local development only and should not be submitted to GitHub.

## 18. How to Run

1. Clone or download the project.
2. Create and activate a Python environment.
3. Install the packages from `requirements.txt`.
4. Configure `DATABASE_URL` in a local `.env` file if using Neon PostgreSQL.
5. Open `Predictive_Maintenance_Individual_Project_Simplified.ipynb`.
6. Select the project Python environment/kernel.
7. Run the notebook from the project root from top to bottom.
8. Confirm that the final validation cell reports that the required result files are present.
9. Save the notebook after the successful run so its outputs remain embedded in the submitted `.ipynb`.

## 19. Reproducibility and Security

- Dependencies are listed in `requirements.txt`.
- Database credentials are stored in `.env` locally and excluded from version control.
- `.env.example` can be used as a template for the required environment variable.
- `.venv312/` is excluded from version control.
- Synthetic testing uses a fixed random seed for reproducibility.

## 20. Limitations

- The dataset does not contain confirmed equipment-failure labels.
- Time → current Linear Regression has limited explanatory power when operating behaviour changes abruptly.
- Synthetic testing is controlled validation and does not represent confirmed real-world equipment failure.
- Thresholds are derived for this dataset and should be recalibrated for another machine, dataset, or operating regime.

## 21. Conclusion

This project extends the original data-streaming workflow with a complete regression-based anomaly-detection process. It connects streaming data to PostgreSQL, trains eight Linear Regression models, analyzes residuals, derives MinC/MaxC/T from observed behaviour, generates controlled synthetic test data, validates normalization and standardization, detects sustained Alert/Error conditions, logs events, and visualizes the results.

The resulting workflow demonstrates how abnormal industrial current behaviour can be identified early and presented as actionable maintenance warnings.
