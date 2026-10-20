import os

FLASK_HOST = "0.0.0.0"
FLASK_PORT = 8000

# MongoDB details
MONGO_URL = "mongodb://localhost:27017"
db_name = "HeartDisease_db"
data_collection_name = "disease_prediction_data"
user_collection_name = "users"
_collection_name = "users"  # Backward compatibility for legacy references

# Security & Session
SECRET_KEY = os.environ.get("SECRET_KEY", "cardiopulse_secure_secret_key_2026_heart_pred")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "cardiopulse_jwt_secret_key_2026_super_secure_32bytes_min")

# File & Artifact Paths
ML_MODEL_PATH = os.path.join(os.getcwd(), "artifact", "logistic_reg_heart_data.pkl")
DATA_PATH = os.path.join(os.getcwd(), "data", "heart.csv")
INPUT_COLUMN_DATA = os.path.join(os.getcwd(), "artifact", "categorical_data_mapping.json")
