import datetime
import pymongo
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request,
)
import config
from src.utils import HeartDisease

heart_disease_obj = HeartDisease()

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
app.config["SECRET_KEY"] = config.SECRET_KEY
jwt = JWTManager(app)

from src.database import mongo_client, db, get_user_collection, ensure_user_indexes

user_collection = get_user_collection()


@app.route("/")
def home():
    return redirect(url_for("login_page"))


@app.route("/register_page")
def register_page():
    return render_template("register.html")


@app.route("/login_page")
def login_page():
    return render_template("login.html")


@app.route("/forget_password_page")
def forget_password_page():
    return render_template("forget_password.html")


@app.route("/prediction_page")
def prediction_page():
    return render_template("index.html")


def find_user_by_identifier(ident):
    """
    Find user in MongoDB by username, email, phone number, or prefix (case-insensitive).
    """
    if not ident:
        return None
    import re
    ident_clean = str(ident).strip()

    ident_pattern = re.compile(f"^{re.escape(ident_clean)}$", re.IGNORECASE)
    user_doc = user_collection.find_one({
        "$or": [
            {"user_name": ident_pattern},
            {"username": ident_pattern},
            {"email_id": ident_pattern},
            {"email": ident_pattern},
            {"contact_number": ident_clean},
            {"contact_no": ident_clean},
        ]
    })
    if user_doc:
        return user_doc

    prefix_pattern = re.compile(f"^{re.escape(ident_clean)}(\\s+.*)?$", re.IGNORECASE)
    user_doc = user_collection.find_one({
        "$or": [
            {"user_name": prefix_pattern},
            {"username": prefix_pattern},
        ]
    })
    if user_doc:
        return user_doc

    if "@" in ident_clean:
        local_part = ident_clean.split("@")[0]
        local_base = re.sub(r"\d+$", "", local_part)
        domain = ident_clean.split("@")[1]
        fuzzy_email = re.compile(f"^{re.escape(local_base)}.*@{re.escape(domain)}$", re.IGNORECASE)
        user_doc = user_collection.find_one({
            "$or": [
                {"email_id": fuzzy_email},
                {"email": fuzzy_email},
            ]
        })
        if user_doc:
            return user_doc
    else:
        local_base = re.sub(r"\d+$", "", ident_clean)
        fuzzy_prefix = re.compile(f"^{re.escape(local_base)}.*@", re.IGNORECASE)
        user_doc = user_collection.find_one({
            "$or": [
                {"email_id": fuzzy_prefix},
                {"email": fuzzy_prefix},
            ]
        })
        if user_doc:
            return user_doc

    return None


@app.route("/register", methods=["POST"])
def register():
    try:
        ensure_user_indexes()
        user_data = request.get_json(silent=True) or request.form
        user_name = str(user_data.get("user_name") or "").strip()
        password = str(user_data.get("password") or "").strip()
        email_id = str(user_data.get("email_id") or "").strip()
        contact_number = str(user_data.get("contact_number") or "").strip()
        dob = str(user_data.get("dob") or "").strip()

        if not user_name or not email_id or not password:
            return jsonify({"status": "failure", "message": "User name, email, and password are required"})

        import re
        email_pat = re.compile(f"^{re.escape(email_id)}$", re.IGNORECASE)
        name_pat = re.compile(f"^{re.escape(user_name)}$", re.IGNORECASE)
        response = user_collection.find_one({
            "$or": [
                {"email_id": email_pat},
                {"email": email_pat},
                {"user_name": name_pat},
                {"username": name_pat},
            ]
        })
        if not response:
            user_collection.insert_one({
                "user_name": user_name,
                "username": user_name,
                "password": password,
                "email_id": email_id,
                "email": email_id,
                "contact_number": contact_number,
                "contact_no": contact_number,
                "dob": dob,
            })
            print(f"[REGISTER SUCCESS] Registered user: {user_name} ({email_id})", flush=True)
            return jsonify({"status": "success", "message": "User Registered Successfully"})
        else:
            return jsonify({"status": "exists", "message": "User with this username or email already exists"})
    except pymongo.errors.DuplicateKeyError:
        return jsonify({"status": "exists", "message": "User with this username or email already exists"})
    except Exception as e:
        print(f"Registration error: {e}", flush=True)
        return jsonify({"status": "failure", "message": f"Server error: {str(e)}"})


@app.route("/login", methods=["POST"])
def login():
    try:
        user_data = request.get_json(silent=True) or request.form
        raw_ident = str(
            user_data.get("user_name")
            or user_data.get("username")
            or user_data.get("email_id")
            or user_data.get("email")
            or ""
        ).strip()
        raw_pwd = str(user_data.get("password") or "").strip()

        print(f"[LOGIN ATTEMPT] Input: identifier={repr(raw_ident)}, password_len={len(raw_pwd)}", flush=True)

        if not raw_ident or not raw_pwd:
            return jsonify({"status": "failure", "message": "Username/email and password are required"})

        # Step 1: Look up user document
        user_doc = find_user_by_identifier(raw_ident)
        if not user_doc:
            print(f"[LOGIN FAILED] No user found for: {repr(raw_ident)}", flush=True)
            return jsonify({
                "status": "failure",
                "message": f"User '{raw_ident}' not found. Please verify your username/email or register."
            })

        # Step 2: Validate password (exact, stripped, or case-insensitive)
        stored_pwd = str(user_doc.get("password") or "")
        is_pwd_match = (
            stored_pwd == raw_pwd
            or stored_pwd.strip() == raw_pwd
            or stored_pwd.strip().lower() == raw_pwd.lower()
        )

        if not is_pwd_match:
            print(f"[LOGIN FAILED] Password mismatch for: {user_doc.get('user_name')}", flush=True)
            return jsonify({
                "status": "failure",
                "message": "Incorrect password. Please try again or use 'Forgot Password'."
            })

        # Step 3: Success - issue JWT token
        actual_name = user_doc.get("user_name") or user_doc.get("username") or raw_ident
        access_token = create_access_token(
            identity=actual_name,
            expires_delta=datetime.timedelta(days=1),
        )
        print(f"[LOGIN SUCCESS] Logged in as: {actual_name}", flush=True)
        return jsonify({
            "status": "success",
            "message": "Login Successful",
            "access_token": access_token,
            "user_name": actual_name,
        })
    except Exception as e:
        print(f"Login error: {e}", flush=True)
        return jsonify({"status": "failure", "message": f"Server error: {str(e)}"})


@app.route("/forget_password", methods=["POST"])
def forget_password():
    try:
        user_data = request.get_json(silent=True) or request.form
        user_name = str(user_data.get("user_name") or "").strip()
        dob = str(user_data.get("dob") or "").strip()
        new_password = str(user_data.get("new_password") or "").strip()

        if not user_name or not dob or not new_password:
            return jsonify({
                "status": "failure",
                "message": "Username/email, date of birth, and new password are required"
            })

        # Step 1: Look up user document
        user_doc = find_user_by_identifier(user_name)
        if not user_doc:
            return jsonify({
                "status": "failure",
                "message": f"User '{user_name}' not found. Please check your username or email."
            })

        # Step 2: Check DOB match
        stored_dob = str(user_doc.get("dob") or "").strip()
        if stored_dob != dob:
            return jsonify({
                "status": "failure",
                "message": "Date of Birth does not match our records for this user."
            })

        # Step 3: Update plain text password in MongoDB
        user_collection.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"password": new_password}}
        )

        # Step 4: Fetch updated entry
        updated_entry = user_collection.find_one({"_id": user_doc["_id"]})
        if updated_entry:
            updated_entry["_id"] = str(updated_entry["_id"])
        print(f"[FORGOT PASSWORD] Password updated for: {user_doc.get('user_name')}", flush=True)

        return jsonify({
            "status": "success",
            "message": "Password updated successfully",
            "updated_user": updated_entry,
        })
    except Exception as e:
        print(f"Forget password error: {e}", flush=True)
        return jsonify({"status": "failure", "message": f"Server error: {str(e)}"})


# --- Categorical Options for Frontend Dropdowns ---


@app.route("/sex_options")
def sex_options():
    col_data = heart_disease_obj.load_column_data()
    return jsonify(list(col_data["sex"].keys()))


@app.route("/cp_options")
def cp_options():
    col_data = heart_disease_obj.load_column_data()
    return jsonify(list(col_data["cp"].keys()))


@app.route("/fbs_options")
def fbs_options():
    col_data = heart_disease_obj.load_column_data()
    return jsonify(list(col_data["fbs"].keys()))


@app.route("/restecg_options")
def restecg_options():
    col_data = heart_disease_obj.load_column_data()
    return jsonify(list(col_data["restecg"].keys()))


@app.route("/exang_options")
def exang_options():
    col_data = heart_disease_obj.load_column_data()
    return jsonify(list(col_data["exang"].keys()))


@app.route("/slope_options")
def slope_options():
    col_data = heart_disease_obj.load_column_data()
    return jsonify(list(col_data["slope"].keys()))


@app.route("/thal_options")
def thal_options():
    col_data = heart_disease_obj.load_column_data()
    return jsonify(list(col_data["thal"].keys()))


@app.route("/random_sample/<int:desired_class>")
def random_sample(desired_class):
    if desired_class not in (0, 1):
        return jsonify({"message": "Class must be 0 or 1"}), 400

    try:
        sample = heart_disease_obj.get_random_sample(desired_class)
        return jsonify(sample)
    except ValueError as error:
        return jsonify({"message": str(error)}), 404


# --- Prediction Route (JWT Protected) ---


@app.route("/predict_heart_disease", methods=["POST"])
@jwt_required()
def predict_heart_disease():
    current_user = get_jwt_identity()
    user_input_data = request.get_json(silent=True) or request.form.to_dict()

    if not user_input_data:
        return jsonify({"error": "Missing input data"}), 400

    try:
        prediction, _ = heart_disease_obj.predict(user_input_data)
        try:
            heart_disease_obj.save_data_in_db(user_email=current_user)
        except Exception as db_err:
            print(f"Warning: Failed to save to database: {db_err}")
    except (KeyError, ValueError) as err:
        return jsonify({"error": str(err)}), 400

    result_text = "Heart Disease Detected" if int(prediction) == 1 else "Normal / No Disease"

    return jsonify({
        "Predicted Class": int(prediction),
        "Result": result_text,
    })


if __name__ == "__main__":
    print(f"Server running at http://{config.FLASK_HOST}:{config.FLASK_PORT}...")
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=True, use_reloader=False)