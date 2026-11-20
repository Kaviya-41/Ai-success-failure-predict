"""
SHAP explainability service for XGBoost model predictions.

Provides feature importance and contribution analysis.
"""

import shap
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
import joblib
import os


class SHAPService:
    """
    Service for generating SHAP explanations for model predictions.
    
    SHAP (SHapley Additive exPlanations) values show the contribution of each feature
    to pushing the prediction from the base value (average prediction) to the actual prediction.
    """
    
    @staticmethod
    def explain_prediction(
        model: Any,
        scaler: Any,
        features_df: pd.DataFrame,
        feature_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Generate SHAP explanation for a prediction.
        
        Args:
            model: Trained XGBoost model
            scaler: Fitted StandardScaler
            features_df: Single row or multiple rows of features
            feature_columns: List of feature names in order
            
        Returns:
            Dictionary with SHAP values and explanations
        """
        # Scale features
        features_scaled = scaler.transform(features_df)
        
        # Create SHAP explainer
        explainer = shap.TreeExplainer(model)
        
        # Get SHAP values
        shap_values = explainer.shap_values(features_scaled)
        
        # Handle binary classification (shap_values is list for each class)
        if isinstance(shap_values, list):
            # For binary classification, use positive class SHAP values
            shap_values = shap_values[1]
        
        # Get base value (expected model output)
        base_value = explainer.expected_value
        if isinstance(base_value, list):
            base_value = base_value[1]
        
        # Get predictions
        predictions = model.predict_proba(features_scaled)
        pred_proba_success = predictions[:, 1] if predictions.shape[1] > 1 else predictions[:, 0]
        
        # Build explanations for each row
        explanations = []
        
        for idx in range(len(features_df)):
            row_shap_values = shap_values[idx] if len(shap_values.shape) > 1 else shap_values
            row_features = features_df.iloc[idx]
            
            # Create contribution list
            contributions = []
            for feat_idx, feat_name in enumerate(feature_columns):
                shap_val = float(row_shap_values[feat_idx])
                feat_val = float(row_features[feat_name])
                
                contributions.append({
                    "feature": feat_name,
                    "value": feat_val,
                    "shap_value": shap_val,
                    "direction": "positive" if shap_val > 0 else "negative",
                    "impact": abs(shap_val)
                })
            
            # Sort by absolute impact
            contributions.sort(key=lambda x: x["impact"], reverse=True)
            
            # Get top positive and negative contributors
            top_positive = [c for c in contributions if c["direction"] == "positive"][:3]
            top_negative = [c for c in contributions if c["direction"] == "negative"][:3]
            
            explanations.append({
                "prediction_probability_success": float(pred_proba_success[idx]),
                "base_value": float(base_value),
                "all_contributions": contributions,
                "top_positive_factors": top_positive,
                "top_negative_factors": top_negative,
                "summary": SHAPService._generate_summary(top_positive, top_negative)
            })
        
        return {
            "status": "success",
            "explanations": explanations if len(explanations) > 1 else explanations[0] if explanations else None,
            "message": f"Generated SHAP explanations for {len(features_df)} prediction(s)"
        }
    
    @staticmethod
    def _generate_summary(positive_factors: List[Dict], negative_factors: List[Dict]) -> str:
        """Generate human-readable summary of key factors."""
        summary_parts = []
        
        if positive_factors:
            top_positive = positive_factors[0]
            summary_parts.append(
                f"Strongly driven towards Success by {top_positive['feature']} ({top_positive['value']:.2f})"
            )
        
        if negative_factors:
            top_negative = negative_factors[0]
            summary_parts.append(
                f"Pulled towards Failure by {top_negative['feature']} ({top_negative['value']:.2f})"
            )
        
        if not summary_parts:
            summary_parts.append("Prediction is driven by balanced contribution of multiple factors")
        
        return ". ".join(summary_parts)
    
    @staticmethod
    def get_global_feature_importance(
        model: Any,
        scaler: Any,
        training_data: pd.DataFrame,
        feature_columns: List[str],
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """
        Calculate global feature importance using SHAP.
        
        Args:
            model: Trained XGBoost model
            scaler: Fitted scaler
            training_data: Training dataset
            feature_columns: Feature names
            sample_size: Number of samples to use for SHAP calculation
            
        Returns:
            Dictionary with global importance scores
        """
        # Sample data
        if len(training_data) > sample_size:
            sample_idx = np.random.choice(len(training_data), sample_size, replace=False)
            data_sample = training_data.iloc[sample_idx]
        else:
            data_sample = training_data
        
        # Scale
        data_scaled = scaler.transform(data_sample)
        
        # Create explainer and get SHAP values
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(data_scaled)
        
        # Handle binary classification
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Success class
        
        # Calculate mean absolute SHAP values
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        # Build importance dictionary
        importance = {}
        for feat_name, importance_val in zip(feature_columns, mean_abs_shap):
            importance[feat_name] = float(importance_val)
        
        # Sort by importance
        sorted_importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        return {
            "status": "success",
            "feature_importance": sorted_importance,
            "sample_size_used": len(data_sample),
            "message": "Global feature importance calculated using SHAP"
        }
