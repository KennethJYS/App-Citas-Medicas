import pyodbc

def get_db_connection():
    # Ajusta SERVER al nombre de tu instancia de SQL Server (ej: localhost o el nombre de tu PC)
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;" 
        "DATABASE=SanaYaDB;"
        "Trusted_Connection=yes;" # Usa autenticación de Windows
    )
    return pyodbc.connect(conn_str)