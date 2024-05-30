from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    jsonify,
    make_response,
    g,
)
from functools import wraps
import os
from os.path import join, dirname
from dotenv import load_dotenv
from pymongo import MongoClient
import jwt
from bson import ObjectId
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)

SECRET_KEY = "ini_kunci_rahasia_admin"

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

TOKEN_KEY = "bobaper"


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")


#-------------------------------------------  START ADMIN ROUTES ------------------------------------------------------#

@app.route("/login/admin", methods=["GET", "POST"])
def loginAdmin():
    error_msg = ""
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        result = db.admins.find_one({"email": email, "password": pw_hash})
        if result:
            payload = {
                "id": result["email"],
                "exp": datetime.now() + timedelta(days=1),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            response = make_response(redirect(url_for("dashboard")))
            response.set_cookie(TOKEN_KEY, token)
            return response
        else:
            error_msg = "Incorrect email or password"
    return render_template("admin/loginadmin.html", error_msg=error_msg)


# Fungsi untuk validasi akun admin
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get(TOKEN_KEY)
        if not token:
            return redirect(url_for("loginAdmin"))
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            g.user_email = payload.get("id")
            # Check if the user is the registered admin
            admin_account = db.admins.find_one({"email": g.user_email})
            if not admin_account:
                return redirect(url_for("loginAdmin"))
        except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
            return redirect(url_for("loginAdmin"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/register/admin", methods=["GET", "POST"])
def registeradmin():
    return render_template("admin/registeradmin.html")


@app.route("/register/admin/save", methods=["POST"])
def registeradminsave():
    email = request.form["email"]
    username = request.form["username"]
    password = request.form["password"]
    pass_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    doc = {
        "email": email,
        "username": username,
        "password": pass_hash,
        "date_created": datetime.now(),
    }
    db.admins.insert_one(doc)
    return jsonify({"result": "success"})


@app.route("/check-dup", methods=["POST"])
def check_dup():
    email = request.form["email"]
    exists = bool(db.admins.find_one({"email": email}))
    return jsonify({"result": "success", "exists": exists})


@app.route("/dashboard")
@login_required
def dashboard():
    user_info = db.admins.find_one({"email": g.user_email}, {"_id": False})
    products = db.produk.find()
    return render_template(
        "admin/dashboard.html",
        user_info=user_info,
        email=g.user_email,
        products=products,
    )


@app.route("/tambahproduk", methods=["GET", "POST"])
@login_required
def tambahproduk():
    if request.method == "POST":
        nama = request.form["nama"]
        harga = request.form["harga"]
        stock = request.form["stock"]
        nama_foto = request.files["foto"]

        today = datetime.now()
        mytime = today.strftime("%Y-%m-%d-%H-%M-%S")

        if nama_foto:
            nama_file_asli = nama_foto.filename
            nama_file_foto = nama_file_asli.split("/")[-1]
            nama_file = f"{mytime}-{nama_file_foto}"
            file_path = f"static/imgproduct/{nama_file}"
            nama_foto.save(file_path)
        else:
            nama_file_foto = None

        doc = {"nama": nama, "harga": harga, "stock": stock, "foto": nama_file}
        db.produk.insert_one(doc)
        return redirect(url_for("dashboard"))

    return render_template("admin/tambahproduk.html")


@app.route("/editproduk/<_id>", methods=["GET", "POST"])
@login_required
def editproduk(_id):
    if request.method == "POST":
        id = request.form["_id"]
        nama = request.form["nama"]
        harga = request.form["harga"]
        stock = request.form["stock"]
        nama_foto = request.files["foto"]
        doc = {"nama": nama, "harga": harga, "stock": stock}

        today = datetime.now()
        mytime = today.strftime("%Y-%m-%d-%H-%M-%S")

        if nama_foto:
            nama_file_asli = nama_foto.filename
            nama_file_foto = nama_file_asli.split("/")[-1]
            nama_file = f"{mytime}-{nama_file_foto}"
            file_path = f"static/imgproduct/{nama_file}"
            nama_foto.save(file_path)
            doc["foto"] = nama_file

        db.produk.update_one({"_id": ObjectId(id)}, {"$set": doc})
        return redirect(url_for("dashboard"))

    id = ObjectId(_id)
    data = db.produk.find_one({"_id": id})
    return render_template("admin/editproduk.html", data=data)


@app.route("/deleteproduk/<_id>")
@login_required
def delete_produk(_id):
    db.produk.delete_one({"_id": ObjectId(_id)})
    return redirect(url_for("dashboard"))


@app.route("/konfirmasipesananadmin", methods=["GET", "POST"])
def statuspesananadmin():
    return render_template("admin/konfirmasipesananadmin.html")


@app.route("/review/admin", methods=["GET", "POST"])
def reviewadmin():
    return render_template("admin/reviewadmin.html")


@app.route("/kelolauser/admin", methods=["GET", "POST"])
@login_required
def kelolauser():
    admins = list(db.admins.find())
    return render_template("admin/kelolauser.html", admins=admins)


@app.route("/logoutadmin")
def logoutadmin():
    response = make_response(redirect(url_for("loginAdmin")))
    response.set_cookie(TOKEN_KEY, "", expires=0)
    return response

#--------------------------------------END ADMIN ROUTES--------------------------------------------------#

#--------------------------------------Bagian User ROUTES--------------------------------------------------#

@app.route("/register/user", methods=["GET", "POST"])
def registeruser():
    return render_template("user/registeruser.html")


@app.route("/register/user/save", methods=["POST"])
def registerusersave():
    email = request.form["email"]
    username = request.form["username"]
    password = request.form["password"]
    password2 = request.form["password2"]

    # Check if passwords match
    if password != password2:
        return jsonify({"result": "error", "message": "Passwords do not match"})

    # Check if email already exists
    if db.users.find_one({"email": email}):
        return jsonify({"result": "error", "message": "Email already registered"})

    pass_hash = hashlib.sha256((password + password2).encode("utf-8")).hexdigest()

    now = datetime.now()

    doc = {
        "email": email,
        "username": username,
        "password": pass_hash,
        "date_created": now,
    }

    db.users.insert_one(doc)

    return jsonify({"result": "success"})


@app.route("/login/user", methods=["GET", "POST"])
def loginuser():
    return render_template("user/loginuser.html")


@app.route("/login/user/validate", methods=["POST"])
def validate_user_login():
    email = request.form["email"]
    password = request.form["password"]
    pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    result = db.users.find_one({"email": email, "password": pw_hash})

    if result:
        # Generate JWT token
        payload = {
            "id": result["email"],
            "exp": datetime.utcnow() + timedelta(days=1),  # Token expires in 1 day
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256").decode("utf-8")
        return jsonify({"result": "success", "token": token})
    else:
        return jsonify({"result": "error", "message": "Incorrect email or password"})

# Route for user profile ketika berhasil login
@app.route("/product")
def product():
    token = request.args.get("token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("email")
        # Fetch user data or perform any necessary actions
        return render_template("user/product.html", email=email)
    except jwt.ExpiredSignatureError:
        return "Token expired. Please login again."
    except jwt.InvalidTokenError:
        return "Invalid token. Please login again."


@app.route("/profile", methods=["GET", "POST"])
def profile():
    return render_template("user/profile.html")


@app.route("/shoppingcart", methods=["GET", "POST"])
def shoppingcart():
    return render_template("user/shoppingcart.html")

#--------------------------------------END USER ROUTES----------------------------------------------------#


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
