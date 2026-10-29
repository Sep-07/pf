# DICCIONARIO
# xy       = texto pegado con las coordenadas "lat, lon"
# lat, lon = coordenadas del punto de referencia
# r        = radio permitido en metros
import db

xy = input("Pega las coordenadas (lat, lon): ")
lat, lon = [float(v) for v in xy.replace(" ", "").split(",")]
r = float(input("Radio en metros (Enter = 100): ") or 100)

cnx = db.con()
cur = cnx.cursor()
cur.execute("DELETE FROM conf")
cur.execute("INSERT INTO conf (lat, lon, radio) VALUES (%s,%s,%s)", (lat, lon, r))
cnx.commit()
cnx.close()
print("Guardado:", lat, lon, r)