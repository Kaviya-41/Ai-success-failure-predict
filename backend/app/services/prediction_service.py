"""
Enhanced prediction service combining IF-ELSE baseline with XGBoost ML model.

Provides two prediction methods with clear distinction.
"""

import pandas as pd
import joblib
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from app.services.ml_service import MLService
from app.services.training_service import TrainingService
from app.services.shap_service import SHAPService
import numpy as np


class PredictionService:
    """
    Service for generating predictions using both baseline and ML methods.
    
    Returns:
    - Baseline IF-ELSE prediction (always available)
    - ML prediction (if trained model exists)
    - SHAP explanation (if ML prediction used)
    """
    
    MODELS_DIR = None
    
    @staticmethod
    def set_models_dir(path: str):
        """Set the directory where models are saved."""
        PredictionService.MODELS_DIR = path
        TrainingService.set_models_dir(path)
    
    @staticmethod
    def predict_with_both_methods(
        metrics: Dict[str, Any],
        include_shap: bool = True,
        model_name: str = "xgboost_v1"
    ) -> Dict[str, Any]:
        """
        Generate predictions using both baseline IF-ELSE and trained ML model.
        
        Args:
            metrics: Project metrics dictionary
            include_shap: Whether to include SHAP explanation for ML prediction
            model_name: Name of trained model to use
            
        Returns:
            Dictionary with baseline prediction, ML prediction (if available), and SHAP explanation
        """
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "baseline_prediction": None,
            "ml_prediction": None,
            "shap_explanation": None,
            "recommended_prediction": None,
            "model_used": None
        }
        
        # 1. Get baseline IF-ELSE prediction (always available)
        try:
            baseline = MLService.predict_single(metrics)
            result["baseline_prediction"] = baseline
            baseline_available = True
        except Exception as e:
            result["baseline_prediction"] = {"error": str(e)}
            baseline_available = False
        
        # 2. Try to get ML prediction if model exists
        model_available = PredictionService._check_model_exists(model_name)
        
        if model_available:
            try:
                # Get ML prediction
                ml_result = PredictionService._predict_with_ml(metrics, model_name)
                result["ml_prediction"] = ml_result["prediction"]
                result["model_used"] = model_name
                
                # Get SHAP explanation if requested
                if include_shap and ml_result.get("model") and ml_result.get("scaler"):
                    try:
                        shap_result = PredictionService._get_shap_explanation(
                            metrics,
                            ml_result["model"],
                            ml_result["scaler"]
                        )
                        result["shap_explanation"] = shap_result
                    except Exception as e:
                        result["shap_explanation"] = {"error": f"SHAP generation failed: {str(e)}"}
                
                # Determine recommended prediction
                if baseline_available and result["ml_prediction"]:
                    # If both available, ML is primary (because it's trained on real data)
                    # But show both for comparison
                    result["recommended_prediction"] = result["ml_prediction"]
                    result["prediction_method"] = "XGBoost ML (trained)"
                elif baseline_available:
                    result["recommended_prediction"] = result["baseline_prediction"]
                    result["prediction_method"] = "Baseline IF-ELSE"
                
            except Exception as e:
                result["ml_prediction"] = {"error": str(e)}
                result["recommended_prediction"] = result.get("baseline_prediction")
                result["prediction_method"] = "Baseline IF-ELSE (ML failed)"
        else:
            # No trained model, use baseline only
            if baseline_available:
                result["recommended_prediction"] = result["baseline_prediction"]
                result["prediction_method"] = "Baseline IF-ELSE (No trained model)"
        
        return result
    
    @staticmethod
    def _check_model_exists(model_name: str) -> bool:
        """Check if trained model file exists."""
        if not PredictionService.MODELS_DIR:
            return False
        
        model_path = os.path.join(PredictionService.MODELS_DIR, f"{model_name}.joblib")
        return os.path.exists(model_path)
    
    @staticmethod
    def _predict_with_ml(
        metrics: Dict[str, Any],
        model_name: str
    ) -> Dict[str, Any]:
        """
        Get ML prediction from trained XGBoost model.
        
        Args:
            metrics: Project metrics
            model_name: Name of trained model
            
        Returns:
            Dictionary with ML prediction result
        """
        try:
            # Load model and scaler
            model, scaler = TrainingService.load_model(model_name)
            
            # Prepare features
            features_list = [
                metrics.get(col, 0) for col in TrainingService.FEATURE_COLUMNS
            ]
            features_df = pd.DataFrame([features_list], columns=TrainingService.FEATURE_COLUMNS)
            
            # Scale
            features_scaled = scaler.transform(features_df)
            
            # Predict
            prediction = model.predict(features_scaled)[0]
            probability = model.predict_proba(features_scaled)[0]
            
            success_prob = float(probability[1]) * 100
            failure_prob = float(probability[0]) * 100
            
            # Format similar to baseline for consistency
            result = {
                "prediction": "Success" if prediction == 1 else "Failure",
                "is_successful_prediction": bool(prediction == 1),
                "success_probability": round(success_prob, 2),
                "failure_probability": round(failure_prob, 2),
                "confidence_score": round(abs(success_prob - failure_prob), 2),
                "risk_score": round(failure_prob, 2),
                "risk_level": PredictionService._determine_risk_level(failure_prob),
                "health_score": round(success_prob, 2),
                "model_algorithm": f"XGBoost ML ({model_name})",
                "prediction_time_ms": 0  # ML prediction is fast
            }
            
            return {
                "prediction": result,
                "model": model,
                "scaler": scaler
            }
        
        except Exception as e:
            raise Exception(f"ML prediction failed: {str(e)}")
    
    @staticmethod
    def _get_shap_explanation(
        metrics: Dict[str, Any],
        model: Any,
        scaler: Any
    ) -> Dict[str, Any]:
        """
        Generate SHAP explanation for ML prediction.
        
        Args:
            metrics: Project metrics
            model: Trained XGBoost model
            scaler: Fitted scaler
            
        Returns:
            Dictionary with SHAP explanation
        """
        # Prepare features
        features_list = [
            metrics.get(col, 0) for col in TrainingService.FEATURE_COLUMNS
        ]
        features_df = pd.DataFrame([features_list], columns=TrainingService.FEATURE_COLUMNS)
        
        # Get SHAP explanation
        explanation_result = SHAPService.explain_prediction(
            model,
            scaler,
            features_df,
            TrainingService.FEATURE_COLUMNS
        )
        
        if explanation_result["status"] == "success":
            exp = explanation_result["explanations"]
            
            # Format for response
            return {
                "status": "success",
                "prediction_probability_success": exp["prediction_probability_success"],
                "top_positive_factors": exp["top_positive_factors"],
                "top_negative_factors": exp["top_negative_factors"],
                "summary": exp["summary"],
                "all_contributions": exp["all_contributions"]
            }
        else:
            return explanation_result
    
    @staticmethod
    def _determine_risk_level(failure_probability: float) -> str:
        """Determine risk level from failure probability."""
        if failure_probability <= 25:
            return "Low"
        elif failure_probability <= 50:
            return "Medium"
        else:
            return "High"
    
    @staticmethod
    def compare_predictions(
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare baseline and ML predictions side-by-side.
        
        Args:
            metrics: Project metrics
            
        Returns:
            Dictionary with comparison
        """
        combined = PredictionService.predict_with_both_methods(
            metrics,
            include_shap=False  # Skip SHAP for comparison view
        )
        
        comparison = {
            "metrics": metrics,
            "baseline": combined["baseline_prediction"],
            "ml_model": combined["ml_prediction"],
            "agreement": None,
            "recommendation": None
        }
        
        # Check if predictions agree
        if comparison["baseline"] and comparison["ml_model"]:
            baseline_pred = comparison["baseline"].get("prediction")
            ml_pred = comparison["ml_model"].get("prediction")
            
            if baseline_pred == ml_pred:
                comparison["agreement"] = True
                comparison["recommendation"] = f"Both methods agree: {baseline_pred}"
            else:
                comparison["agreement"] = False
                comparison["recommendation"] = (
                    f"Disagreement: Baseline says {baseline_pred}, "
                    f"ML says {ml_pred}. "
                    f"Consider ML as primary (trained on real data)."
                )
        
        return comparison
