# DICCIONARIO
# usu      = usuario al que se le carga el horario
# ini, fin = inicio y fin de la clase de hoy
# dia      = día de la semana de hoy (1 lunes ... 7 domingo)
# cid, pid = id del curso y de la persona
import datetime as dt
from zoneinfo import ZoneInfo
import db

usu = input("Usuario (laura, pedro...): ")
ini = input("Inicio de clase HH:MM: ")
fin = input("Fin de clase HH:MM: ")
dia = dt.datetime.now(ZoneInfo("America/Asuncion")).isoweekday()

cnx = db.con()
cur = cnx.cursor()
cur.execute("INSERT INTO curso (nom) VALUES ('3 BTI') ON CONFLICT (nom) DO NOTHING")
cur.execute("SELECT id FROM curso WHERE nom='3 BTI'")
cid = cur.fetchone()[0]
cur.execute("SELECT id FROM per WHERE usu=%s", (usu,))
pid = cur.fetchone()[0]
cur.execute("DELETE FROM hor WHERE per_id=%s", (pid,))
cur.execute("INSERT INTO hor (per_id, curso_id, dia, ini, fin) VALUES (%s,%s,%s,%s,%s)",
            (pid, cid, dia, ini, fin))
cnx.commit()
cnx.close()
print("Horario cargado para hoy, día", dia)