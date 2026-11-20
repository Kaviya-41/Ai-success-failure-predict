from fastapi import APIRouter, HTTPException

from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    WhatIfRequest,
    WhatIfResponse
)

from app.services.ml_service import MLService


router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"]
)


@router.post(
    "/predict",
    response_model=PredictionResponse
)
def predict_project(
    request: PredictionRequest
):
    """
    Run the Success/Failure IF-ELSE algorithm.
    """

    try:

        metrics = request.model_dump()

        result = MLService.predict_single(
            metrics
        )

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post(
    "/what-if",
    response_model=WhatIfResponse
)
def what_if_prediction(
    request: WhatIfRequest
):
    """
    Run the algorithm for what-if simulation.
    """

    try:

        simulated_values = (
            request.current_values.model_dump()
        )

        simulated_result = (
            MLService.predict_single(
                simulated_values
            )
        )

        return {
            "base_prediction": None,
            "simulated_prediction": simulated_result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"What-if prediction failed: {str(e)}"
        )