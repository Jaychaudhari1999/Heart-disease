import json
import pickle
import numpy as np
import pandas as pd
import config
from src.database import get_data_collection


class HeartDisease():

    def __init__(self):
        pass

    def load_model(self):
        """Loads the pre-trained Logistic Regression model from the artifact path."""
        with open(config.ML_MODEL_PATH, "rb") as f:
            self.model = pickle.load(f)
        return ""

    def load_column_data(self):
        """Loads categorical mapping dictionary from the artifact path."""
        with open(config.INPUT_COLUMN_DATA, "r") as f:
            self.input_columns = json.load(f)
        return self.input_columns

    def get_random_sample(self, desired_class):
        """Returns a random dataset row that the model predicts as desired_class."""
        self.load_model()
        self.load_column_data()

        frame = pd.read_csv(config.DATA_PATH)
        feature_frame = frame.drop(columns="target")
        predictions = self.model.predict(feature_frame)

        valid_rows = frame["ca"].between(0, 3)
        source_fields = {"sex": "gender"}
        for field, mapping in self.input_columns.items():
            source_field = source_fields.get(field, field)
            valid_rows &= frame[source_field].isin(set(mapping.values()))

        candidates = frame.loc[valid_rows & (predictions == desired_class)]
        if candidates.empty:
            raise ValueError(f"No supported samples found for class {desired_class}")

        row = candidates.sample(n=1).iloc[0]
        sample = {
            "age": int(row["age"]),
            "trestbps": float(row["trestbps"]),
            "chol": float(row["chol"]),
            "thalach": float(row["thalach"]),
            "oldpeak": float(row["oldpeak"]),
            "ca": int(row["ca"]),
        }
        for field, mapping in self.input_columns.items():
            source_field = source_fields.get(field, field)
            value = int(row[source_field])
            sample[field] = next(
                label for label, mapped_value in mapping.items()
                if mapped_value == value
            )

        return sample

    def create_test_df(self):
        """Creates 1xN NumPy test array and converts to DataFrame."""
        self.load_model()
        self.load_column_data()

        test_array = np.zeros((1, self.model.n_features_in_))

        # Validate all categorical fields exist before indexing
        categorical_fields = ["sex", "cp", "fbs", "restecg", "exang", "slope", "thal"]
        for field in categorical_fields:
            val = str(self.data.get(field, "")).strip().lower()
            field_map = self.input_columns.get(field, {})
            if val not in field_map:
                # Check if input is a raw numeric code (e.g., 0, 1) matching mapped values
                matched_label = next((k for k, v in field_map.items() if str(v) == val), None)
                if matched_label:
                    self.data[field] = matched_label
                else:
                    allowed = list(field_map.keys())
                    raise ValueError(
                        f"Invalid value '{val}' for field '{field}'. Allowed values: {allowed}"
                    )

        # Numerical fields
        test_array[0, 0] = self.data["age"]

        # Categoricals mapped via JSON
        test_array[0, 1] = self.input_columns["sex"][self.data["sex"]]
        test_array[0, 2] = self.input_columns["cp"][self.data["cp"]]

        # Numerical fields
        test_array[0, 3] = self.data["trestbps"]
        test_array[0, 4] = self.data["chol"]

        # Categoricals mapped via JSON
        test_array[0, 5] = self.input_columns["fbs"][self.data["fbs"]]
        test_array[0, 6] = self.input_columns["restecg"][self.data["restecg"]]

        # Numerical field
        test_array[0, 7] = self.data["thalach"]

        # Categoricals mapped via JSON
        test_array[0, 8] = self.input_columns["exang"][self.data["exang"]]

        # Numerical field
        test_array[0, 9] = self.data["oldpeak"]

        # Categoricals mapped via JSON
        test_array[0, 10] = self.input_columns["slope"][self.data["slope"]]

        # Numerical field
        test_array[0, 11] = self.data["ca"]

        # Categoricals mapped via JSON
        test_array[0, 12] = self.input_columns["thal"][self.data["thal"]]

        self.test_df = pd.DataFrame(
            test_array, columns=self.model.feature_names_in_
        )

    def predict(self, user_input_data):
        """Casts types, normalizes string categories, and returns prediction."""
        self.data = dict(user_input_data)

        # Cast continuous and count values
        self.data["age"] = int(self.data["age"])
        self.data["trestbps"] = float(self.data["trestbps"])
        self.data["chol"] = float(self.data["chol"])
        self.data["thalach"] = float(self.data["thalach"])
        self.data["oldpeak"] = float(self.data["oldpeak"])
        self.data["ca"] = int(self.data["ca"])

        # Normalize string categoricals for dictionary lookup
        self.data["sex"] = str(self.data["sex"]).strip().lower().replace(" ", "_")
        self.data["cp"] = str(self.data["cp"]).strip().lower().replace(" ", "_")
        self.data["fbs"] = str(self.data["fbs"]).strip().lower().replace(" ", "_")
        self.data["restecg"] = str(self.data["restecg"]).strip().lower().replace(" ", "_")
        self.data["exang"] = str(self.data["exang"]).strip().lower().replace(" ", "_")
        self.data["slope"] = str(self.data["slope"]).strip().lower().replace(" ", "_")
        self.data["thal"] = str(self.data["thal"]).strip().lower().replace(" ", "_")

        # Build test DataFrame and run model inference
        self.create_test_df()
        self.prediction = self.model.predict(self.test_df)

        return int(self.prediction[0]), self.data   
    
    def save_data_in_db(self, user_id=None, user_email=None):
        """Saves user input and predicted class to MongoDB."""
        from datetime import datetime

        # Convert ImmutableMultiDict / dict to a standard Python dictionary
        input_data = dict(self.data)

        # Handle prediction whether it is an array/list or a single scalar
        pred_value = int(self.prediction[0]) if hasattr(self.prediction, "__getitem__") else int(self.prediction)
        input_data["Prediction"] = pred_value
        if user_id:
            input_data["user_id"] = user_id
        if user_email:
            input_data["user_email"] = user_email
        input_data["created_at"] = datetime.utcnow().isoformat()

        # Persist to MongoDB
        collection = get_data_collection()
        insert_result = collection.insert_one(input_data)
        print(f"Data saved to DB successfully with _id: {insert_result.inserted_id}")