# guia de variables:
# ses   = session (guarda quién inició sesión)
# usu   = usuario escrito en el formulario
# clave = contraseña escrita
# f     = fila encontrada en la base: (id, nom, clave cifrada, rol)
# ch    = compara la clave escrita con la cifrada
# err   = mensaje de error

# ZH  = zona horaria de Paraguay
# tard = True si llegó tarde, False si no, None si hoy no tiene clase
# n   = ahora
# lim = hora límite (inicio de la clase + tolerancia)
# tar = resultado de tard

# DICCIONARIO (marcaje)
# PMAX = precisión máxima aceptada del GPS, en metros
# dm   = distancia en metros entre dos coordenadas (fórmula de Haversine)
# prox = qué toca marcar ahora: 'ent' o 'sal'
# t    = tipo de marcación
# c    = fila de conf: (lat, lon, radio)
# d    = distancia calculada al colegio
# mot  = motivo del rechazo

# DICCIONARIO (admin)
# adm    = decorador: solo deja pasar a administradores
# vivo   = cierra la sesión de quien fue desactivado
# ps     = lista de personas
# f      = datos del formulario
# nom, ape, usu, clave, cat, rol = campos de la persona nueva
# pid    = id de la persona

import os
from flask import Flask, render_template, request, redirect, url_for
from flask import session as ses
from werkzeug.security import check_password_hash as ch, generate_password_hash as gh
from functools import wraps
from dotenv import load_dotenv
import db
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import math
from flask import jsonify

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

@app.route("/login", methods=["GET", "POST"])
def login():
    err = None
    if request.method == "POST":
        usu = request.form["usu"].strip()
        clave = request.form["clave"]
        cnx = db.con()
        cur = cnx.cursor()
        cur.execute("SELECT id, nom, clave, rol FROM per WHERE usu=%s AND act", (usu,))
        f = cur.fetchone()
        cnx.close()
        if f and ch(f[2], clave):
            ses.clear()
            ses["id"], ses["nom"], ses["rol"] = f[0], f[1], f[3]
            return redirect(url_for("inicio"))
        err = "Usuario o contraseña incorrectos"
    return render_template("login.html", err=err)

@app.route("/")
def inicio():
    if "id" not in ses:
        return redirect(url_for("login"))
    return render_template("inicio.html", nom=ses["nom"], rol=ses["rol"])

@app.route("/salir")
def salir():
    ses.clear()
    return redirect(url_for("login"))

PMAX = 200

def dm(a, b, c, d):
    R = 6371000
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = p2 - p1, math.radians(d - b)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


ZH = ZoneInfo("America/Asuncion")

def tard(cur, pid, tol):
    n = datetime.now(ZH)
    cur.execute(
        "SELECT ini FROM hor WHERE per_id=%s AND dia=%s AND fin > %s "
        "ORDER BY ini LIMIT 1", (pid, n.isoweekday(), n.time()))
    f = cur.fetchone()
    if not f:
        return None
    lim = datetime.combine(n.date(), f[0], tzinfo=ZH) + timedelta(minutes=tol)
    return n > lim

def prox(cur, pid):
    cur.execute(
        "SELECT tipo FROM marc WHERE per_id=%s AND ok "
        "AND (fh AT TIME ZONE 'America/Asuncion')::date = "
        "(now() AT TIME ZONE 'America/Asuncion')::date "
        "ORDER BY fh DESC LIMIT 1", (pid,))
    f = cur.fetchone()
    return "sal" if f and f[0] == "ent" else "ent"

@app.route("/marcar")
def marcar():
    if "id" not in ses:
        return redirect(url_for("login"))
    cnx = db.con()
    cur = cnx.cursor()
    t = prox(cur, ses["id"])
    cnx.close()
    return render_template("marcar.html", t=t, nom=ses["nom"])

@app.route("/api/marcar", methods=["POST"])
def api_marcar():
    if "id" not in ses:
        return jsonify(ok=False, msg="Sesión vencida, vuelve a ingresar"), 401
    j = request.get_json()
    lat, lon, prec = float(j["lat"]), float(j["lon"]), float(j["prec"])
    cnx = db.con()
    cur = cnx.cursor()
    cur.execute("SELECT lat, lon, radio, tol FROM conf LIMIT 1")
    c = cur.fetchone()
    if not c:
        cnx.close()
        return jsonify(ok=False, msg="Falta configurar la ubicación del colegio")
    if prec > PMAX:
        cnx.close()
        return jsonify(ok=False, msg=f"Ubicación poco precisa ({prec:.0f} m). Reintenta.")
    t = prox(cur, ses["id"])
    d = dm(lat, lon, c[0], c[1])
    ok = d <= c[2]
    mot = None if ok else "Fuera del área permitida"
    tar = tard(cur, ses["id"], c[3]) if ok and t == "ent" else None
    cur.execute(
        "INSERT INTO marc (per_id, tipo, dist, prec, ok, motivo, tarde) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)", (ses["id"], t, d, prec, ok, mot, tar))
    cnx.commit()
    cnx.close()
    if ok:
        if t == "sal":
            return jsonify(ok=True, msg="Salida registrada")
        return jsonify(ok=True, msg="Entrada registrada" + (" (llegada tarde)" if tar else ""))
    return jsonify(ok=False, msg=f"Estás a {d:.0f} m. Debes estar a menos de {c[2]:.0f} m del colegio.")
def adm(fn):
    @wraps(fn)
    def w(*a, **k):
        if "id" not in ses:
            return redirect(url_for("login"))
        if ses.get("rol") != "admin":
            return "Solo para administradores", 403
        return fn(*a, **k)
    return w

@app.before_request
def vivo():
    if "id" in ses and request.endpoint not in ("login", "salir", "static"):
        cnx = db.con()
        cur = cnx.cursor()
        cur.execute("SELECT act FROM per WHERE id=%s", (ses["id"],))
        f = cur.fetchone()
        cnx.close()
        if not f or not f[0]:
            ses.clear()
            return redirect(url_for("login"))

@app.route("/admin")
@adm
def admin():
    cnx = db.con()
    cur = cnx.cursor()
    cur.execute("SELECT id, nom, ape, usu, cat, rol, act FROM per ORDER BY act DESC, ape, nom")
    ps = cur.fetchall()
    cnx.close()
    return render_template("admin.html", ps=ps, err=request.args.get("err"), yo=ses["id"])

@app.route("/admin/agregar", methods=["POST"])
@adm
def agregar():
    f = request.form
    nom, ape, usu = f["nom"].strip(), f["ape"].strip(), f["usu"].strip()
    clave, cat, rol = f["clave"], f["cat"], f["rol"]
    if not (nom and ape and usu) or len(clave) < 6 \
            or cat not in ("prof", "dir", "coord", "emp") or rol not in ("pers", "admin"):
        return redirect(url_for("admin", err="Datos inválidos (la contraseña necesita al menos 6 caracteres)"))
    cnx = db.con()
    cur = cnx.cursor()
    cur.execute("SELECT 1 FROM per WHERE usu=%s", (usu,))
    if cur.fetchone():
        cnx.close()
        return redirect(url_for("admin", err="Ese usuario ya existe"))
    cur.execute(
        "INSERT INTO per (nom, ape, usu, clave, cat, rol) VALUES (%s,%s,%s,%s,%s,%s)",
        (nom, ape, usu, gh(clave), cat, rol))
    cnx.commit()
    cnx.close()
    return redirect(url_for("admin"))

@app.route("/admin/estado/<int:pid>", methods=["POST"])
@adm
def estado(pid):
    if pid == ses["id"]:
        return redirect(url_for("admin", err="No puedes desactivarte a ti mismo"))
    cnx = db.con()
    cur = cnx.cursor()
    cur.execute("UPDATE per SET act = NOT act WHERE id=%s", (pid,))
    cnx.commit()
    cnx.close()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)