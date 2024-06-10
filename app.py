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
            # Remove spaces from the file name
            sanitized_nama = nama.replace(" ", "_")
            # Get the original file extension
            ekstensi_file = nama_foto.filename.split(".")[-1]
            nama_file = f"{sanitized_nama}.{ekstensi_file}"
            file_path = f"static/imgproduct/{nama_file}"
            nama_foto.save(file_path)
        else:
            nama_file = None

        print(nama_file)
        doc = {"nama": nama, "harga": harga, "stock": stock, "foto": nama_file}
        db.produk.insert_one(doc)
        return redirect(url_for("dashboard"))

    return render_template("admin/tambahproduk.html")


# @app.route("/editproduk/<_id>", methods=["GET", "POST"])
# @login_required
# def editproduk(_id):
#     if request.method == "POST":
#         id = request.form["_id"]
#         nama = request.form["nama"]
#         harga = float(request.form["harga"])
#         stock = int(request.form["stock"])
#         nama_foto = request.files["foto"]
#         doc = {"nama": nama, "harga": harga, "stock": stock}

#         if nama_foto:
#             # Mengambil ekstensi file asli
#             ekstensi_file = nama_foto.filename.split(".")[-1]
#             nama_file = f"{nama}.{ekstensi_file}"
#             file_path = f"static/imgproduct/{nama_file}"
#             nama_foto.save(file_path)
#             doc["foto"] = nama_file

#         db.produk.update_one({"_id": ObjectId(id)}, {"$set": doc})
#         return redirect(url_for("dashboard"))

#     id = ObjectId(_id)
#     data = db.produk.find_one({"_id": id})
#     return render_template("admin/editproduk.html", data=data)

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
            # Remove spaces from the file name
            sanitized_nama = nama.replace(" ", "_")
            # Get the original file extension
            ekstensi_file = nama_foto.filename.split(".")[-1]
            nama_file = f"{sanitized_nama}.{ekstensi_file}"
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
    deleted_product = db.produk.find_one_and_delete({"_id": ObjectId(_id)})
    if deleted_product:
        db.cartuser.delete_many({"product_id": str(deleted_product["_id"])})
        return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("dashboard"))


@app.route("/konfirmasipesananadmin", methods=["GET", "POST"])
@login_required
def konfirmasipesananadmin():
    try:
        # Ambil semua pesanan dengan status 'sedang dikonfirmasi' dari database
        orders = list(db.orders.find({"status": "sedang dikonfirmasi"}))
        for order in orders:
            order["_id"] = str(order["_id"])
            for item in order["cart_items"]:
                item["_id"] = str(item["_id"])
        print(orders)

        # Pass the filtered orders to the template
        return render_template("admin/konfirmasipesananadmin.html", orders=orders)
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

    # Update order status in the database
    result = db.orders.update_one(
        {"_id": ObjectId(id_pesan)}, {"$set": {"status": status}}
    )
    if result.modified_count == 0:
        return jsonify({"message": "Gagal memperbarui status pesanan"}), 500

    # Log the notification for admin
    print(f"Pengguna diberitahu: {pesan}")

    return jsonify({"message": pesan})


@app.route("/statuspesanadmin", methods=["GET"])
@login_required
def statuspesananadmin():
    try:
        # Ambil semua pesanan dengan status 'Proses' atau 'Dikirim' dari database
        orders = list(db.orders.find({"status": {"$in": ["Di Proses", "Di Kirim"]}}))
        for order in orders:
            order["_id"] = str(order["_id"])

        return render_template(
            "admin/statuspesanadmin.html",
            orders=orders,
        )
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500


@app.route("/dikirim_admin", methods=["POST"])
@login_required
def dikrim_admin():
    data = request.json
    action = data.get("action")
    id_pesan = data.get("idPesan")

    if action == "dikirim":
        status = "Di Kirim"
        pesan = f"Pesanan dengan ID {id_pesan} telah dikirim."
    else:
        return jsonify({"message": "Aksi tidak dikenal"}), 400

    # Update order status in the database
    result = db.orders.update_one(
        {"_id": ObjectId(id_pesan)}, {"$set": {"status": status}}
    )
    if result.modified_count == 0:
        return jsonify({"message": "Gagal memperbarui status pesanan"}), 500

    return jsonify({"message": pesan})


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
        return render_template(
            "user/produkuser.html",
            user_id=user_id,
            user=user,
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
        user=user,
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
        username = user.get("username")

        if request.method == "POST":
            data = request.form.to_dict()
            payment_method = data.get("payment_method")

            # Handle file upload
            file = request.files.get("bankProof") or request.files.get("qrisProof")
            if file:
                filename = secure_filename(file.filename)
                extension = filename.split(".")[-1]
                buktibayar = f"{username}.{extension}"
                filepath = f"static/buktipembayaran/{buktibayar}"
                file.save(filepath)
            else:
                filepath = None  # or handle error appropriately

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
                "username": user.get("username"),
                "notelp": data.get("nohp"),
                "address": data.get("address"),
                "address2": data.get("address2"),
                "payment_method": payment_method,
                "total_harga": total_harga,
                "pengiriman": pengiriman,
                "cart_items": cart_items,
                "payment_proof": filepath,
                "status": "sedang dikonfirmasi",
                "created_at": datetime.now(),
            }

            # Save order to database
            db.orders.insert_one(order_data)

            # Clear user's cart
            result = db.cartuser.delete_many({"user_id": str(user_id)})
            if result.deleted_count == 0:
                raise Exception("Cart items were not deleted")

            return jsonify({"result": "success"})
        else:
            return jsonify({"result": "error", "message": "Invalid request method"})
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

        orders = list(db.orders.find({"user_id": str(user_id)}))
        for order in orders:
            order["_id"] = str(order["_id"])
            product_id = order.get("product_id")

            if product_id:
                product = db.produk.find_one({"_id": ObjectId(product_id)})
                if product:
                    order["product_photo"] = product.get("foto")
                    order["product_name"] = product.get("nama")
                    order["product_price"] = product.get("harga")
                else:
                    order["product_photo"] = ""
            else:
                order["product_photo"] = ""
                

        return render_template(
            "user/statuspesananuser.html",
            username=username,
            user=user_doc,
            orders=orders,
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



@app.route("/review", methods=["GET", "POST"])
def review():
    return render_template("user/review.html")


@app.route("/profile", methods=["GET", "POST"])
@token_required
def profile(user):
    if request.method == "POST":
        # Get the form data
        username = request.form.get("username")
        email = user.get("email")  # Retrieve existing email from user object
        notelp = int(request.form.get("notelp"))
        address = request.form.get("address")

        # Handle file upload
        profile_picture = request.files.get("profile_picture")
        profile_picture_filename = user.get(
            "profile_picture", "default.jpg"
        )  # Default to existing picture or default.jpg

        if profile_picture:
            # Generate a secure filename based on the user's input
            profile_filename = secure_filename(profile_picture.filename)
            extension = profile_filename.split(".")[-1]
            profile_picture_filename = f"profile_pics/{username}.{extension}"

            # Save the new profile picture
            profile_picture.save(
                os.path.join(app.static_folder, profile_picture_filename)
            )

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
    response.set_cookie(TOKEN_KEY, "", expires=0)
    return response


# --------------------------------------END USER ROUTES----------------------------------------------------#


if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=True)
