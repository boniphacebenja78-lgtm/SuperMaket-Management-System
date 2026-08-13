import mariadb
from config import DB_CONFIG


def get_db_connection():
    try:
        connection = mariadb.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )

        print("MariaDB connection successful!")

        return connection

    except mariadb.Error as e:
        print(f"MariaDB connection error: {e}")
        return None