import os

FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.environ.get("PORT", os.environ.get("FLASK_PORT", 8000)))

# MongoDB / Azure Cosmos DB details
MONGO_URL = os.environ.get(
    "MONGO_URL",
    "mongodb+srv://dbuser8bojfo:Jay%401234@docdb-cluster-20261020-0958.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
)
db_name = os.environ.get("MONGO_DB_NAME", "HeartDisease_db")
data_collection_name = os.environ.get("MONGO_DATA_COLLECTION", "disease_prediction_data")
user_collection_name = os.environ.get("MONGO_USER_COLLECTION", "users")
_collection_name = user_collection_name  # Backward compatibility

# Security & Session
SECRET_KEY = os.environ.get("SECRET_KEY", "cardiopulse_secure_secret_key_2026_heart_pred")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "cardiopulse_jwt_secret_key_2026_super_secure_32bytes_min")

# File & Artifact Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_MODEL_PATH = os.path.join(BASE_DIR, "artifact", "logistic_reg_heart_data.pkl")
DATA_PATH = os.path.join(BASE_DIR, "data", "heart.csv")
INPUT_COLUMN_DATA = os.path.join(BASE_DIR, "artifact", "categorical_data_mapping.json")
