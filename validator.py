from flask import session,redirect ,url_for
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import datetime
from jwt import ExpiredSignatureError,InvalidTokenError
from db_connect import get_db_connection

SECRET_KEY="apache12.comcf"

def get_data():
    return jwt.decode(session["token"],SECRET_KEY,algorithms=["HS256"])

def validatuser():
    try:
        if "token" not in session:
            return True

        decode_payload = jwt.decode(session["token"],SECRET_KEY,algorithms=["HS256"])

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE userid=%s AND email=%s AND password=%s AND user_disable=0",(decode_payload["userid"],decode_payload["email"],decode_payload["password"]))
        result = cursor.fetchone()
        if result:
            return False
        else:
            return True

    except ExpiredSignatureError:
        print("Token expired")
        session.pop("token", None)
        return True

    except InvalidTokenError:
        print("Invalid token")
        session.pop("token", None)
        return True

def validate_for_admin():
    try:
        if "token" not in session:
            return True

        decode_payload = jwt.decode(session["token"],SECRET_KEY,algorithms=["HS256"])

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE userid=%s AND email=%s AND password=%s AND level='Admin' AND user_disable=0",(decode_payload["userid"],decode_payload["email"],decode_payload["password"]))
        result = cursor.fetchone()
        if result:
            return False
        else:
            return True

    except ExpiredSignatureError:
        print("Token expired")
        session.pop("token", None)
        return True

    except InvalidTokenError:
        print("Invalid token")
        session.pop("token", None)
        return True