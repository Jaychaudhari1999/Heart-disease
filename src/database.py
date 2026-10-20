import os
import pymongo
import config

try:
    import certifi
    ca_file = certifi.where()
except Exception:
    ca_file = None

def get_mongo_client():
    kwargs = {
        "serverSelectionTimeoutMS": int(os.environ.get("MONGO_TIMEOUT_MS", 5000)),
        "connectTimeoutMS": int(os.environ.get("MONGO_CONNECT_TIMEOUT_MS", 5000)),
        "socketTimeoutMS": int(os.environ.get("MONGO_SOCKET_TIMEOUT_MS", 5000)),
    }
    if ca_file and ("tls=true" in config.MONGO_URL.lower() or "ssl=true" in config.MONGO_URL.lower() or "mongodb+srv" in config.MONGO_URL.lower()):
        kwargs["tlsCAFile"] = ca_file
    return pymongo.MongoClient(config.MONGO_URL, **kwargs)

mongo_client = get_mongo_client()
db = mongo_client[config.db_name]

user_collection = db[config.user_collection_name]
data_collection = db[config.data_collection_name]

_indexes_created = False

def ensure_user_indexes():
    global _indexes_created
    if not _indexes_created:
        try:
            user_collection.create_index("email", unique=True, maxTimeMS=3000)
            _indexes_created = True
        except Exception as e:
            print(f"Index creation note: {e}")

def get_data_collection():
    return data_collection

def get_user_collection():
    return user_collection
