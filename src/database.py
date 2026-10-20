import pymongo
import config
mongo_client = pymongo.MongoClient(config.MONGO_URL)
db = mongo_client[config.db_name]

def get_data_collection():
    data_collection = db[config.data_collection_name]
    return data_collection

def get_user_collection():
    user_collection = db[config.user_collection_name]
    # Ensure index on email for unique accounts and fast lookups
    try:
        user_collection.create_index("email", unique=True)
    except Exception as e:
        print(f"Index creation note: {e}")
    return user_collection