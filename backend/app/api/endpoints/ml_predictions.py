"""
Enhanced predictions endpoint supporting both baseline and ML models with SHAP explanations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import pandas as pd
from datetime import datetime
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.prediction_history import PredictionHistory
from app.models.activity_log import ActivityLog
from app.services.prediction_service import PredictionService
from app.services.ml_service import MLService
from app.services.training_service import TrainingService
import os

router = APIRouter(prefix="/predictions", tags=["Predictions"])

# Initialize models directory
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)
PredictionService.set_models_dir(MODELS_DIR)


class MetricsInput(BaseModel):
    """Input metrics for prediction."""
    budget: float
    duration_days: int
    team_size: int
    team_experience_years: float
    project_complexity: int
    requirement_changes: int
    sprint_delays: int
    bug_count: int
    testing_coverage: float
    client_involvement: float
    resource_availability: float
    customer_satisfaction: float
    project_type: Optional[str] = "Web"


class PredictionResponse(BaseModel):
    """Response with both baseline and ML predictions."""
    prediction: str
    success_probability: float
    failure_probability: float
    risk_score: float
    risk_level: str
    health_score: float
    confidence_score: float
    model_algorithm: str
    prediction_time_ms: float
    top_risk_factors: Optional[list] = None
    top_success_factors: Optional[list] = None
    recommendations: Optional[list] = None


@router.post("/predict")
def predict_project_success(
    metrics: MetricsInput,
    project_id: Optional[int] = None,
    include_ml: bool = True,
    include_shap: bool = True,
    save_history: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate project success/failure prediction.
    
    Returns baseline IF-ELSE prediction and optional ML prediction if model is trained.
    
    Args:
        metrics: Project metrics
        project_id: Optional - Associate prediction with project
        include_ml: Include ML model prediction if available (default: True)
        include_shap: Include SHAP explanation for ML prediction (default: True)
        save_history: Save prediction to history (default: True)
    
    Returns:
        Dictionary with baseline prediction and optional ML prediction + SHAP
    """
    try:
        # Validate project if specified
        if project_id:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            if current_user.role != "admin" and project.owner_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not enough privileges")
        
        # Convert metrics to dictionary
        metrics_dict = metrics.dict()
        
        # Get predictions
        if include_ml:
            result = PredictionService.predict_with_both_methods(
                metrics_dict,
                include_shap=include_shap
            )
        else:
            # Baseline only
            baseline = MLService.predict_single(metrics_dict)
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics_dict,
                "baseline_prediction": baseline,
                "ml_prediction": None,
                "shap_explanation": None,
                "recommended_prediction": baseline,
                "model_used": None,
                "prediction_method": "Baseline IF-ELSE (Only)"
            }
        
        # Save to history if requested
        if save_history and project_id:
            try:
                # Get recommended prediction
                rec = result.get("recommended_prediction", result.get("baseline_prediction"))
                
                history = PredictionHistory(
                    project_id=project_id,
                    method=result.get("prediction_method", "baseline"),
                    metrics_json=json.dumps(metrics_dict),
                    is_successful_prediction=rec.get("is_successful_prediction"),
                    success_probability=rec.get("success_probability"),
                    failure_probability=rec.get("failure_probability"),
                    risk_score=rec.get("risk_score"),
                    risk_level=rec.get("risk_level"),
                    health_score=rec.get("health_score"),
                    confidence_score=rec.get("confidence_score"),
                    prediction=rec.get("prediction"),
                    top_risk_factors=json.dumps(rec.get("top_risk_factors", [])),
                    top_success_factors=json.dumps(rec.get("top_success_factors", [])),
                    recommendations=json.dumps(rec.get("recommendations", []))
                )
                
                # Add SHAP if available
                if result.get("shap_explanation") and result["shap_explanation"].get("status") == "success":
                    history.shap_explanation = json.dumps(result["shap_explanation"])
                
                db.add(history)
                db.commit()
            except Exception as e:
                # Log but don't fail if history save fails
                print(f"Warning: Failed to save prediction history: {str(e)}")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/explain")
def explain_prediction(
    metrics: MetricsInput,
    model_name: str = "xgboost_v1",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get SHAP explanation for a prediction using trained model.
    
    Args:
        metrics: Project metrics
        model_name: Name of trained model to explain
    
    Returns:
        SHAP explanation with feature contributions
    """
    try:
        # Check if model exists
        model_path = os.path.join(MODELS_DIR, f"{model_name}.joblib")
        if not os.path.exists(model_path):
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_name} not found"
            )
        
        # Load model
        model, scaler = TrainingService.load_model(model_name)
        
        # Prepare features
        import pandas as pd
        features_list = [
            metrics.dict().get(col, 0) for col in TrainingService.FEATURE_COLUMNS
        ]
        features_df = pd.DataFrame([features_list], columns=TrainingService.FEATURE_COLUMNS)
        
        # Get SHAP explanation
        from app.services.shap_service import SHAPService
        explanation_result = SHAPService.explain_prediction(
            model,
            scaler,
            features_df,
            TrainingService.FEATURE_COLUMNS
        )
        
        return explanation_result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@router.get("/history/{project_id}")
def get_prediction_history(
    project_id: int,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get prediction history for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    # Query history
    history = db.query(PredictionHistory).filter(
        PredictionHistory.project_id == project_id
    ).order_by(
        PredictionHistory.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    result = []
    for h in history:
        metrics = {}
        try:
            metrics = json.loads(h.metrics_json) if h.metrics_json else {}
        except:
            pass
        
        result.append({
            "id": h.id,
            "method": h.method,
            "prediction": h.prediction,
            "success_probability": h.success_probability,
            "failure_probability": h.failure_probability,
            "risk_level": h.risk_level,
            "health_score": h.health_score,
            "created_at": h.created_at,
            "metrics_summary": {k: v for k, v in metrics.items()} if metrics else {}
        })
    
    return {
        "project_id": project_id,
        "total_records": db.query(PredictionHistory).filter(
            PredictionHistory.project_id == project_id
        ).count(),
        "limit": limit,
        "offset": offset,
        "predictions": result
    }


@router.get("/compare/{project_id}")
def compare_prediction_methods(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare baseline and ML predictions for a project's latest metrics."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    try:
        # Build metrics from project
        metrics = {
            "budget": project.budget,
            "duration_days": project.duration_days,
            "team_size": project.team_size,
            "team_experience_years": project.team_experience_years,
            "project_complexity": project.project_complexity,
            "requirement_changes": project.requirement_changes,
            "sprint_delays": project.sprint_delays,
            "bug_count": project.bug_count,
            "testing_coverage": project.testing_coverage,
            "client_involvement": project.client_involvement,
            "resource_availability": project.resource_availability,
            "customer_satisfaction": project.customer_satisfaction,
            "project_type": project.project_type
        }
        
        # Compare
        comparison = PredictionService.compare_predictions(metrics)
        comparison["project_id"] = project_id
        
        return comparison
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


# Keep existing endpoints
from app.schemas.prediction import PredictionRequest, PredictionResponse as PredictionResponseSchema

@router.post("/predict-endpoint", response_model=PredictionResponseSchema)
async def predict(
    prediction_request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Original prediction endpoint - now uses unified service internally.
    Kept for backward compatibility.
    """
    metrics = prediction_request.dict()
    
    # Use unified service
    result = MLService.predict_single(metrics)
    
    return result

@router.post("/what-if")
def what_if_prediction(
    scenario: Dict[str, Any],
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run what-if analysis - predict with modified metrics.
    
    Args:
        scenario: Modified metrics to test
        project_id: Optional - base project to modify
    
    Returns:
        Prediction with modified metrics
    """
    try:
        # If project_id provided, load and merge metrics
        if project_id:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            if current_user.role != "admin" and project.owner_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not enough privileges")
            
            # Build base metrics from project
            metrics = {
                "budget": project.budget,
                "duration_days": project.duration_days,
                "team_size": project.team_size,
                "team_experience_years": project.team_experience_years,
                "project_complexity": project.project_complexity,
                "requirement_changes": project.requirement_changes,
                "sprint_delays": project.sprint_delays,
                "bug_count": project.bug_count,
                "testing_coverage": project.testing_coverage,
                "client_involvement": project.client_involvement,
                "resource_availability": project.resource_availability,
                "customer_satisfaction": project.customer_satisfaction,
                "project_type": project.project_type
            }
            
            # Apply scenario changes
            metrics.update(scenario)
        else:
            metrics = scenario
        
        # Get prediction
        result = PredictionService.predict_with_both_methods(metrics, include_shap=True)
        
        return {
            "scenario": scenario,
            "original_project_id": project_id,
            "prediction": result,
            "message": "What-if analysis complete"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-if analysis failed: {str(e)}")
