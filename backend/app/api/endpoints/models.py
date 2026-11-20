import json
import os
import time

import joblib
import pandas as pd
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_manager
from app.core.database import get_db
from app.models.activity_log import ActivityLog
from app.models.dataset import Dataset
from app.models.model_metadata import ModelMetadata
from app.models.prediction_history import ModelVersion
from app.models.user import User
from app.services.ml_service import MLService
from app.services.training_service import TrainingService

router = APIRouter(prefix="/models")

# Initialize models directory for training service
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)
TrainingService.set_models_dir(MODELS_DIR)

@router.post("/train-xgboost/{dataset_id}", status_code=status.HTTP_200_OK)
def train_xgboost_model(
    dataset_id: int,
    payload: dict | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_manager),
):
    model_name = (payload or {}).get("model_name", "xgboost_v1") if payload else "xgboost_v1"

    """
    Train an XGBoost model on a previously uploaded dataset.
    
    Args:
        dataset_id: ID of uploaded dataset
        model_name: Name for the trained model (default: xgboost_v1)
    
    Returns:
        Training results with metrics
    """
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Load dataset
        datasets_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "uploaded_datasets"
        )
        local_path = os.path.join(datasets_dir, f"dataset_{dataset.id}_{dataset.filename}")
        
        if not os.path.exists(local_path):
            raise HTTPException(status_code=404, detail="Dataset file not found on server")
        
        # Load and parse file
        if dataset.filename.endswith(".csv"):
            df = pd.read_csv(local_path)
        elif dataset.filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(local_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Train model
        start_time = time.time()
        training_result = TrainingService.train_and_save(df, model_name)
        training_duration = time.time() - start_time
        
        # Save to database
        # Deactivate previous models
        db.query(ModelVersion).update({ModelVersion.is_active: False})
        
        # Create new model version
        top_features_dict = training_result.get("feature_importance", {})
        top_features = sorted(
            top_features_dict.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        model_version = ModelVersion(
            model_name=model_name,
            algorithm="xgboost",
            dataset_id=dataset_id,
            accuracy=training_result["metrics"]["accuracy"],
            precision=training_result["metrics"]["precision"],
            recall=training_result["metrics"]["recall"],
            f1_score=training_result["metrics"]["f1_score"],
            roc_auc=training_result["metrics"]["roc_auc"],
            training_samples=training_result["metrics"]["train_samples"],
            test_samples=training_result["metrics"]["test_samples"],
            file_path=training_result["model_path"],
            is_active=True,
            training_duration_seconds=training_duration,
            top_features=json.dumps(dict(top_features)),
            preprocessing_notes=json.dumps(training_result["preprocessing"])
        )
        
        db.add(model_version)
        db.commit()
        
        # Audit log
        log = ActivityLog(
            action="train_xgboost",
            details=f"Trained XGBoost model '{model_name}' on dataset {dataset.filename}. Accuracy: {training_result['metrics']['accuracy']:.4f}",
            user_id=current_user.id
        )
        db.add(log)
        db.commit()
        
        return {
            "status": "success",
            "model_name": model_name,
            "message": f"XGBoost model trained successfully",
            "metrics": training_result["metrics"],
            "preprocessing": training_result["preprocessing"],
            "top_features": dict(top_features),
            "training_duration_seconds": training_duration
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

@router.get("/versions")
def list_model_versions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_manager)
):
    """List all trained model versions."""
    models = db.query(ModelVersion).order_by(ModelVersion.training_date.desc()).all()
    
    result = []
    for model in models:
        top_features = {}
        if model.top_features:
            try:
                top_features = json.loads(model.top_features)
            except:
                pass
        
        result.append({
            "id": model.id,
            "model_name": model.model_name,
            "algorithm": model.algorithm,
            "is_active": model.is_active,
            "accuracy": model.accuracy,
            "precision": model.precision,
            "recall": model.recall,
            "f1_score": model.f1_score,
            "roc_auc": model.roc_auc,
            "training_samples": model.training_samples,
            "test_samples": model.test_samples,
            "training_date": model.training_date,
            "training_duration_seconds": model.training_duration_seconds,
            "top_features": top_features
        })
    
    return result

@router.post("/activate/{model_id}")
def activate_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_manager)
):
    """Set a model version as active for predictions."""
    model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Deactivate all models
    db.query(ModelVersion).update({ModelVersion.is_active: False})
    
    # Activate this model
    model.is_active = True
    db.commit()
    
    # Audit log
    log = ActivityLog(
        action="activate_model",
        details=f"Activated model {model.model_name}",
        user_id=current_user.id
    )
    db.add(log)
    db.commit()
    
    return {
        "message": f"Successfully activated {model.model_name}",
        "model_id": model_id,
        "model_name": model.model_name
    }



@router.post("/train/{dataset_id}", status_code=status.HTTP_200_OK)
def retrain_models(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_manager)
):
    """Retrains all machine learning classifiers using a previously uploaded dataset, compares metrics, and sets the best classifier as active."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    datasets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploaded_datasets")
    local_path = os.path.join(datasets_dir, f"dataset_{dataset.id}_{dataset.filename}")
    if not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail="Dataset source file not found on server")
        
    try:
        # Load dataset file
        if dataset.filename.endswith(".csv"):
            df = pd.read_csv(local_path)
        else:
            df = pd.read_excel(local_path)
            
        X, y = MLService.preprocess_df(df)
        
        # Check size constraints
        if len(df) < 10:
            raise HTTPException(status_code=400, detail="Dataset is too small to train models (needs at least 10 rows)")
            
        # Train and compare classifiers
        results = MLService.train_and_compare(X, y)
        comparison = results["comparison"]
        best_model_name = results["best_model"]
        
        # Deactivate previous active models in DB
        db.query(ModelMetadata).update({ModelMetadata.is_active: False})
        
        # Save metrics in DB
        for algo_name, metrics in comparison.items():
            db_model = db.query(ModelMetadata).filter(ModelMetadata.algorithm == algo_name).first()
            if not db_model:
                db_model = ModelMetadata(
                    model_name=algo_name,
                    algorithm=algo_name,
                    file_path=metrics["file_path"]
                )
            db_model.accuracy = metrics["accuracy"]
            db_model.precision = metrics["precision"]
            db_model.recall = metrics["recall"]
            db_model.f1_score = metrics["f1_score"]
            db_model.roc_auc = metrics["roc_auc"]
            db_model.is_active = (algo_name == best_model_name)
            
            db.add(db_model)
            
        db.commit()
        
        # Audit log
        log = ActivityLog(
            action="train_models",
            details=f"Retrained models on dataset '{dataset.filename}'. Selected {best_model_name} as active.",
            user_id=current_user.id
        )
        db.add(log)
        db.commit()
        
        return {
            "message": "Models trained successfully",
            "best_model": best_model_name,
            "comparison": comparison
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to retrain models: {str(e)}")

@router.get("/compare")
def compare_models(db: Session = Depends(get_db)):
    """Returns a list of all models and their verification metrics."""
    models = db.query(ModelMetadata).all()
    if not models:
        # Initialize default model if empty
        try:
            MLService.get_active_model_details()
            models = db.query(ModelMetadata).all()
        except Exception:
            pass
    return models

@router.post("/select/{model_id}")
def select_active_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_manager)
):
    """Sets a specific model (by ID) as the active prediction model."""
    model = db.query(ModelMetadata).filter(ModelMetadata.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
        
    db.query(ModelMetadata).update({ModelMetadata.is_active: False})
    model.is_active = True
    db.commit()
    
    # Save active name to config
    MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saved_models")
    active_config = {"active_model": model.model_name}
    joblib.dump(active_config, os.path.join(MODELS_DIR, "active_config.joblib"))
    
    # Audit log
    log = ActivityLog(action="select_model", details=f"Selected active model {model.model_name}", user_id=current_user.id)
    db.add(log)
    db.commit()
    
    return {"message": f"Successfully activated {model.model_name}", "model": model}
