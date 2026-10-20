-- Exonero - esquema completo de PostgreSQL 16.
-- Generado desde la spec del modelo entidad-relacion.
--
-- Este archivo es de REFERENCIA y para arrancar rapido. La base del equipo
-- la crea Alembic a partir de los modelos de app/modulos/*/modelos.py;
-- este SQL sirve para leer el esquema entero de un tirón, para pegarlo en
-- una base vacía si hace falta, y para la defensa.
--
-- Corre entero sobre una base vacía, en este orden.

CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TYPE rol_enum            AS ENUM ('estudiante', 'profesor');
CREATE TYPE estado_cuenta_enum  AS ENUM ('activa', 'dada_de_baja');
CREATE TYPE tema_enum           AS ENUM ('claro', 'oscuro');
CREATE TYPE centro_enum         AS ENUM ('escuela', 'liceo', 'utu', 'facultad', 'instituto');
CREATE TYPE modalidad_enum      AS ENUM ('presencial', 'online', 'ambas');
CREATE TYPE lugar_enum          AS ENUM ('espacio_propio', 'a_domicilio', 'ambos', 'espacio_publico');
CREATE TYPE formato_enum        AS ENUM ('individual', 'grupal', 'ambos');
CREATE TYPE ficha_enum          AS ENUM ('borrador', 'publicada', 'pausada');
CREATE TYPE clase_enum          AS ENUM ('pendiente', 'aprobada', 'cancelada', 'dictada', 'no_asistida');
CREATE TYPE actor_enum          AS ENUM ('estudiante', 'profesor');
CREATE TYPE cobro_enum          AS ENUM ('retenido', 'cobrado', 'liberado', 'reembolsado');
CREATE TYPE sentido_enum        AS ENUM ('alumno_a_profesor', 'profesor_a_alumno');

CREATE TABLE barrio (
    id              bigserial PRIMARY KEY,
    nombre          text NOT NULL UNIQUE,
    departamento    text NOT NULL DEFAULT 'Montevideo',
    latitud         numeric(9,6),   -- centroide: con esto Leaflet centra el mapa
    longitud        numeric(9,6),
    creado_el       timestamptz NOT NULL DEFAULT now(),
    actualizado_el  timestamptz
);

CREATE TABLE etapa_educativa (
    id              bigserial PRIMARY KEY,
    nombre          text NOT NULL UNIQUE,   -- ciclo básico, bachillerato, UTU, universidad, ingreso
    orden           int  NOT NULL DEFAULT 0,
    niveles         text[],                 -- {'1.º','2.º','3.º'}
    creado_el       timestamptz NOT NULL DEFAULT now(),
    actualizado_el  timestamptz
);

CREATE TABLE centro_educativo (
    id              bigserial PRIMARY KEY,
    nombre          text NOT NULL,
    tipo            centro_enum NOT NULL,
    barrio_id       bigint REFERENCES barrio(id),
    direccion       text,
    latitud         numeric(9,6),
    longitud        numeric(9,6),
    creado_el       timestamptz NOT NULL DEFAULT now(),
    actualizado_el  timestamptz
);

CREATE TABLE materia (
    id              bigserial PRIMARY KEY,
    nombre          text NOT NULL UNIQUE,
    nombre_corto    text,
    activa          boolean NOT NULL DEFAULT true,
    creado_el       timestamptz NOT NULL DEFAULT now(),
    actualizado_el  timestamptz
);

CREATE TABLE idioma (
    id              bigserial PRIMARY KEY,
    nombre          text NOT NULL UNIQUE,
    creado_el       timestamptz NOT NULL DEFAULT now(),
    actualizado_el  timestamptz
);

-- Comisión e IVA en tabla y no como constante: se cambian sin tocar
-- código y quedan versionadas por fecha.
CREATE TABLE parametro_plataforma (
    id              bigserial PRIMARY KEY,
    clave           text NOT NULL,          -- 'comision_servicio' | 'tasa_iva'
    valor           numeric(10,4) NOT NULL,
    vigente_desde   date NOT NULL DEFAULT CURRENT_DATE,
    creado_el       timestamptz NOT NULL DEFAULT now(),
    actualizado_el  timestamptz,
    UNIQUE (clave, vigente_desde)
);

CREATE TABLE usuario (
    id                bigserial PRIMARY KEY,
    correo            citext NOT NULL UNIQUE,     -- es la credencial; no se cambia
    hash_clave        text   NOT NULL,            -- bcrypt; nunca la clave en texto plano
    nombre            text   NOT NULL,
    apellido          text   NOT NULL,
    documento         text   UNIQUE,
    telefono          text,
    fecha_nacimiento  date,                       -- define si es menor de edad
    foto_base64       text,
    rol               rol_enum NOT NULL,          -- fijo: una cuenta es alumno o profesor
    estado            estado_cuenta_enum NOT NULL DEFAULT 'activa',
    tema              tema_enum NOT NULL DEFAULT 'claro',
    creado_el         timestamptz NOT NULL DEFAULT now(),
    actualizado_el    timestamptz
);

CREATE TABLE perfil_estudiante (
    id                bigserial PRIMARY KEY,
    usuario_id        bigint NOT NULL UNIQUE REFERENCES usuario(id) ON DELETE CASCADE,
    etapa_id          bigint REFERENCES etapa_educativa(id),
    nivel             text,                       -- '5.º de bachillerato'
    centro_id         bigint REFERENCES centro_educativo(id),
    barrio_id         bigint REFERENCES barrio(id),
    direccion         text,
    latitud           numeric(9,6),
    longitud          numeric(9,6),
    adulto_nombre     text,                       -- obligatorio si es menor
    adulto_telefono   text,
    puntaje_promedio  numeric(3,2) NOT NULL DEFAULT 0,  -- lo escribe solo el módulo resenas
    cantidad_resenas  int NOT NULL DEFAULT 0,
    creado_el         timestamptz NOT NULL DEFAULT now(),
    actualizado_el    timestamptz
);

CREATE TABLE perfil_profesor (
    id                      bigserial PRIMARY KEY,
    usuario_id              bigint NOT NULL UNIQUE REFERENCES usuario(id) ON DELETE CASCADE,

    titular                 text,
    biografia               varchar(600),
    titulo_habilitante      text,
    anios_experiencia       int,

    barrio_id               bigint REFERENCES barrio(id),
    direccion_espacio       text,
    latitud                 numeric(9,6),
    longitud                numeric(9,6),
    modalidad               modalidad_enum NOT NULL DEFAULT 'presencial',
    lugar_clase             lugar_enum     NOT NULL DEFAULT 'espacio_propio',
    costo_traslado          numeric(10,2)  NOT NULL DEFAULT 0,

    precio_hora_presencial  numeric(10,2),
    precio_hora_online      numeric(10,2),

    duracion_min            int NOT NULL DEFAULT 60,
    duracion_max            int NOT NULL DEFAULT 120,
    descanso_min            int NOT NULL DEFAULT 0,
    max_clases_dia          int,
    aviso_minimo_horas      int NOT NULL DEFAULT 12,

    formato                 formato_enum NOT NULL DEFAULT 'individual',
    cupo_min                int,
    cupo_max                int,

    estado_ficha            ficha_enum NOT NULL DEFAULT 'borrador',
    puntaje_promedio        numeric(3,2) NOT NULL DEFAULT 0,
    cantidad_resenas        int NOT NULL DEFAULT 0,
    clases_dictadas         int NOT NULL DEFAULT 0,

    creado_el               timestamptz NOT NULL DEFAULT now(),
    actualizado_el          timestamptz,

    CONSTRAINT duracion_coherente CHECK (duracion_max >= duracion_min)
);

CREATE TABLE profesor_materia (
    id                  bigserial PRIMARY KEY,
    perfil_profesor_id  bigint NOT NULL REFERENCES perfil_profesor(id) ON DELETE CASCADE,
    materia_id          bigint NOT NULL REFERENCES materia(id),
    UNIQUE (perfil_profesor_id, materia_id)
);

CREATE TABLE profesor_etapa (
    id                  bigserial PRIMARY KEY,
    perfil_profesor_id  bigint NOT NULL REFERENCES perfil_profesor(id) ON DELETE CASCADE,
    etapa_id            bigint NOT NULL REFERENCES etapa_educativa(id),
    programa            text,                     -- 'Plan 2006'
    UNIQUE (perfil_profesor_id, etapa_id)
);

CREATE TABLE profesor_idioma (
    id                  bigserial PRIMARY KEY,
    perfil_profesor_id  bigint NOT NULL REFERENCES perfil_profesor(id) ON DELETE CASCADE,
    idioma_id           bigint NOT NULL REFERENCES idioma(id),
    UNIQUE (perfil_profesor_id, idioma_id)
);

-- Barrios a los que el profesor se traslada
CREATE TABLE profesor_zona (
    id                  bigserial PRIMARY KEY,
    perfil_profesor_id  bigint NOT NULL REFERENCES perfil_profesor(id) ON DELETE CASCADE,
    barrio_id           bigint NOT NULL REFERENCES barrio(id),
    UNIQUE (perfil_profesor_id, barrio_id)
);

-- Duraciones que se le ofrecen al alumno: 60, 90, 120
CREATE TABLE profesor_duracion (
    id                  bigserial PRIMARY KEY,
    perfil_profesor_id  bigint NOT NULL REFERENCES perfil_profesor(id) ON DELETE CASCADE,
    minutos             int NOT NULL,
    UNIQUE (perfil_profesor_id, minutos)
);

-- 'Cómo es una clase conmigo'
CREATE TABLE punto_metodo (
    id                  bigserial PRIMARY KEY,
    perfil_profesor_id  bigint NOT NULL REFERENCES perfil_profesor(id) ON DELETE CASCADE,
    texto               text NOT NULL,
    orden               int  NOT NULL DEFAULT 0
);

CREATE TABLE foto_lugar (
    id                  bigserial PRIMARY KEY,
    perfil_profesor_id  bigint NOT NULL REFERENCES perfil_profesor(id) ON DELETE CASCADE,
    imagen_base64       text NOT NULL,
    epigrafe            text,
    orden               int  NOT NULL DEFAULT 0,
    es_portada          boolean NOT NULL DEFAULT false,
    creado_el           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE franja_disponibilidad (
    id                  bigserial PRIMARY KEY,
    perfil_profesor_id  bigint NOT NULL REFERENCES perfil_profesor(id) ON DELETE CASCADE,
    dia_semana          smallint NOT NULL,        -- 0 = domingo … 6 = sábado
    hora_inicio         time NOT NULL,
    hora_fin            time NOT NULL,
    modalidad           modalidad_enum NOT NULL DEFAULT 'ambas',
    activa              boolean NOT NULL DEFAULT true,
    creado_el           timestamptz NOT NULL DEFAULT now(),
    actualizado_el      timestamptz,

    CONSTRAINT dia_valido    CHECK (dia_semana BETWEEN 0 AND 6),
    CONSTRAINT franja_valida CHECK (hora_fin > hora_inicio)
);

CREATE TABLE bloqueo (
    id                  bigserial PRIMARY KEY,
    perfil_profesor_id  bigint NOT NULL REFERENCES perfil_profesor(id) ON DELETE CASCADE,
    inicio              timestamptz NOT NULL,
    fin                 timestamptz NOT NULL,
    motivo              text,
    creado_el           timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT bloqueo_valido CHECK (fin > inicio)
);

CREATE TABLE clase (
    id              bigserial PRIMARY KEY,
    estudiante_id   bigint NOT NULL REFERENCES usuario(id),
    profesor_id     bigint NOT NULL REFERENCES usuario(id),
    materia_id      bigint REFERENCES materia(id),
    etapa_id        bigint REFERENCES etapa_educativa(id),
    tema            text,                          -- qué quiere trabajar el alumno

    inicio          timestamptz NOT NULL,
    duracion_min    int NOT NULL,
    fin             timestamptz NOT NULL,          -- lo calcula la app al insertar
    modalidad       modalidad_enum NOT NULL,
    ubicacion       text,                          -- dirección o enlace de videollamada

    estado          clase_enum NOT NULL DEFAULT 'pendiente',
    motivo          text,                          -- de la cancelación
    cancelada_por   actor_enum,

    -- desglose congelado al crear
    precio_hora     numeric(10,2) NOT NULL,
    costo_traslado  numeric(10,2) NOT NULL DEFAULT 0,
    pct_comision    numeric(5,2)  NOT NULL,
    pct_iva         numeric(5,2)  NOT NULL,
    subtotal        numeric(10,2) NOT NULL,
    impuesto        numeric(10,2) NOT NULL,
    total           numeric(10,2) NOT NULL,

    creado_el       timestamptz NOT NULL DEFAULT now(),
    actualizado_el  timestamptz,

    CONSTRAINT clase_valida       CHECK (fin > inicio),
    CONSTRAINT partes_distintas   CHECK (estudiante_id <> profesor_id),
    CONSTRAINT modalidad_concreta CHECK (modalidad IN ('presencial', 'online'))
);

-- La única defensa real contra dos clases encima: si dos alumnos confirman
-- el mismo horario en el mismo segundo, la base rechaza la segunda. Solo
-- aplica a las aprobadas: varias solicitudes pendientes sobre el mismo
-- hueco son legítimas.
ALTER TABLE clase ADD CONSTRAINT clase_sin_superposicion
    EXCLUDE USING gist (
        profesor_id WITH =,
        tstzrange(inicio, fin) WITH &&
    ) WHERE (estado = 'aprobada');

-- ATENCIÓN: guardar número completo y CCV es aceptable en este trabajo
-- académico con datos inventados, pero ninguna plataforma real puede
-- hacerlo. No cargar tarjetas reales en esta tabla.
CREATE TABLE tarjeta (
    id              bigserial PRIMARY KEY,
    usuario_id      bigint NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    numero          text NOT NULL,
    titular         text NOT NULL,
    vence_mes       smallint NOT NULL,
    vence_anio      smallint NOT NULL,
    ccv             text NOT NULL,
    activa          boolean NOT NULL DEFAULT true,
    creado_el       timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT mes_valido CHECK (vence_mes BETWEEN 1 AND 12)
);

-- clase_id admite NULL y es ON DELETE SET NULL, no CASCADE: al rechazar, la
-- clase se borra y el cobro liberado tiene que quedar registrado. El UNIQUE
-- sigue valiendo (PostgreSQL permite varios NULL).
CREATE TABLE cobro (
    id              bigserial PRIMARY KEY,
    clase_id        bigint UNIQUE REFERENCES clase(id) ON DELETE SET NULL,
    tarjeta_id      bigint REFERENCES tarjeta(id),
    importe         numeric(10,2) NOT NULL,
    estado          cobro_enum NOT NULL DEFAULT 'retenido',
    retenido_el     timestamptz NOT NULL DEFAULT now(),
    cobrado_el      timestamptz,    -- al aprobar el profesor
    liberado_el     timestamptz,    -- al rechazar
    reembolsado_el  timestamptz,    -- al cancelar, desde la BackgroundTask
    actualizado_el  timestamptz
);

CREATE TABLE hilo (
    id                  bigserial PRIMARY KEY,
    estudiante_id       bigint NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    profesor_id         bigint NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    ultimo_mensaje_el   timestamptz,    -- por acá se ordena la bandeja
    creado_el           timestamptz NOT NULL DEFAULT now(),

    UNIQUE (estudiante_id, profesor_id)
);

CREATE TABLE mensaje (
    id          bigserial PRIMARY KEY,
    hilo_id     bigint NOT NULL REFERENCES hilo(id) ON DELETE CASCADE,
    autor_id    bigint NOT NULL REFERENCES usuario(id),
    contenido   text NOT NULL,
    enviado_el  timestamptz NOT NULL DEFAULT now(),
    leido_el    timestamptz     -- NULL = sin leer; se completa al abrir el hilo
);

-- Anónimas y en los dos sentidos. El autor se guarda para poder exigir
-- una sola por par y para dejar que la edite, pero NUNCA se devuelve
-- en la API.
CREATE TABLE resena (
    id               bigserial PRIMARY KEY,
    autor_id         bigint NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    destinatario_id  bigint NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    sentido          sentido_enum NOT NULL,
    puntaje          smallint NOT NULL,
    texto            text,
    creado_el        timestamptz NOT NULL DEFAULT now(),
    actualizado_el   timestamptz,

    CONSTRAINT puntaje_valido CHECK (puntaje BETWEEN 1 AND 5),
    CONSTRAINT no_autorresena CHECK (autor_id <> destinatario_id),
    UNIQUE (autor_id, destinatario_id)
);

-- El más usado del sistema: calendario del profesor, cálculo de huecos
-- libres y detección de superposición.
CREATE INDEX ix_clase_profesor_inicio    ON clase (profesor_id, inicio);
CREATE INDEX ix_clase_estudiante_inicio  ON clase (estudiante_id, inicio DESC);
CREATE INDEX ix_clase_estado             ON clase (estado);

CREATE INDEX ix_franja_profesor_dia      ON franja_disponibilidad (perfil_profesor_id, dia_semana);
CREATE INDEX ix_bloqueo_profesor_inicio  ON bloqueo (perfil_profesor_id, inicio);

-- La búsqueda con filtros y el ranking de mejor puntuados
CREATE INDEX ix_profesor_busqueda        ON perfil_profesor (estado_ficha, barrio_id, puntaje_promedio DESC);
CREATE INDEX ix_profesor_materia_materia ON profesor_materia (materia_id);
CREATE INDEX ix_profesor_etapa_etapa     ON profesor_etapa (etapa_id);
CREATE INDEX ix_profesor_zona_barrio     ON profesor_zona (barrio_id);

-- Historial del chat y contador de no leídos
CREATE INDEX ix_mensaje_hilo_enviado     ON mensaje (hilo_id, enviado_el DESC);
CREATE INDEX ix_mensaje_sin_leer         ON mensaje (hilo_id) WHERE leido_el IS NULL;

CREATE INDEX ix_resena_destinatario      ON resena (destinatario_id);
CREATE INDEX ix_cobro_estado             ON cobro (estado);