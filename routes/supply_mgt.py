from flask import Blueprint, render_template, request, redirect, url_for, flash
from validator import validate_for_admin, get_data, validatuser
from db_connect import get_db_connection
from datetime import date

p_supply_mgt = Blueprint("supply_mgt", __name__, url_prefix="/suppliers")


@p_supply_mgt.route("/list")
def list():
    if validatuser():
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM supplies WHERE disabled=0")
    supplys = cursor.fetchall()

    conn.close()

    return render_template("supply_list.html", supplys=supplys)


@p_supply_mgt.route("/remove/<int:id>")
def delete(id):
    if validate_for_admin():
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("UPDATE supplies SET disabled= 1 WHERE supplyid=%s", (id,))

    conn.commit()
    conn.close()

    return redirect(request.referrer or "/")
