import uvicorn
from fastapi import FastAPI
import joblib
from pydantic import BaseModel
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Any
import logging

from pydantic_core.core_schema import none_schema

#setup the basic config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#creat a app object
app = FastAPI(
    title = "Customer Churn Prediction API",
    description = "API for predicting customer churn Using Multiple ML models",
    version ="1.0.0"
)

#defining the global variable model
model = {}
scaler = None
encoders= {}
feature_order =[]

#defining the input features
class ChurnPredictionInput(BaseModel):
    total_spent:float
    avg_order_value:float
    order_frequency: float
    avg_freight: float
    avg_total_order: float
    favorite_category: str
    avg_product_weight: float
    customer_state: str
    preferred_payment: str
    favorite_month: int
    weekend_tendency: float
    recency_days: int
    customer_lifetime_days: int
    av_days_between_orders: float


    class Config:
        schema_extra = {
            "example": {
                "total_spend": 1500.50,
                "avg_order_value": 75.25,
                "order_frequency": 0.8,
                "avg_total_order": 90.55,
                "favorite_category": "electronics",
                "avg_product_weight": 2.5,
                "customer_state": "CA",
                "preferred_payment": "Credit_card",
                "favorite_month": 6,
                "weekend_tendency": 0.3,
                "recency_days": 45,
                "customer_lifetime_days": 365,
                "avg_days_between_orders": 30.5
            }
        }




class PredictionRequest(BaseModel):
    #define input features here
    logistics_regression: Dict[str, Any]
    random_forest: Dict[str, Any]
    xgboost: Dict[str, Any]
    ensemble_predictions : Dict[str, Any]

@app.on_event("startup")
async def load_models():
    "load trained model on startup"
    global scaler, encoders, feature_order

    try:
        #load the models
        model['logistic_regression'] = joblib.load('logistic_regression.joblib')
        model['random_forest'] = joblib.load('random_forest.joblib')
        model['xgboost'] = joblib.load('xgboost.joblib')

        #loading scaler
        scaler = joblib.load('churn_scaler.joblib')

        #loading encoders
        encoders = joblib.load('encoders.joblib')
 logger.info("Model and preprocessor loaded successfully!")
        logger.info(f'loaded encoders for : {list(encoders.keys())}')
        logger.info(f'loaded scaler for : {list(scaler.keys())}')
        logger.info(f'loaded feature order for : {feature_order}')

    except Exception as e:
        logger.error(f"Error loading models: {str(e)}")
        raise

@app.get("/")
def read_root():
    return{
        "message": "Customer Churn Prediction API",
        "available_models":['Logistic_regression', 'random_forest', 'xgboost']
        "endpoints":["/predict", "/health", "/models-info"]

    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return{
        "status": "health",
        "model_loaded": len(model),
        "available_models": list(model.keys())

    }

def preprocess_input(input_data: ChurnPredictionInput) -> tuple:
    """convert input to Dataframe and  handle preprocessing exactly like training"""
    #convert to dictionary then Dataframe
    data_dict = input_data.dict()
    df= pd.DataFrame([data_dict])

    #ensure features order ,matches training
    df= df[feature_order]

    #apply label encoding on categorical features
    categorical_features = ['favorite_category', 'customer_state', 'preferred_payment']
    for col in categorical_features:
        if col in encoders:
            try:
                #convert to string
                df[col] = df[col].astype(str)
                #apply the same label encoder use
                df[col] = encoders[col].transform(df[col])
            except ValueError as e:
                #handle unseen categorical
                logger.warning(f"unseen category in {col}: {df[col].values[0]}")
                raise HTPPException(
                    status_code =400,
                    details= f"Unknown category '{df[col].values[0]}' in feature '{col}'"
                )

            #now apply scaling to all features since categorical is now jhumerical
    df_scaled= pd.DataFrame(
        scaler.transform(df),
        columns = df.columns,
        index = df.index
    )

    return df_scaled, df


@app.post("/predict")
def predict(request: PredictionRequest):
    #using model to make predictions
    predictions = model.predict([[request.features1, request.features2]])
    return{"predictions":predictions}

        #load features
        feature_order = joblib.load("feature_order.joblib")
