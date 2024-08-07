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
from werkzeug.utils import secure_filename
from math import ceil

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
    reviews = list(db.reviews.find().sort("created_at", -1))  # Fetch reviews
    # Fetch user data for each review to get the profile picture
    for review in reviews:
        review_user = db.users.find_one({"_id": ObjectId(review["user_id"])})
        review["profile_picture"] = review_user.get("profile_picture", "default.jpg")
        if "rating" not in review:
            review["rating"] = 0  # Default rating value if missing
    return render_template("index.html", produk=produk, reviews=reviews)


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
        user=user_info,
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
        user=user_info,
    )


# -------------------------------------------  MULAI ROUTES ADMIN ------------------------------------------------------#
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
            error_msg = "Email atau password salah"
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
            # Cek apakah user adalah admin yang terdaftar
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
            # Menghapus spasi dan membuat nama file aman untuk URL
            sanitized_nama = nama.replace(" ", "_")
            # Mendapatkan ekstensi file asli
            ekstensi_file = nama_foto.filename.split(".")[-1]
            nama_file = f"{sanitized_nama}.{ekstensi_file}"
            file_path = f"static/imgproduct/{nama_file}"
            nama_foto.save(file_path)
        else:
            nama_file = None
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
        harga = int(request.form["harga"])
        stock = int(request.form["stock"])
        nama_foto = request.files["foto"]
        doc = {"nama": nama, "harga": harga, "stock": stock}
        if nama_foto:
            # Menghapus spasi dan membuat nama file 
            sanitized_nama = nama.replace(" ", "_")
            # Mendapatkan ekstensi file asli
            ekstensi_file = nama_foto.filename.split(".")[-1]
            nama_file = f"{sanitized_nama}.{ekstensi_file}"
            file_path = f"static/imgproduct/{nama_file}"
            nama_foto.save(file_path)
            doc["foto"] = nama_file
        db.produk.update_one({"_id": ObjectId(id)}, {"$set": doc})
        # Memperbarui koleksi cartuser dengan detail produk yang baru
        cart_update_doc = {"product_name": nama, "product_price": harga}
        if nama_foto:
            cart_update_doc["product_photo"] = nama_file
        db.cartuser.update_many({"product_id": id}, {"$set": cart_update_doc})
        # Memperbarui koleksi orders dengan detail produk yang baru
        orders = db.orders.find({"cart_items.product_id": id})
        for order in orders:
            updated_cart_items = []
            for item in order["cart_items"]:
                if item["product_id"] == id:
                    item["product_name"] = nama
                    if nama_foto:
                        item["product_photo"] = nama_file
                updated_cart_items.append(item)
            db.orders.update_one(
                {"_id": order["_id"]}, {"$set": {"cart_items": updated_cart_items}}
            )
        return redirect(url_for("dashboard"))
    id = ObjectId(_id)
    data = db.produk.find_one({"_id": id})
    return render_template("admin/editproduk.html", data=data)


@app.route("/deleteproduk/<_id>", methods=["POST"])
@login_required
def delete_produk(_id):
    deleted_product = db.produk.find_one_and_delete({"_id": ObjectId(_id)})
    if deleted_product:
        db.cartuser.delete_many({"product_id": str(deleted_product["_id"])})
    return redirect(url_for("dashboard"))


@app.route("/konfirmasipesananadmin", methods=["GET", "POST"])
@login_required
def konfirmasipesananadmin():
    try:
        per_page = 5  # Jumlah entri per halaman
        page = int(request.args.get("page", 1))
            # Menghitung total jumlah pesanan
        order_count = db.orders.count_documents({"status": "sedang dikonfirmasi"})
        # Mengambil pesanan dengan paginasi
        orders = list(
            db.orders.find({"status": "sedang dikonfirmasi"})
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        # Memproses pesanan untuk menyertakan foto profil dan alamat
        for order in orders:
            order["_id"] = str(order["_id"])
            for item in order["cart_items"]:
                item["_id"] = str(item["_id"])
            # Mengambil detail user
            user_id = order.get("user_id")
            user = db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                order["profile_picture"] = url_for(
                    "static",
                    filename=user.get("profile_picture", "profile_pics/default.jpg"),
                )
                order["address"] = user.get("address", "Alamat tidak tersedia")
                order["notelp"] = user.get("notelp", "No Phone Number")
            else:
                order["profile_picture"] = url_for(
                    "static", filename="profile_pics/default.jpg"
                )
                order["address"] = "Alamat tidak tersedia"
                order["notelp"] = "No Phone Number"
        # Mengirim pesanan yang difilter ke template
        return render_template(
            "admin/konfirmasipesananadmin.html",
            orders=orders,
            order_count=order_count,
            page=page,
            per_page=per_page,
            ceil=ceil,
        )
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500



@app.route("/confirm_admin", methods=["POST"])
@login_required
def confirm_admin():
    data = request.json
    action = data.get("action")
    id_pesan = data.get("idPesan")
    if action == "accept":
        status = "Di Proses"
        pesan = f"Pesanan dengan ID {id_pesan} sedang diproses."
    elif action == "reject":
        status = "Di Tolak"
        pesan = f"Pesanan dengan ID {id_pesan} telah ditolak."
    else:
        return jsonify({"message": "Aksi tidak dikenal"}), 400
    # Memperbarui status pesanan di database
    result = db.orders.update_one(
        {"_id": ObjectId(id_pesan)}, {"$set": {"status": status}}
    )
    if result.modified_count == 0:
        return jsonify({"message": "Gagal memperbarui status pesanan"}), 500
    # Mencatat pemberitahuan untuk admin
    print(f"Pengguna diberitahu: {pesan}")
    return jsonify({"message": pesan})


@app.route("/statuspesanadmin", methods=["GET"])
@login_required
def statuspesananadmin():
    try:
        orders_in_process = list(db.orders.find({"status": "Di Proses"}))
        orders_shipped = list(db.orders.find({"status": "Di Kirim"}))
        orders_completed = list(db.orders.find({"status": "Pesanan Selesai"}))
        for order in orders_in_process + orders_shipped + orders_completed:
            order["_id"] = str(order["_id"])
        return render_template(
            "admin/statuspesanadmin.html",
            orders_in_process=orders_in_process,
            orders_shipped=orders_shipped,
            orders_completed=orders_completed,
        )
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500


@app.route("/dikirim_admin", methods=["POST"])
@login_required
def dikrim_admin():
    data = request.json
    action = data.get("action")
    id_pesan = data.get("idPesan")
    if action == "send":
        status = "Di Kirim"
        pesan = f"Pesanan dengan ID {id_pesan} sedang dikirim."
    else:
        return jsonify({"message": "Aksi tidak dikenal"}), 400
    # Memperbarui status pesanan di database
    result = db.orders.update_one(
        {"_id": ObjectId(id_pesan)}, {"$set": {"status": status}}
    )
    if result.modified_count == 0:
        return jsonify({"message": "Gagal memperbarui status pesanan"}), 500
    # Mencatat pemberitahuan untuk admin
    print(f"Pengguna diberitahu: {pesan}")
    return jsonify({"message": pesan})


@app.route("/review/admin", methods=["GET", "POST"])
@login_required
def reviewadmin():
    try:
        if request.method == "POST":
            review_id = request.form["review_id"]
            db.reviews.delete_one({"_id": ObjectId(review_id)})
        reviews = list(db.reviews.find())
        for review in reviews:
            review["_id"] = str(review["_id"])
        return render_template("admin/reviewadmin.html", reviews=reviews)
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500


@app.route("/kelolauser/admin", methods=["GET", "POST"])
@login_required
def kelolauser():
    try:
        per_page = 5  # Jumlah entri per halaman
        page = int(request.args.get("page", 1))
        # Menghitung total jumlah admin dan user
        admin_count = db.admins.count_documents({})
        user_count = db.users.count_documents({})
        # Mengambil admin dan user dengan paginasi
        admins = list(
            db.admins.find({}).skip((page - 1) * per_page).limit(per_page)
        )
        users = list(
            db.users.find({}).skip((page - 1) * per_page).limit(per_page)
        )
        for admin in admins:
            admin["_id"] = str(admin["_id"])
        for user in users:
            user["_id"] = str(user["_id"])
        return render_template(
            "admin/kelolauser.html",
            admins=admins,
            users=users,
            admin_count=admin_count,
            user_count=user_count,
            page=page,
            per_page=per_page,
            ceil=ceil,
        )
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500


@app.route("/kelolauser/delete_admin/<admin_id>", methods=["DELETE"])
@login_required
def delete_admin(admin_id):
    db.admins.delete_one({"_id": ObjectId(admin_id)})
    return jsonify({"result": "success"})


@app.route("/kelolauser/delete_user/<user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    db.users.delete_one({"_id": ObjectId(user_id)})
    return jsonify({"result": "success"})


@app.route("/logoutadmin")
def logoutadmin():
    response = make_response(redirect(url_for("loginAdmin")))
    response.delete_cookie(TOKEN_KEY)
    return response

# -------------------------------------------  AKHIR ROUTES ADMIN ------------------------------------------------------#

# --------------------------------------Bagian User ROUTES--------------------------------------------------#
@app.route("/register/user", methods=["POST"])
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
        "profile_picture": "profile_pics/Default_Profile_Pictures.png",
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
        # Fetch reviews and sort by creation date descending
        reviews = list(db.reviews.find().sort("created_at", -1))
        # Fetch user data for each review to get the profile picture
        for review in reviews:
            review_user = db.users.find_one({"_id": ObjectId(review["user_id"])})
            review["profile_picture"] = review_user.get(
                "profile_picture", "default.jpg"
            )
            if "rating" not in review:
                review["rating"] = 0  # Default rating value if missing
        return render_template(
            "user/produkuser.html",
            user_id=user_id,
            user=user,
            produk=produk,
            username=username,
            pesan=pesan,
            reviews=reviews,  # Pass reviews to template
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
        item["product_photo"] = f"imgproduct/{product['foto']}"
        total_harga += item["product_price"] * item["quantity"]
    pesan = db.cartuser.count_documents({"user_id": str(user["_id"])})
    username = user.get("username")
    return render_template(
        "user/shoppingcart.html",
        username=username,
        cart_items=cart_items,
        pesan=pesan,
        user=user,
        total_harga=total_harga,
    )


@app.route("/addshoppingcart", methods=["POST"])
@token_required
def add_shopping_cart(user):
    try:
        data = request.get_json()
        product_id = data.get("product_id")
        product = db.produk.find_one({"_id": ObjectId(product_id)})
        if not product or product["stock"] <= 0:
            return jsonify({"result": "error", "message": "Product not available."})
        # Check if the product is already in the cart
        cart_item = db.cartuser.find_one(
            {"user_id": str(user["_id"]), "product_id": product_id}
        )
        if cart_item:
            # Check if adding one more exceeds the stock
            if cart_item["quantity"] + 1 > product["stock"]:
                return jsonify(
                    {"result": "error", "message": "Melebihi stok yang tersedia."}
                )
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
        # Fetch current cart item and product
        cart_item = db.cartuser.find_one(
            {"user_id": str(user_id), "product_id": str(product_id)}
        )
        product = db.produk.find_one({"_id": ObjectId(product_id)})
        if not cart_item or not product:
            return jsonify(
                {"result": "error", "message": "Product or cart item not found."}
            )
        current_quantity = cart_item["quantity"]
        stock = product["stock"]
        # Check stock before updating
        if action == "increment":
            if current_quantity + 1 > stock:
                return jsonify(
                    {"result": "error", "message": "Exceeds available stock."}
                )
            db.cartuser.update_one(
                {"user_id": str(user_id), "product_id": str(product_id)},
                {"$inc": {"quantity": 1}},
            )
        elif action == "decrement":
            new_quantity = current_quantity - 1
            if new_quantity <= 0:
                db.cartuser.delete_one({"_id": cart_item["_id"]})
            else:
                db.cartuser.update_one(
                    {"user_id": str(user_id), "product_id": str(product_id)},
                    {"$set": {"quantity": new_quantity}},
                )
        return jsonify({"result": "success"}), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500


@app.route("/deletecartitem", methods=["POST"])
def delete_cart_item():
    try:
        token = request.cookies.get("token")
        if not token:
            return jsonify(
                {"result": "error", "message": "Token missing. Please login again."}
            )
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        product_id = request.json.get("product_id")
        # Delete the cart item
        db.cartuser.delete_one({"user_id": str(user_id), "product_id": str(product_id)})
        return jsonify({"result": "success"}), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    token = request.cookies.get("token")
    if not token:
        return redirect(url_for("loginuser"))
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        user_doc = db.users.find_one({"_id": ObjectId(user_id)})
        username = user_doc.get("username")
        pesan = db.cartuser.count_documents({"user_id": str(user_doc["_id"])})
        # Handle POST request for checkout
        if request.method == "POST":
            data = request.json
            cart_items = data.get("cart_items", [])
            total_harga = data.get("total_harga", 0.0)
            pengiriman = data.get("pengiriman")
            # print(pengiriman)
            # Set delivery method cookie
            response = make_response(jsonify({"result": "success"}))
            response.set_cookie("pengiriman", pengiriman)
            return response
        # Handle GET request for checkout page
        cart_items = list(db.cartuser.find({"user_id": str(user_id)}))
        total_harga = sum(
            item["product_price"] * item["quantity"] for item in cart_items
        )
        pengiriman = request.cookies.get("pengiriman")
        # print(pengiriman)
        return render_template(
            "user/checkout.html",
            cart_items=cart_items,
            total_harga=total_harga,
            username=username,
            pesan=pesan,
            pengiriman=pengiriman,
            user=user_doc,
        )
    except jwt.ExpiredSignatureError:
        return redirect(
            url_for("loginuser", error_msg="Token expired. Please login again.")
        )
    except jwt.InvalidTokenError:
        return redirect(
            url_for("loginuser", error_msg="Invalid token. Please login again.")
        )
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500


@app.route("/pesan", methods=["POST"])
def pesan():
    token = request.cookies.get("token")
    if not token:
        return redirect(url_for("loginuser"))

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"result": "error", "message": "User not found"}), 404

        username = user.get("username")

        if request.method == "POST":
            data = request.form.to_dict()
            payment_method = data.get("payment_method")

            # Handle file upload
            file = request.files.get("bankProof") or request.files.get("qrisProof")
            filepath = None

            if file:
                if file.filename.split(".")[-1].lower() not in ["jpg", "jpeg", "png"]:
                    return (
                        jsonify(
                            {
                                "error": "Invalid file format. Only accepts JPG, JPEG, and PNG."
                            }
                        ),
                        400,
                    )
                filename = secure_filename(file.filename)
                extension = filename.split(".")[-1]
                buktibayar = f"{username}.{extension}"
                filepath = f"static/buktipembayaran/{buktibayar}"
                file.save(filepath)

            # Get cart items and calculate total_harga
            cart_items = list(db.cartuser.find({"user_id": str(user_id)}))
            total_harga = sum(
                item["product_price"] * item["quantity"] for item in cart_items
            )
            pengiriman = request.cookies.get("pengiriman")

            # Prepare order data
            order_data = {
                "user_id": user_id,
                "nama": data.get("namalengkap"),
                "username": username,
                "notelp": data.get("nohp"),
                "address": data.get("address"),
                "payment_method": payment_method,
                "total_harga": total_harga,
                "pengiriman": pengiriman,
                "cart_items": cart_items,
                "payment_proof": filepath,
                "status": "sedang dikonfirmasi",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "review": False,
            }

            # Simpan pesanan ke database
            db.orders.insert_one(order_data)

            # Update stok produk
            for item in cart_items:
                product_id = ObjectId(item["product_id"])
                quantity = item["quantity"]
                db.produk.update_one(
                    {"_id": product_id}, {"$inc": {"stock": -quantity}}
                )

            # Kosongkan keranjang belanja pengguna
            result = db.cartuser.delete_many({"user_id": str(user_id)})
            if result.deleted_count == 0:
                raise Exception("Cart items were not deleted")

            return jsonify({"result": "success"})

        else:
            return (
                jsonify({"result": "error", "message": "Invalid request method"}),
                405,
            )

    except jwt.ExpiredSignatureError:
        return redirect(
            url_for("loginuser", error_msg="Token expired. Please login again.")
        )

    except jwt.InvalidTokenError:
        return redirect(
            url_for("loginuser", error_msg="Invalid token. Please login again.")
        )

    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500


@app.route("/statuspesananuser", methods=["GET"])
def statuspesananuser():
    token = request.cookies.get("token")
    if not token:
        return redirect(url_for("loginuser"))
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        user_doc = db.users.find_one({"_id": ObjectId(user_id)})
        username = user_doc.get("username")
        pesan = db.cartuser.count_documents({"user_id": str(user_id)})
        # Fetch and sort orders by creation date in descending order
        orders = list(db.orders.find({"user_id": str(user_id)}).sort("created_at", -1))
        for order in orders:
            order["_id"] = str(order["_id"])
        return render_template(
            "user/statuspesananuser.html",
            username=username,
            user=user_doc,
            orders=orders,
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
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500


@app.route("/order/<order_id>")
def order_detail(order_id):
    token = request.cookies.get("token")
    if not token:
        return redirect(url_for("loginuser"))
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        user_doc = db.users.find_one({"_id": ObjectId(user_id)})
        username = user_doc.get("username")
        orders = list(db.orders.find({}))
        order = next((order for order in orders if str(order["_id"]) == order_id), None)
        if not order:
            return "Order not found", 404
        return render_template(
            "user/order_detail.html", user=user_doc, username=username, order=order
        )
    except jwt.ExpiredSignatureError:
        return redirect(
            url_for("loginuser", error_msg="Token expired. Please login again.")
        )


@app.route("/update_order_status/<order_id>", methods=["POST"])
def update_order_status(order_id):
    token = request.cookies.get("token")
    if not token:
        return redirect(url_for("loginuser"))
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        # Update order status
        result = db.orders.update_one(
            {"_id": ObjectId(order_id), "user_id": str(user_id)},
            {"$set": {"status": "Pesanan Selesai"}},
        )
        if result.matched_count == 0:
            return (
                jsonify(
                    {
                        "result": "error",
                        "message": "Order not found or user not authorized",
                    }
                ),
                404,
            )
        return jsonify({"result": "success"})
    except jwt.ExpiredSignatureError:
        return redirect(
            url_for("loginuser", error_msg="Token expired. Please login again.")
        )
    except jwt.InvalidTokenError:
        return redirect(
            url_for("loginuser", error_msg="Invalid token. Please login again.")
        )
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500


@app.route("/write_review", methods=["GET"])
def write_review():
    token = request.cookies.get("token")
    if not token:
        return redirect(url_for("loginuser"))
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        user = db.users.find_one({"_id": ObjectId(user_id)})
        product_id = request.args.get("product_id")
        if not product_id:
            return redirect(url_for("product"))
        return render_template(
            "user/write_review.html", user=user, product_id=product_id
        )
    except jwt.ExpiredSignatureError:
        return redirect(
            url_for("loginuser", error_msg="Token expired. Please login again.")
        )
    except jwt.InvalidTokenError:
        return redirect(
            url_for("loginuser", error_msg="Invalid token. Please login again.")
        )


# Submit review endpoint
@app.route("/submit_review", methods=["POST"])
def submit_review():
    token = request.cookies.get("token")
    if not token:
        return redirect(url_for("loginuser"))

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        user_doc = db.users.find_one({"_id": ObjectId(user_id)})

        review_data = request.form
        product_id = review_data.get("product_id")
        review_text = review_data.get("review")
        rating = int(review_data.get("rating", 0))

        # Insert review into database
        db.reviews.insert_one(
            {
                "user_id": str(user_id),
                "product_id": product_id,
                "review": review_text,
                "rating": rating,
                "username": user_doc.get("username"),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )

        # Update order status to indicate review submitted
        db.orders.update_one(
            {"user_id": user_id, "cart_items.product_id": product_id},
            {"$set": {"cart_items.$.review": True}},
        )

        return redirect(url_for("product"))

    except jwt.ExpiredSignatureError:
        return redirect(
            url_for("loginuser", error_msg="Token expired. Please login again.")
        )

    except jwt.InvalidTokenError:
        return redirect(
            url_for("loginuser", error_msg="Invalid token. Please login again.")
        )

    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500


@app.route("/profile", methods=["GET", "POST"])
@token_required
def profile(user):
    if request.method == "POST":
        # Get the form data
        username = request.form.get("username")
        email = user.get("email")  # Retrieve existing email from user object
        notelp = request.form.get("notelp")
        
        # Ensure the phone number starts with +62
        if not notelp.startswith("+62"):
            notelp = "+62" + notelp
        
        address = request.form.get("address")
        
        # Handle file upload
        profile_picture = request.files.get("profile_picture")
        profile_picture_filename = user.get("profile_picture", "default.jpg")  # Default to existing picture or default.jpg
        
        if profile_picture:
            # Generate a secure filename based on the user's input
            profile_filename = secure_filename(profile_picture.filename)
            extension = profile_filename.split(".")[-1]
            profile_picture_filename = f"profile_pics/{username}.{extension}"
            
            # Save the new profile picture
            profile_picture_path = os.path.join(app.static_folder, profile_picture_filename)
            profile_picture.save(profile_picture_path)
        
        # Update the user document in the database
        db.users.update_one(
            {"_id": ObjectId(user["_id"])},
            {
                "$set": {
                    "username": username,
                    "notelp": notelp,
                    "address": address,
                    "profile_picture": profile_picture_filename,
                }
            },
        )
        
        # Update the user object to reflect the changes
        user.update(
            {
                "username": username,
                "notelp": notelp,
                "address": address,
                "profile_picture": profile_picture_filename,
            }
        )
    
    pesan = db.cartuser.count_documents({"user_id": str(user["_id"])})
    return render_template(
        "user/profile.html", username=user.get("username"), pesan=pesan, user=user
    )



@app.route("/logoutuser", methods=["GET", "POST"])
def logoutuser():
    response = make_response(redirect(url_for("loginuser")))
    # Clear the 'pengiriman' cookie
    response.set_cookie("pengiriman", "", expires=0, samesite="Strict", domain=None)
    # Clear the 'token' cookie
    response.set_cookie(
        "token", "", expires=0, httponly=True, samesite="Strict", domain=None
    )
    return response


# --------------------------------------END USER ROUTES----------------------------------------------------#
if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
