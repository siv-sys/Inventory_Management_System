import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user='root',
        password = '',
        database='inventory_management_system',
    )
