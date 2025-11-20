from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from validator import validate_for_admin, get_data, validatuser
from db_connect import get_db_connection
from datetime import date

p_sale_mgt = Blueprint("sale_mgt", __name__, url_prefix="/product")


#
# sale detail item (show item after sale)
#
@p_sale_mgt.route("/sale-detail/<int:id>")
def show_sale_detail(id):
    if validatuser():
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT saledetails.detailid,saledetails.recorddate, products.productcode,products.productname,SUM(sales.quantity) AS quantity,sales.price,sales.discount FROM sales JOIN products ON products.productid = sales.productid JOIN saledetails ON sales.detailid = saledetails.detailid GROUP BY saledetails.detailid,saledetails.recorddate, products.productcode,products.productname,sales.price, sales.discount HAVING saledetails.detailid=%s",
        (id,),
    )
    sale_items = cursor.fetchall()

    total = sum(
        item["quantity"] * float(item["price"])
        - (item["quantity"] * float(item["price"]) * float(item["discount"]))
        for item in sale_items
    )
    # sale_items = []
    if sale_items:
        sale_info = {
            "id": sale_items[0]["detailid"],
            "date": sale_items[0]["recorddate"],
            "total": total,
            "customer_name": sale_items[0]["productname"],
            "status": sale_items[0]["productcode"],
        }

        return render_template(
            "sale_detail.html", sale_info=sale_info, sale_items=sale_items
        )
    else:
        return "Invalid..."

#
# sale item
#
@p_sale_mgt.route("sale", methods=["GET", "POST"])
def sale():
    if validatuser():
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM products WHERE products.disabled=0 AND products.quantity > 0"
    )
    products = cursor.fetchall()

    if request.method == "POST":
        items = request.form.getlist("product_id[]") or []
        quantities = request.form.getlist("quantity[]") or []

        if items is None or len(items) == 0:
            flash("Enter items...", "info")
            return redirect(request.referrer or "/")

        total = 0
        sale_items = []

        for i, product_id in enumerate(items):
            quantity = int(quantities[i])

            product = next(
                (
                    p
                    for p in products
                    if str(p["productid"]) == product_id
                    and int(p["quantity"]) >= quantity
                ),
                None,
            )

            if product:
                subtotal = float(product["price"]) * quantity
                total += subtotal
                sale_items.append(
                    (product_id, quantity, float(product["price"]), subtotal)
                )

        userid = session["userid"]

        if len(sale_items) != 0:
            cursor.execute(
                "INSERT INTO saledetails(userid,recorddate) VALUES(%s,%s)",
                (userid, date.today()),
            )
            detailid = cursor.lastrowid

            for product_id, quantity, price, subtotal in sale_items:
                cursor.execute(
                    "INSERT INTO sales(detailid,productid,quantity,price,discount) VALUES(%s,%s,%s,%s,%s)",
                    (detailid, product_id, quantity, price, 0),
                )

            conn.commit()
            conn.close()
            return redirect(url_for("sale_mgt.show_sale_detail", id=detailid))
        else:
            flash("product not enught", "info")
            return redirect(request.referrer or "/")

    return render_template("sale.html", products=products)

#
# sale detail
#
@p_sale_mgt.route("/sale-detil-list")
def sale_detail_list():
    if validatuser():
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM saledetails")
    sale_list_view = cursor.fetchall()

    conn.close()

    # Pagination
    page = request.args.get("page", default=1, type=int)
    per_page = 5
    total_orders = len(sale_list_view)
    total_pages = (total_orders + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    sale_list = sale_list_view[start:end]

    return render_template(
        "sale_list.html",
        sale_list=sale_list,
        page=page,
        total_pages=total_pages,
        total_orders=total_orders,
    )
