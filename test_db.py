import mariadb
from config import DB_CONFIG

print("Testing MariaDB connection...")
print("--------------------------------")
print("Host:", DB_CONFIG["host"])
print("Port:", DB_CONFIG["port"])
print("User:", DB_CONFIG["user"])
print("Database:", DB_CONFIG["database"])
print("--------------------------------")

try:
    connection = mariadb.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )

    print("SUCCESS! MariaDB connection is working.")

    cursor = connection.cursor()

    cursor.execute("SELECT DATABASE()")
    result = cursor.fetchone()

    print("Connected database:", result[0])

    cursor.close()
    connection.close()

except mariadb.Error as e:
    print("MARIADB ERROR:")
    print(e)