import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host='localhost',          # or the hostname/IP of your MySQL server
        user='root',    # replace with your MySQL username
        password='Password@123',  # replace with your MySQL password
        database='expiry_app'   # replace with your database name
    )
    return conn
