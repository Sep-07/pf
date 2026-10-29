# guia de variables:
# con() = abre una conexión a la base de datos
# cnx   = conexión
# cur   = cursor (el que ejecuta las consultas)
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def con():
    return psycopg2.connect(
        dbname=os.getenv("BD_NOMBRE"),
        user=os.getenv("BD_USUARIO"),
        password=os.getenv("BD_CLAVE"),
        host=os.getenv("BD_HOST"),
        port=os.getenv("BD_PUERTO"),
    )

if __name__ == "__main__":
    cnx = con()
    cur = cnx.cursor()
    cur.execute("SELECT count(*) FROM per")
    print("Conexión OK, personas:", cur.fetchone()[0])
    cnx.close()