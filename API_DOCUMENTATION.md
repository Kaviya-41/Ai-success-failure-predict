# ML Upgrade API Documentation

## Overview
Enhanced prediction system with XGBoost ML model training, SHAP explanations, GitHub analysis, and prediction history tracking.

---

## Authentication
All endpoints require Bearer token authentication:
```bash
Authorization: Bearer {access_token}
```

---

## 1. Predictions

### POST /predictions/predict
Get predictions using baseline and/or ML model

**Request:**
```json
{
  "budget": 100000,
  "duration_days": 180,
  "team_size": 5,
  "team_experience_years": 3,
  "project_complexity": 3,
  "requirement_changes": 2,
  "sprint_delays": 1,
  "bug_count": 15,
  "testing_coverage": 75,
  "client_involvement": 3,
  "resource_availability": 85,
  "customer_satisfaction": 4,
  "project_type": "Web",
  "project_id": 1,
  "include_ml": true,
  "include_shap": true,
  "save_history": true
}
```

**Response:**
```json
{
  "timestamp": "2026-08-14T10:30:00Z",
  "metrics": { ... },
  "baseline_prediction": {
    "prediction": "Success",
    "is_successful_prediction": true,
    "success_probability": 72.5,
    "failure_probability": 27.5,
    "risk_score": 27.5,
    "risk_level": "Low",
    "health_score": 72.5,
    "confidence_score": 45,
    "model_algorithm": "Success/Failure IF-ELSE Decision Algorithm"
  },
  "ml_prediction": {
    "prediction": "Success",
    "success_probability": 75.3,
    ...
  },
  "shap_explanation": {
    "status": "success",
    "prediction_probability_success": 75.3,
    "top_positive_factors": [...],
    "top_negative_factors": [...],
    "summary": "Model predicts success primarily due to high testing coverage..."
  },
  "recommended_prediction": { ... },
  "prediction_method": "XGBoost ML (trained)",
  "model_used": "xgboost_v1"
}
```

### POST /predictions/explain
Get SHAP explanation for a specific prediction

**Request:**
```json
{
  "budget": 100000,
  "duration_days": 180,
  ...
  "model_name": "xgboost_v1"
}
```

**Response:**
```json
{
  "status": "success",
  "prediction_probability_success": 75.3,
  "top_positive_factors": [
    {
      "feature_name": "testing_coverage",
      "value": 75,
      "shap_value": 0.32,
      "direction": "positive",
      "impact": "strong"
    }
  ],
  "top_negative_factors": [...],
  "summary": "Human-readable explanation text",
  "all_contributions": [...]
}
```

### GET /predictions/history/{project_id}
Get prediction history for a project

**Query Parameters:**
- `limit` (default: 10): Number of records to return
- `offset` (default: 0): Number of records to skip

**Response:**
```json
{
  "project_id": 1,
  "total_records": 25,
  "limit": 10,
  "offset": 0,
  "predictions": [
    {
      "id": 1,
      "method": "XGBoost ML",
      "prediction": "Success",
      "success_probability": 75.3,
      "failure_probability": 24.7,
      "risk_level": "Low",
      "health_score": 75.3,
      "created_at": "2026-08-14T10:30:00Z"
    }
  ]
}
```

### GET /predictions/compare/{project_id}
Compare baseline and ML predictions for a project

**Response:**
```json
{
  "project_id": 1,
  "metrics": { ... },
  "baseline": { ... },
  "ml_model": { ... },
  "agreement": true,
  "recommendation": "Both methods agree: Success"
}
```

---

## 2. Models Training

### POST /models/train-xgboost/{dataset_id}
Train a new XGBoost model

**Request Body:**
```json
{
  "model_name": "xgboost_v1"
}
```

**Response:**
```json
{
  "status": "success",
  "model_name": "xgboost_v1",
  "message": "XGBoost model trained successfully",
  "metrics": {
    "accuracy": 0.85,
    "precision": 0.83,
    "recall": 0.87,
    "f1_score": 0.85,
    "roc_auc": 0.89
  },
  "preprocessing": {
    "total_samples": 50,
    "train_samples": 40,
    "test_samples": 10,
    "features_used": 12,
    "missing_values_filled": 0
  },
  "top_features": {
    "testing_coverage": 0.32,
    "bug_count": 0.18,
    ...
  },
  "training_duration_seconds": 12.5
}
```

### GET /models/versions
List all trained model versions

**Response:**
```json
[
  {
    "id": 1,
    "model_name": "xgboost_v1",
    "algorithm": "xgboost",
    "is_active": true,
    "accuracy": 0.85,
    "precision": 0.83,
    "recall": 0.87,
    "f1_score": 0.85,
    "roc_auc": 0.89,
    "training_samples": 40,
    "test_samples": 10,
    "training_date": "2026-08-14T10:00:00Z",
    "training_duration_seconds": 12.5,
    "top_features": {
      "testing_coverage": 0.32,
      ...
    }
  }
]
```

### POST /models/activate/{model_id}
Set a model as active for predictions

**Response:**
```json
{
  "message": "Successfully activated xgboost_v1",
  "model_id": 1,
  "model_name": "xgboost_v1"
}
```

---

## 3. GitHub Analysis

### POST /github/analyze
Analyze and save a public GitHub repository report. The API accepts the existing
optional `project_id` for compatibility; repository analysis itself only needs
`repository_url`.

**Request:**
```json
{
  "repository_url": "https://github.com/owner/repo"
}
```

**Response:**
```json
{
  "status": "success",
  "report_id": 1,
  "repository": { "repository_name": "owner/repo" },
  "metrics": {
    "languages": { "<language>": "<bytes>" },
    "commits": "<GitHub API count>",
    "contributors": "<GitHub API count>",
    "source_files": "<tree count>",
    "test_files": "<tree count>",
    "dependency_files": ["<detected manifest or lockfile>"],
    "code_quality": "<measured score>",
    "dependency_risk": "<measured score>"
  },
  "prediction": "<IF-ELSE result>",
  "health_score": "<computed score>",
  "risk_score": "<computed score>",
  "risk_level": "<computed level>",
  "positive_factors": ["<analysis-derived strength>"],
  "risk_factors": ["<analysis-derived weakness>"],
  "recommendations": ["<analysis-derived recommendation>"],
  "created_at": "<saved timestamp>"
}
```

Repository metadata, tree, languages, commit/contributor/issue/PR counts, README,
dependency manifests, lockfiles, and a bounded sample of source files are read
from the GitHub REST API. Source checks are structural indicators, not a full
static analysis or vulnerability scan. GitHub API rate limits are returned as
HTTP 429 with reset/retry guidance when available.

GitHub analysis is limited to 10 submitted analyses per UTC day for each user
and workspace. Requests that reach GitHub but fail still count toward the
daily quota. Further requests return HTTP 429 with a `Retry-After` header until
the quota resets at midnight UTC.

Each analysis makes multiple GitHub REST API requests. Without authentication,
GitHub allows 60 requests per hour per IP, which can be exhausted after only a
few analyses. To use the higher authenticated limit, create a GitHub personal
access token and set `GITHUB_TOKEN` in `backend/.env` (local backend) or in the
root `.env` used by Docker Compose. Restart the backend after setting it. The
token is used only for server-side GitHub API requests and must not be added to
frontend environment variables or committed to source control.

### GET /github/reports
List the current user's saved repository reports (admins can see all reports).
Supports an optional `limit` query parameter (1-100; default 20).

**Response:**
```json
{
  "reports": [
    {
      "id": "<report id>",
      "repository_url": "<submitted repository URL>",
      "repository_name": "<owner/repository>",
      "prediction": "<IF-ELSE result>",
      "health_score": "<computed score>",
      "risk_score": "<computed score>",
      "risk_level": "<computed level>",
      "created_at": "<saved timestamp>"
    }
  ]
}
```

### GET /github/reports/{report_id}
Retrieve the complete saved report, including repository indicators and
recommendations. Users can retrieve their own reports; admins can retrieve any.

### GET /github/repository/{project_id}
The legacy project-linked endpoint is retained for API compatibility.

---

## 4. Datasets

### POST /datasets/upload
Upload CSV/Excel training dataset

**Form Data:**
```
file: <file> (CSV or Excel)
```

**Response:**
```json
{
  "status": "success",
  "dataset_id": 1,
  "filename": "training_data.csv",
  "rows": 50,
  "message": "Dataset uploaded successfully"
}
```

### GET /datasets/
List all uploaded datasets

**Response:**
```json
[
  {
    "id": 1,
    "filename": "training_data.csv",
    "row_count": 50,
    "uploaded_at": "2026-08-14T10:00:00Z"
  }
]
```

---

## Example cURL Commands

### 1. Make a prediction
```bash
curl -X POST http://localhost:8000/api/predictions/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "budget": 100000,
    "duration_days": 180,
    "team_size": 5,
    "team_experience_years": 3,
    "project_complexity": 3,
    "requirement_changes": 2,
    "sprint_delays": 1,
    "bug_count": 15,
    "testing_coverage": 75,
    "client_involvement": 3,
    "resource_availability": 85,
    "customer_satisfaction": 4,
    "project_type": "Web",
    "include_ml": true,
    "include_shap": true
  }'
```

### 2. Train XGBoost model
```bash
curl -X POST http://localhost:8000/api/models/train-xgboost/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{"model_name": "xgboost_v1"}'
```

### 3. Analyze GitHub repository
```bash
curl -X POST http://localhost:8000/api/github/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{"repo_url": "https://github.com/owner/repo"}'
```

### 4. Upload dataset
```bash
curl -X POST http://localhost:8000/api/datasets/upload \
  -H "Authorization: Bearer your_token" \
  -F "file=@training_data.csv"
```

---

## Error Responses

### 400 - Bad Request
```json
{
  "detail": "Invalid input: testing_coverage must be between 0 and 100"
}
```

### 401 - Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 - Not Found
```json
{
  "detail": "Model not found"
}
```

### 500 - Server Error
```json
{
  "detail": "Training failed: insufficient data"
}
```

---

## Key Concepts

### Prediction Methods
- **Baseline**: Always available IF-ELSE decision algorithm (deterministic)
- **ML**: XGBoost model (requires training first)

### SHAP Explanations
- Shows which features positively/negatively influence ML predictions
- Provides human-readable summary
- Available when ML model is used

### Model Versioning
- Multiple models can be trained
- Only one can be active at a time
- Switching models changes /predictions/predict behavior

### Graceful Degradation
- If ML model not available, baseline is used
- If GitHub API fails, error is returned with fallback option
- All existing functionality preserved

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Server Error |

---

## Rate Limiting
- GitHub API: 60 requests/hour (unauthenticated), 5000/hour (authenticated)
- GitHub analysis: 10 submissions per user and per workspace per UTC day
- Training: One model at a time recommended (resource intensive)
- Predictions: No limit
