from pymongo import MongoClient
import jwt
from datetime import datetime, timedelta
import hashlib
from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
    make_response,
)
import os
from os.path import join, dirname
from dotenv import load_dotenv

app = Flask(__name__)

SECRET_KEY = "thisismysecretkey"

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

TOKEN_KEY = "mytoken"


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")


@app.route("/login/admin", methods=["GET", "POST"])
def loginAdmin():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        result = db.admins.find_one({"email": email, "password": pw_hash})

        if result:
            payload = {
                "id": result["email"],
                "exp": datetime.utcnow() + timedelta(days=1),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            return jsonify({"result": "success", "token": token})
        else:
            return jsonify({"result": "fail", "msg": "Incorrect email or password"})
    return render_template("admin/loginadmin.html")


@app.route("/register/admin", methods=["GET", "POST"])
def registeradmin():
    return render_template("admin/registeradmin.html")


@app.route("/register/admin/save", methods=["POST"])
def register():
    email = request.form["email"]
    username = request.form["username"]
    password = request.form["password"]
    pass_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    doc = {"email": email, "username": username, "password": pass_hash}
    db.admins.insert_one(doc)
    return jsonify({"result": "success"})


@app.route("/check-dup", methods=["POST"])
def check_dup():
    email = request.form["email"]
    exists = bool(db.admins.find_one({"email": email}))
    return jsonify({"result": "success", "exists": exists})


@app.route("/dashboard/<email>")
def dashboard(email):
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        status = email == payload.get("id")
        user_info = db.admins.find_one({"email": email}, {"_id": False})
        return render_template(
            "admin/dashboard.html", user_info=user_info, status=status
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("loginadmin"))


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
