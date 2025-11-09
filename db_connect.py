import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host='localhost', #127.0.0.1
        user='root',
        password = '',
        database='inventory_management_system',
    )