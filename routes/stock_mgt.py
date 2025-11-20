from flask import Blueprint, render_template, request, redirect, url_for, flash
from validator import validate_for_admin, get_data, validatuser
from db_connect import get_db_connection
from datetime import date

p_stock_mgt = Blueprint("stock_mgt", __name__, url_prefix="/stock-info")


@p_stock_mgt.route("/new-stock", methods=["GET", "POST"])
def create_new_stock():
    if validatuser():
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM categories")
    categorys = cursor.fetchall()

    cursor.execute("SELECT * FROM supplies")
    supplys = cursor.fetchall()

    if request.method == "POST":
        barcode = request.form["barcode"].strip()
        productname = request.form["productName"].strip()
        category = request.form["category"].strip()
        description = request.form["description"].strip()
        quantity = request.form["quantity"].strip()
        price = request.form["price"].strip()
        supplier = request.form["supplier"].strip()
        created_at = date.today()
        updated_at = date.today()
        disabled = 0


        userid = get_data()["userid"]

        cursor.execute(
            "INSERT INTO products (productcode, productname, category, price, quantity, description, created_at, updated_at, userid, disabled) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                barcode,
                productname,
                category,
                price,
                0,
                description,
                created_at,
                updated_at,
                userid,
                disabled,
            ),
        )

        productid = cursor.lastrowid
        print(supplier,userid,productid)

        cursor.execute(
            "INSERT INTO stocks(userid,productid,productcode,quantity,price,supplyid,recorddate) VALUES(%s,%s,%s,%s,%s,%s,%s)",
            (userid, productid, barcode, quantity, price, supplier, created_at),
        )

        conn.commit()
        conn.close()

        return redirect(url_for('inventorys'))

    return render_template(
        "create_new_stock.html", categorys=categorys, supplys=supplys
    )
