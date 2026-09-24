from app.models.database import get_connection

try:
    connection = get_connection()

    if connection.is_connected():
        print("Database connection successful!")

except Exception as e:
    print("Database connection failed!")
    print("Error:", e)

finally:
    try:
        connection.close()
    except:
        pass