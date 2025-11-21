import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="host.docker.internal",
        user='root',
        password = '',
        database='inventory_management_system',
    )