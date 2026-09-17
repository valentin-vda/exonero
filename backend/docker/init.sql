-- Se corre una sola vez, al crear el volumen de la base.
-- Las tablas NO van aca: las crea Alembic. Aca solo lo que Alembic no puede
-- crear comodo por si mismo.
CREATE EXTENSION IF NOT EXISTS citext;      -- correo insensible a mayusculas
CREATE EXTENSION IF NOT EXISTS btree_gist;  -- para EXCLUDE USING gist en clase
