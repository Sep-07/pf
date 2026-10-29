
/* DICCIONARIO
per   = personal (todas las personas del colegio)
disp  = dispositivos (celular vinculado a cada persona)
marc  = marcaciones (entradas y salidas, no se pueden modificar)
curso = cursos del colegio
hor   = horarios de clases de profesores
conf  = configuración general (una sola fila)

id     = identificador
per_id = id de la persona en per
disp_id= id del dispositivo en disp
curso_id = id del curso en curso
nom / ape = nombre / apellido
usu    = usuario para iniciar sesión
clave  = contraseña cifrada (nunca en texto plano)
cat    = categoría: prof, dir, coord, emp
rol    = pers (normal) o admin (coordinación y dirección)
act    = activo (true/false)
tok    = código aleatorio que identifica el celular
aut    = dispositivo autorizado (true/false)
creado = cuándo se vinculó el dispositivo
tipo   = ent (entrada) o sal (salida)
fh     = fecha y hora de la marcación (la pone el servidor)
dist   = distancia al colegio en metros
prec   = precisión del GPS en metros
ok     = marcación aceptada (true/false)
motivo = motivo del rechazo, si lo hubo
tarde  = llegó tarde (true/false), solo en entradas
dia    = día de la semana: 1 lunes ... 7 domingo
ini/fin= hora de inicio y fin de la clase
lat/lon= coordenadas del colegio
radio  = radio permitido en metros
tol    = minutos de tolerancia antes de contar como tarde
*/

DROP TABLE IF EXISTS marc, hor, curso, disp, conf, per CASCADE;
DROP FUNCTION IF EXISTS bloq() CASCADE;

CREATE TABLE per (
    id SERIAL PRIMARY KEY,
    nom TEXT NOT NULL,
    ape TEXT NOT NULL,
    usu TEXT NOT NULL UNIQUE,
    clave TEXT NOT NULL,
    cat TEXT NOT NULL CHECK (cat IN ('prof','dir','coord','emp')),
    rol TEXT NOT NULL DEFAULT 'pers' CHECK (rol IN ('pers','admin')),
    act BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE disp (
    id SERIAL PRIMARY KEY,
    per_id INT NOT NULL REFERENCES per(id),
    tok TEXT NOT NULL UNIQUE,
    aut BOOLEAN NOT NULL DEFAULT TRUE,
    creado TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE marc (
    id SERIAL PRIMARY KEY,
    per_id INT NOT NULL REFERENCES per(id),
    disp_id INT REFERENCES disp(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('ent','sal')),
    fh TIMESTAMPTZ NOT NULL DEFAULT now(),
    dist REAL,
    prec REAL,
    ok BOOLEAN NOT NULL,
    motivo TEXT,
    tarde BOOLEAN
);

CREATE TABLE curso (
    id SERIAL PRIMARY KEY,
    nom TEXT NOT NULL UNIQUE
);

CREATE TABLE hor (
    id SERIAL PRIMARY KEY,
    per_id INT NOT NULL REFERENCES per(id),
    curso_id INT REFERENCES curso(id),
    dia SMALLINT NOT NULL CHECK (dia BETWEEN 1 AND 7),
    ini TIME NOT NULL,
    fin TIME NOT NULL
);

CREATE TABLE conf (
    id SERIAL PRIMARY KEY,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    radio REAL NOT NULL DEFAULT 100,
    tol INT NOT NULL DEFAULT 10
);

CREATE FUNCTION bloq() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Las marcaciones no se pueden modificar ni borrar';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER marc_fija
BEFORE UPDATE OR DELETE ON marc
FOR EACH ROW EXECUTE FUNCTION bloq();

SELECT nom, usu, cat, rol, clave FROM per;

SELECT lat, lon, radio FROM conf;

SELECT * FROM marc ORDER BY id DESC;