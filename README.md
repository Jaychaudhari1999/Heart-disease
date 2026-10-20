# CardioPulse — Heart Disease Prediction

CardioPulse is a Flask web application that uses a pre-trained logistic regression model to estimate a heart-disease class from a set of health measurements. It includes account registration and login, a browser-based prediction form, and optional storage of prediction inputs in MongoDB.

> **Medical disclaimer:** This project is for educational and demonstration purposes only. Its predictions are not a diagnosis or medical advice. Do not use them to make healthcare decisions; consult a qualified healthcare professional.

## Features

- Register, log in, and reset a password using a username or email and date of birth.
- Submit health measurements through the web form and receive a model prediction.
- Retrieve categorical input options and sample inputs from the bundled dataset.
- Store prediction inputs and results in MongoDB.
- Explore the model training workflow in the Jupyter notebook.

## Requirements

- Python 3.10 or later recommended.
- Azure Cosmos DB for MongoDB (configured by default in `config.py`) or a MongoDB instance for registration, login, password reset, and prediction-history storage.
- Python packages are listed in `requirements.txt`. It includes the Flask app's runtime dependencies and the packages used by the model-training notebook.

Install the dependencies in a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The serialized model in `artifact/` was created with scikit-learn. Pickle artifacts can be incompatible across scikit-learn versions, so use a compatible version if model loading fails.

## Run locally

1. Start MongoDB on `localhost:27017`. The application uses the `HeartDisease_db` database and creates/uses its collections as needed.
2. From the project root, configure non-default secrets and start the Flask app:

   ```powershell
   $env:SECRET_KEY = "replace-with-a-long-random-secret"
   $env:JWT_SECRET_KEY = "replace-with-another-long-random-secret"
   python app.py
   ```

3. Open [http://localhost:5005](http://localhost:5005) in a browser and register an account.

The app binds to `0.0.0.0:5005`; these settings and the MongoDB URL are defined in `config.py`. The current startup command enables Flask debug mode and is intended for local development only. Do not expose it directly to the internet or use the default secrets in a deployed environment.

### Security note

This codebase is a demo, not production-ready authentication: account passwords are currently stored in MongoDB as plain text, and password reset verifies the date of birth provided at registration. Do not use real personal or medical information with an internet-accessible deployment.

## Prediction inputs

Each prediction uses these 13 model features:

| Feature | Description |
| --- | --- |
| `age` | Age in years |
| `sex` | Categorical sex option |
| `cp` | Chest-pain category |
| `trestbps` | Resting blood pressure |
| `chol` | Serum cholesterol |
| `fbs` | Fasting blood sugar category |
| `restecg` | Resting electrocardiographic category |
| `thalach` | Maximum heart rate achieved |
| `exang` | Exercise-induced angina category |
| `oldpeak` | ST depression induced by exercise |
| `slope` | Slope of the peak exercise ST segment |
| `ca` | Number of major vessels (0–3) |
| `thal` | Thalassemia category |

Categorical labels and their numeric encodings are stored in `artifact/categorical_data_mapping.json`. Numeric ranges and option lists are also presented in the web form.

The prediction endpoint returns class `1` as **Heart Disease Detected** and class `0` as **Normal / No Disease**. This is a classification result from the bundled model, not a calibrated clinical risk score.

## HTTP routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Redirect to login |
| `GET` | `/register_page` | Registration page |
| `GET` | `/login_page` | Login page |
| `GET` | `/forget_password_page` | Password reset page |
| `GET` | `/prediction_page` | Prediction form |
| `POST` | `/register` | Create an account |
| `POST` | `/login` | Authenticate and return a JWT |
| `POST` | `/forget_password` | Reset a password after a date-of-birth check |
| `GET` | `/sex_options`, `/cp_options`, `/fbs_options`, `/restecg_options`, `/exang_options`, `/slope_options`, `/thal_options` | Get categorical form options |
| `GET` | `/random_sample/<desired_class>` | Get a sample row for class `0` or `1` |
| `POST` | `/predict_heart_disease` | Return a prediction; requires a JWT |

For `/predict_heart_disease`, send the 13 input fields as JSON or form data and include the login token in the `Authorization` header as `Bearer <token>`.

## Project layout

```text
.
├── app.py                              # Flask routes and application startup
├── config.py                           # Host, MongoDB, secret, and artifact settings
├── artifact/
│   ├── logistic_reg_heart_data.pkl     # Pre-trained model
│   └── categorical_data_mapping.json   # Category labels and encodings
├── data/
│   └── heart.csv                       # Dataset used for sample inputs
├── src/
│   ├── database.py                     # MongoDB collection helpers
│   ├── utils.py                        # Model loading, input preparation, prediction
│   └── notebook/                       # Model training notebook
├── static/                             # Static assets
└── templates/                          # Login, registration, reset, and prediction pages
```

## Configuration and data

- `SECRET_KEY` and `JWT_SECRET_KEY` can be supplied through environment variables. The fallback values in `config.py` are development defaults and must be replaced for any deployment.
- The MongoDB / Azure Cosmos DB URL and database/collection names are configured in `config.py` and can also be overridden via the `MONGO_URL` environment variable.
- Model, mapping, and dataset paths are derived from the current working directory. Run `python app.py` from the project root so those paths resolve correctly.
- Prediction history is written to MongoDB under the configured data collection. The app logs a warning if that write fails, but still returns the prediction.

## Model and dataset

The pre-trained model is loaded from `artifact/logistic_reg_heart_data.pkl`; the categorical mappings are loaded from `artifact/categorical_data_mapping.json`. The sample-input route reads `data/heart.csv` and selects a row predicted as the requested class. The notebook `src/notebook/2. Logistic Regression - Heart Data.ipynb` contains the model training and evaluation workflow.
