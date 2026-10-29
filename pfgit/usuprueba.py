# guia de variables:
# gh  = generar hash (cifra la contraseña)
# u   = lista de usuarios de prueba: (nom, ape, usu, clave, cat, rol)
import db
from werkzeug.security import generate_password_hash as gh

u = [
    ("Ana", "Admin", "admin", "admin123", "coord", "admin"),
    ("Carlos", "Prueba", "carlos", "carlos123", "prof", "pers"),
    ("Laura", "Prueba", "laura", "laura123", "prof", "pers"),
    ("Pedro", "Prueba", "pedro", "pedro123", "prof", "pers"),
]

cnx = db.con()
cur = cnx.cursor()
for nom, ape, usu, clave, cat, rol in u:
    cur.execute(
        "INSERT INTO per (nom, ape, usu, clave, cat, rol) "
        "VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (usu) DO NOTHING",
        (nom, ape, usu, gh(clave), cat, rol),
    )
cnx.commit()
cnx.close()
print("Usuarios creados")