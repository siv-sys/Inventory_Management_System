from db_connect import get_db_connection
from validator import validatuser, validate_for_admin
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import date
import jwt
import datetime

from routes.user_mgt import p_user_mgt
from routes.sale_mgt import p_sale_mgt
from routes.stock_mgt import p_stock_mgt
from routes.supply_mgt import p_supply_mgt

app = Flask(__name__)
app.secret_key = "siv_2025"

SECRET_KEY = "apache12.comcf"

#
# register
#
app.register_blueprint(p_user_mgt)
app.register_blueprint(p_sale_mgt)
app.register_blueprint(p_stock_mgt)
app.register_blueprint(p_supply_mgt)


#
# code for route login
#
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE email = %s AND password=%s AND user_disable=0",
            (email, password),
        )
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            session["userid"] = result["userid"]
            session["email"] = result["email"]
            session["nickname"] = result["nickname"]
            payload = {
                "userid": result["userid"],
                "email": result["email"],
                "password": result["password"],
                "level": result["level"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            }
            session["token"] = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            flash("login successfull...")

            return redirect(url_for("dashboard"))
        else:
            flash("Invalid login...", "danger")

    return render_template("login.html")


#
# code for logout
#
@app.route("/logout")
def logout():
    #
    # clear session for login
    #
    session.clear()
    return redirect(url_for("login"))


#
# dashboard
#
@app.route("/dashboard")
def dashboard():
    if validatuser():
        flash("Please log in first!", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS product_count FROM products WHERE disabled=0")
    total_product = cursor.fetchone()["product_count"]

    cursor.execute(
        "SELECT *  FROM products INNER JOIN categories ON products.category = categories.cateid WHERE products.disabled=0"
    )
    products = cursor.fetchall()

    cursor.execute(
        "SELECT categories.title,CAST(SUM(products.quantity) AS SIGNED ) AS total,ROUND((SUM(products.quantity)/(SELECT SUM(P1.quantity) FROM products AS P1 WHERE P1.disabled=0))*100,2) AS percentage FROM products INNER JOIN categories ON products.category = categories.cateid WHERE products.disabled = 0 GROUP BY categories.title ORDER BY CAST(SUM(products.quantity) AS SIGNED ) DESC"
    )
    productByCategory = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM products JOIN categories ON products.category=categories.cateid WHERE products.disabled=0 ORDER BY CAST(products.quantity as integer) DESC LIMIT 6"
    )
    recent_products = cursor.fetchall()

    cursor.execute(
        "SELECT stocks.stockid,products.productname,products.productcode,users.nickname,SUM(stocks.quantity) AS quantity,stocks.price,stocks.recorddate FROM stocks JOIN users ON stocks.userid = users.userid JOIN products ON products.productid = stocks.productid GROUP BY products.productid, products.productname, products.productcode,stocks.recorddate ORDER BY stocks.recorddate DESC LIMIT 10"
    )
    recent_orders = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) AS COUNTER FROM products WHERE products.disabled=0 AND CAST(products.quantity as integer) > 10"
    )
    instock_product = cursor.fetchone()["COUNTER"]

    cursor.execute(
        "SELECT COUNT(*) AS COUNTER FROM products WHERE products.disabled=0 AND CAST(products.quantity as integer) > 0 AND CAST(products.quantity as integer) < 10"
    )
    low_stock = cursor.fetchone()["COUNTER"]

    cursor.execute(
        "SELECT COUNT(*) AS COUNTER FROM products WHERE products.disabled=0 AND CAST(products.quantity as integer) = 0"
    )
    out_of_stock = cursor.fetchone()["COUNTER"]

    total_prices = sum(int(p["quantity"]) * float(p["price"]) for p in products)

    cursor.execute(
        "SELECT SUM(CAST(quantity AS integer) * CAST(price AS float)) AS total_price FROM stocks WHERE YEAR(recorddate) = YEAR(NOW())"
    )
    total_orders = cursor.fetchone()["total_price"] or 0

    cursor.execute(
        "SELECT SUM(CAST(quantity AS integer) * CAST(price AS float)) AS total_price FROM sales JOIN saledetails ON sales.detailid = saledetails.detailid WHERE YEAR(recorddate) = YEAR(NOW())"
    )
    total_sale = cursor.fetchone()["total_price"] or 0

    cursor.execute(
        "SELECT COUNT(*) AS total_customer FROM saledetails WHERE YEAR(recorddate) = YEAR(NOW())"
    )
    total_customer = cursor.fetchone()["total_customer"] or 0

    inventorys = {
        "total_product": total_product,
        "in_stock": instock_product,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "total_price": total_prices,
        "total_order": total_orders,
        "total_sale": total_sale,
        "total_customer": total_customer,
    }

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        users=users,
        total_product=total_product,
        products=products,
        productByCategory=productByCategory,
        recent_products=recent_products,
        recent_orders=recent_orders,
        inventorys=inventorys,
    )


#
# index
#
@app.route("/")
def index():
    return redirect(url_for("dashboard"))


#
# product
#
@app.route("/products")
def products():
    if validatuser():
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM categories")
    categorys = cursor.fetchall()

    return render_template("add_product.html", categorys=categorys)


#
# add product (insert data on database)
#
@app.route("/products/add", methods=["POST"])
def add_products():
    if validatuser():
        return redirect(url_for("login"))

    if request.method == "POST":
        productcode = request.form["productcode"].strip()
        productname = request.form["productname"].strip()
        quantity = 0
        price = 0
        category = request.form["category"].strip()
        description = request.form["description"].strip()
        userid = session["userid"]
        disabled = 0

        created_at = date.today()
        updated_at = date.today()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "INSERT INTO products (productcode, productname, category, price, quantity, description, created_at, updated_at, userid, disabled) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                productcode,
                productname,
                category,
                price,
                quantity,
                description,
                created_at,
                updated_at,
                userid,
                disabled,
            ),
        )

        conn.commit()

        flash("Insert data success...", "seccess")

        cursor.close()
        conn.close()

    return redirect(url_for("products"))


#
# delete product (disabled record not deleted record)
#
@app.route("/products/delete/<int:id>")
def delete_product(id):
    if validatuser():
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    print(id)

    cursor.execute("UPDATE products SET disabled=1 WHERE productid=%s", (id,))

    conn.commit()
    cursor.close()
    conn.close()

    products()

    flash("Product Delete successfully!", "danger")
    return redirect(request.referrer or "/")


#
# update product (update item after change value)
#
@app.route("/products/update/<int:id>", methods=["POST"])
def update_product(id):
    if validatuser():
        return redirect(url_for("login"))

    if request.method == "POST":
        productcode = request.form["productcode"].strip()
        productname = request.form["productname"].strip()
        category = request.form["category"].strip()
        description = request.form["description"].strip()
        userid = session["userid"]

        updated_at = date.today()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "UPDATE products SET productcode=%s,productname=%s,category=%s,description=%s,updated_at=%s WHERE productid=%s",
            (
                productcode,
                productname,
                category,
                description,
                updated_at,
                id,
            ),
        )

        conn.commit()
        cursor.close()
        conn.close()

        products()

    flash("Product Update successfully!", "success")
    return redirect(url_for("inventorys"))


#
# edit product (show item before update)
#
@app.route("/products/edit/<int:id>", methods=["GET"])
def edit_product(id):
    if validatuser():
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products WHERE disabled=0 AND productid=%s", (id,))
    product = cursor.fetchone()

    cursor.execute("SELECT * FROM categories")
    categorys = cursor.fetchall()

    conn.close()

    return render_template("update_product.html", product=product, categorys=categorys)


#
# show stock for update
#
@app.route("/products/show-stock/<int:id>", methods=["GET"])
def show_stock_for_add_stock(id):
    if validate_for_admin():
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT products.*,title FROM products INNER JOIN categories ON products.category = categories.cateid WHERE disabled=0 AND productid=%s",
        (id,),
    )
    product = cursor.fetchone()

    cursor.execute("SELECT * FROM supplies WHERE disabled=0")
    suppliers = cursor.fetchall()

    return render_template("add_stock.html", product=product, suppliers=suppliers)


#
# add stock
#
@app.route("/product/stock/add/<int:id>", methods=["POST"])
def add_stock(id):
    if validatuser():
        return redirect(url_for("login"))

    if request.method == "POST":
        quantity = request.form["quantity"].strip()
        price_in = request.form["price"].strip()
        supplier_id = request.form["supplier_id"]
        userid = session["userid"]
        recordate = date.today()
        productcode = "-"

        errors = []

        if not supplier_id or supplier_id == "":
            errors.append("Please select a supplier.")
        if not quantity or not quantity.isdigit() or int(quantity) <= 0:
            errors.append("Quantity must be a positive number.")
        if not price_in:
            errors.append("Please enter a price.")
        else:
            try:
                price_in_val = float(price_in)
                if price_in_val <= 0:
                    errors.append("Price must be greater than 0.")
            except ValueError:
                errors.append("Price must be a valid number.")

        if errors:
            for e in errors:
                flash(e, "error")
        else:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "INSERT INTO stocks(userid,productid,productcode,quantity,price,supplyid,recorddate) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (userid, id, productcode, quantity, price_in, supplier_id, recordate),
            )
            conn.commit()
            conn.close()
            inventorys()

    return redirect(url_for("inventorys"))


#
# route inventory
#
@app.route("/inventorys")
def inventorys():
    if validatuser():
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM categories")
    categorys = cursor.fetchall()

    cursor.execute(
        "SELECT productid,productcode,productname, CAST(quantity as integer) AS quantity,CAST(price as float) AS price,title,products.description,categories.cateid FROM products INNER JOIN categories ON products.category = categories.cateid WHERE disabled=0"
    )
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("inventory.html", categorys=categorys, products=products)


#
# recent order
#
@app.route("/order")
def order_detail():
    if validatuser():
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT stocks.stockid,products.productname,products.productcode,supplies.nickname,SUM(stocks.quantity) AS quantity,stocks.price,stocks.recorddate FROM stocks JOIN users ON stocks.userid = users.userid JOIN products ON products.productid = stocks.productid JOIN supplies ON supplies.supplyid = stocks.supplyid GROUP BY products.productid, products.productname, products.productcode,supplies.nickname,stocks.recorddate ORDER BY stocks.stockid DESC"
    )
    all_orders = cursor.fetchall()

    conn.close()

    # Pagination
    page = request.args.get("page", default=1, type=int)
    per_page = 5
    total_orders = len(all_orders)
    total_pages = (total_orders + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    orders = all_orders[start:end]
    return render_template(
        "recent_orders.html",
        orders=orders,
        page=page,
        total_pages=total_pages,
        total_orders=total_orders,
    )


# @app.route('/sale-detail/<int:id>')
# def show_sale_detail(id):
#     if validatuser():
#         return redirect(url_for("login"))

#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     cursor.execute("SELECT saledetails.detailid,saledetails.recorddate, products.productcode,products.productname,SUM(sales.quantity) AS quantity,sales.price,sales.discount FROM sales JOIN products ON products.productid = sales.productid JOIN saledetails ON sales.detailid = saledetails.detailid GROUP BY saledetails.detailid,saledetails.recorddate, products.productcode,products.productname,sales.price, sales.discount HAVING saledetails.detailid=%s",(id,))
#     sale_items = cursor.fetchall()

#     total = sum(item["quantity"] * float(item["price"]) - (item["quantity"] * float(item["price"]) * float(item["discount"]))  for item in sale_items)
#     # sale_items = []
#     sale_info = {
#         "id": sale_items[0]["detailid"],
#         "date": sale_items[0]["recorddate"],
#         "total": total,
#         "customer_name": sale_items[0]["productname"],
#         "status": sale_items[0]["productcode"]
#     }
#     return render_template('sale_detail.html',sale_info=sale_info, sale_items=sale_items)

# #
# #
# #
# @app.route('/sale',methods=["GET","POST"])
# def sale():
#     if validatuser():
#         return redirect(url_for("login"))

#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     cursor.execute("SELECT * FROM products WHERE products.disabled=0 AND products.quantity > 0")
#     products = cursor.fetchall()

#     if request.method == "POST":
#         items = request.form.getlist("product_id[]")
#         quantities = request.form.getlist("quantity[]")

#         total = 0
#         sale_items = []

#         for i,product_id in enumerate(items):
#             quantity = int(quantities[i])

#             product = next((p for p in products if str(p["productid"]) == product_id), None)
#             if product:
#                 subtotal = float(product["price"]) * quantity
#                 total += subtotal
#                 sale_items.append((product_id, quantity, float(product["price"]), subtotal))

#         userid = session["userid"]

#         cursor.execute("INSERT INTO saledetails(userid,recorddate) VALUES(%s,%s)",(userid,date.today()))
#         detailid = cursor.lastrowid

#         for product_id, quantity, price, subtotal in sale_items:
#             cursor.execute("INSERT INTO sales(detailid,productid,quantity,price,discount) VALUES(%s,%s,%s,%s,%s)",(detailid, product_id, quantity, price, 0))

#         conn.commit()
#         conn.close()
#         return redirect(url_for('show_sale_detail',id=detailid))

#     return render_template('sale.html',products=products)

# @app.route("/sale-detil-list")
# def sale_detail_list():
#     if validatuser():
#         return redirect(url_for("login"))

#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     cursor.execute("SELECT * FROM saledetails")
#     sale_list_view = cursor.fetchall()

#     conn.close()

#     # Pagination
#     page = request.args.get("page", default=1, type=int)
#     per_page = 5
#     total_orders = len(sale_list_view)
#     total_pages = (total_orders + per_page - 1) // per_page

#     start = (page - 1) * per_page
#     end = start + per_page
#     sale_list = sale_list_view[start:end]

#     return render_template("sale_list.html",sale_list=sale_list,page=page,total_pages=total_pages,total_orders=total_orders)

if __name__ == "__main__":
    app.run(debug=True)
