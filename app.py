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
    produk = list(db.produk.find())
    return render_template("index.html", produk=produk)


@app.route("/about", methods=["GET", "POST"])
def about():
    token = request.cookies.get("token")
    status = False
    username = None
    pesan = 0
    user_info = None

    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user_info = db.users.find_one({"_id": ObjectId(user_id)})
            if user_info:
                status = True
                username = user_info.get("username")
                pesan = db.cartuser.count_documents({"user_id": str(user_info["_id"])})
        except jwt.ExpiredSignatureError:
            pass
        except jwt.InvalidTokenError:
            pass

    return render_template(
        "about.html",
        user_info=user_info,
        status=status,
        username=username,
        pesan=pesan,
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    token = request.cookies.get("token")
    status = False
    username = None
    pesan = 0
    user_info = None

    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user_info = db.users.find_one({"_id": ObjectId(user_id)})
            if user_info:
                status = True
                username = user_info.get("username")
                pesan = db.cartuser.count_documents({"user_id": str(user_info["_id"])})
        except jwt.ExpiredSignatureError:
            pass
        except jwt.InvalidTokenError:
            pass

    return render_template(
        "contact.html",
        user_info=user_info,
        status=status,
        username=username,
        pesan=pesan,
    )


# -------------------------------------------  START ADMIN ROUTES ------------------------------------------------------#


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
        harga = int(request.form["harga"])
        stock = int(request.form["stock"])
        nama_foto = request.files["foto"]

        if nama_foto:
            # Mengambil ekstensi file asli
            ekstensi_file = nama_foto.filename.split(".")[-1]
            nama_file = f"{nama}.{ekstensi_file}"
            file_path = f"static/imgproduct/{nama_file}"
            nama_foto.save(file_path)
        else:
            nama_file = None

        print(nama_file)
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
        harga = float(request.form["harga"])
        stock = int(request.form["stock"])
        nama_foto = request.files["foto"]
        doc = {"nama": nama, "harga": harga, "stock": stock}

        if nama_foto:
            # Mengambil ekstensi file asli
            ekstensi_file = nama_foto.filename.split(".")[-1]
            nama_file = f"{nama}.{ekstensi_file}"
            file_path = f"static/imgproduct/{nama_file}"
            nama_foto.save(file_path)
            doc["foto"] = nama_file

        db.produk.update_one({"_id": ObjectId(id)}, {"$set": doc})
        return redirect(url_for("dashboard"))

    id = ObjectId(_id)
    data = db.produk.find_one({"_id": id})
    return render_template("admin/editproduk.html", data=data)


from bson import ObjectId


@app.route("/deleteproduk/<_id>")
@login_required
def delete_produk(_id):
    deleted_product = db.produk.find_one_and_delete({"_id": ObjectId(_id)})
    if deleted_product:
        db.cartuser.delete_many({"product_id": str(deleted_product["_id"])})
        return redirect(url_for("dashboard"))
    else:
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
    users = list(db.users.find())
    return render_template("admin/kelolauser.html", admins=admins, users=users)


@app.route("/logoutadmin")
def logoutadmin():
    response = make_response(redirect(url_for("loginAdmin")))
    response.set_cookie(TOKEN_KEY, "", expires=0)
    return response


# --------------------------------------END ADMIN ROUTES--------------------------------------------------#

# --------------------------------------Bagian User ROUTES--------------------------------------------------#


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

    pass_hash = hashlib.sha256((password).encode("utf-8")).hexdigest()

    now = datetime.now()

    doc = {
        "email": email,
        "username": username,
        "password": pass_hash,
        "date_created": now,
        "shopping_cart": 0,
    }

    db.users.insert_one(doc)

    return jsonify({"result": "success"})


def token_required(f):
    def decorator(*args, **kwargs):
        token = request.cookies.get("token")
        if not token:
            return redirect(
                url_for("loginuser", error_msg="Token missing. Please login again.")
            )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user = db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise jwt.InvalidTokenError()
            return f(user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return redirect(
                url_for("loginuser", error_msg="Token expired. Please login again.")
            )
        except jwt.InvalidTokenError:
            return redirect(
                url_for("loginuser", error_msg="Invalid token. Please login again.")
            )

    decorator.__name__ = f.__name__
    return decorator


@app.route("/login/user", methods=["GET", "POST"])
def loginuser():
    return render_template("user/loginuser.html")


@app.route("/login/user/validate", methods=["POST"])
def validate_user_login():
    email = request.form["email"]
    password = request.form["password"]
    pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    user = db.users.find_one({"email": email, "password": pw_hash})

    if user:
        payload = {
            "user_id": str(user["_id"]),
            "exp": datetime.now() + timedelta(days=1),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        response = jsonify({"result": "success", "token": token})
        response.set_cookie("token", token, httponly=True)
        return response
    else:
        return jsonify({"result": "error", "message": "Incorrect email or password"})


@app.route("/product")
def product():
    token = request.cookies.get("token")
    if not token:
        return redirect(
            url_for("loginuser", error_msg="Token missing. Please login again.")
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        user = db.users.find_one({"_id": ObjectId(user_id)})
        produk = list(db.produk.find())
        username = user.get("username")
        pesan = db.cartuser.count_documents({"user_id": str(user["_id"])})
        return render_template(
            "user/produkuser.html",
            user_id=user_id,
            produk=produk,
            username=username,
            pesan=pesan,
        )
    except jwt.ExpiredSignatureError:
        return redirect(
            url_for("loginuser", error_msg="Token expired. Please login again.")
        )
    except jwt.InvalidTokenError:
        return redirect(
            url_for("loginuser", error_msg="Invalid token. Please login again.")
        )


@app.route("/shoppingcart", methods=["GET"])
@token_required
def shoppingcart(user):
    cart_items = list(db.cartuser.find({"user_id": str(user["_id"])}))
    total_harga = 0
    for item in cart_items:
        product = db.produk.find_one({"_id": ObjectId(item["product_id"])})
        item["product_name"] = product.get("nama")
        item["product_price"] = product.get("harga")
        item["product_photo"] = f"imgproduct/{product['nama']}.jpg"
        total_harga += item["product_price"] * item["quantity"]
    pesan = db.cartuser.count_documents({"user_id": str(user["_id"])})
    username = user.get("username")
    return render_template(
        "user/shoppingcart.html",
        username=username,
        cart_items=cart_items,
        pesan=pesan,
        total_harga=total_harga,
    )


@app.route("/addshoppingcart", methods=["POST"])
@token_required
def add_shopping_cart(user):
    try:
        product_id = request.form.get("product_id")
        product = db.produk.find_one({"_id": ObjectId(product_id)})
        if not product or product["stock"] <= 0:
            return jsonify({"result": "error", "message": "Product not available."})

        # Check if the product is already in the cart
        cart_item = db.cartuser.find_one(
            {"user_id": str(user["_id"]), "product_id": product_id}
        )

        if cart_item:
            # If product is already in the cart, update the quantity
            db.cartuser.update_one({"_id": cart_item["_id"]}, {"$inc": {"quantity": 1}})
        else:
            # If product is not in the cart, add it
            cart_item = {
                "user_id": str(user["_id"]),
                "product_id": product_id,
                "product_name": product.get("nama"),
                "product_price": product.get("harga"),
                "product_photo": product.get("foto"),
                "quantity": 1,
            }
            db.cartuser.insert_one(cart_item)

        return jsonify({"result": "success", "message": "Product added to cart."})
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)})


@app.route("/updatecart", methods=["POST"])
def update_cart():
    try:
        token = request.cookies.get("token")
        if not token:
            return jsonify(
                {"result": "error", "message": "Token missing. Please login again."}
            )

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        product_id = request.json.get("product_id")
        action = request.json.get("action")

        # Update cart based on action
        if action == "increment":
            db.cartuser.update_one(
                {"user_id": str(user_id), "product_id": str(product_id)},
                {"$inc": {"quantity": 1}},
            )
        elif action == "decrement":
            db.cartuser.update_one(
                {"user_id": str(user_id), "product_id": str(product_id)},
                {"$inc": {"quantity": -1}},
            )
            db.cartuser.delete_one(
                {
                    "user_id": str(user_id),
                    "product_id": str(product_id),
                    "quantity": {"$lte": 0},
                }
            )

        return jsonify({"result": "success"}), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    return render_template("user/checkout.html")


@app.route("/review", methods=["GET", "POST"])
def review():
    return render_template("user/review.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    return render_template("user/profile.html")




@app.route("/logoutuser", methods=["GET", "POST"])
def logoutuser():
    response = make_response(redirect(url_for("loginuser")))
    response.set_cookie(TOKEN_KEY, "", expires=0)
    return response


# --------------------------------------END USER ROUTES----------------------------------------------------#


if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=True)
