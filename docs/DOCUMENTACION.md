# Exonero — documentación del proyecto

Todo lo que hay que saber para trabajar acá sin tener que leer el código.
Está escrita sobre todo pensando en el frontend, que es lo que más cuesta
cuando uno viene de backend.

**Índice**

1. [Qué es esto y cómo se levanta](#1-qué-es-esto-y-cómo-se-levanta)
2. [Estructura de carpetas](#2-estructura-de-carpetas)
3. [Arquitectura general](#3-arquitectura-general)
4. [El backend](#4-el-backend)
5. [El frontend](#5-el-frontend)
6. [Login y registro, paso a paso](#6-login-y-registro-paso-a-paso)
7. [Cuentas y perfiles (P1), de punta a punta](#7-cuentas-y-perfiles-p1-de-punta-a-punta)
8. [Catálogos y búsqueda (P2), de punta a punta](#8-catálogos-y-búsqueda-p2-de-punta-a-punta)
9. [Clases y pagos (P4), de punta a punta](#9-clases-y-pagos-p4-de-punta-a-punta)
10. [El sistema de diseño](#10-el-sistema-de-diseño)
11. [Flujos completos](#11-flujos-completos)
12. [Qué está hecho y qué falta](#12-qué-está-hecho-y-qué-falta)
13. [Cosas que hay que decidir](#13-cosas-que-hay-que-decidir)

---

## 1. Qué es esto y cómo se levanta

Exonero es una plataforma de clases particulares: un alumno busca profesores
por materia, barrio, precio y horario, mira la agenda real del profe, reserva
un hueco y paga. El profesor aprueba o rechaza cada solicitud.

El proyecto es un **monorepo**: frontend, backend y `docker-compose.yml` en el
mismo lugar, una rama principal y un *pull request* por pantalla.

### Levantarlo por primera vez

Hace falta **Python 3.13 o 3.14** (`python --version`), Node y Docker Desktop
abierto.

```bash
# 1. La base de datos (es lo unico que corre en Docker)
docker compose up -d            # queda en localhost:5433, no en el 5432 (ver abajo)

# 2. El backend
cd backend
python -m venv .venv            # o py -3.13 -m venv .venv si tenes otra version por defecto
.venv\Scripts\activate          # en Windows
pip install -r requirements.txt
copy .env.example .env          # y revisar los valores
alembic upgrade head            # crea las 24 tablas
python -m app.seeds             # carga los datos de prueba
uvicorn app.main:app --reload   # queda en http://localhost:8000

# 3. El frontend, en otra terminal
cd frontend
npm install
npm run dev                     # queda en http://localhost:5173
```

Abrí `http://localhost:5173` y te va a recibir el login.

Los seeds dejan cargados veinte usuarios, todos con la clave `exonero123`:
`profe1@example.com` a `profe8@example.com` y `alumno1@example.com` a
`alumno12@example.com`. En el login hay dos botones, **Alumno** y **Profe**,
que completan el formulario con el primero de cada uno.

¿Por qué `example.com` y no un dominio inventado como `exonero.test`? Porque
el validador de correos del backend rechaza los dominios `.test` (son de "uso
especial"), y con esos usuarios no se podría entrar. `example.com` está
reservado para ejemplos: no es de nadie.

**Por qué el 5433 y no el 5432.** El 5432 es el puerto por defecto de
PostgreSQL, y si alguna vez lo instalaste en Windows (para otra materia, por
ejemplo) ese servicio ya lo tiene ocupado. Con el contenedor en el 5432,
Alembic termina hablando con *tu* PostgreSQL y no con el del proyecto, y falla
con `password authentication failed for user "exonero"`. Adentro del
contenedor sigue siendo el 5432; lo que cambia es el de afuera, en
`docker-compose.yml` y en `BASE_URL` del `.env`.

### Las tres URLs que importan

| URL | Qué es |
|---|---|
| `http://localhost:5173` | La aplicación |
| `http://localhost:8000/docs` | La documentación interactiva de la API. **Acá se prueba el backend sin frontend**: cada endpoint tiene un botón "Try it out" |
| `http://localhost:8000/api/salud` | Prueba de vida. Si esto no responde, el backend no está levantado |

### Por qué solo PostgreSQL va en Docker

Para que los cuatro corramos la misma versión de base, con el mismo esquema y
los mismos datos de prueba. El backend y el frontend corren locales porque así
el *hot reload* funciona: guardás un archivo y el cambio se ve al instante, sin
reconstruir una imagen.

---

## 2. Estructura de carpetas

```
exonero/
├── docker-compose.yml          solo PostgreSQL
├── DOCUMENTACION.md            este archivo
│
├── backend/
│   ├── requirements.txt
│   ├── .env.example            copiar a .env
│   ├── alembic.ini
│   ├── schema.sql              el esquema completo, de referencia
│   ├── verificar_p4.py         las comprobaciones de P4 (ver la seccion 9)
│   ├── docker/init.sql         extensiones citext y btree_gist
│   ├── alembic/
│   │   ├── env.py              lee la conexion del .env
│   │   └── versions/           una migracion por pull request
│   └── app/
│       ├── main.py             crea la app y monta los routers
│       ├── config.py           toda la configuracion, leida del .env
│       ├── db.py               engine, sesion y la clase Base
│       ├── enums.py            los 12 tipos ENUM de PostgreSQL
│       ├── seguridad.py        hash bcrypt y firma de tokens
│       ├── errores.py          ErrorAPI y el formato unico de error
│       ├── fechas.py           la zona de Montevideo, periodos y ventanas de 1d
│       ├── dependencias.py     quien es el usuario del token
│       ├── registro_modelos.py importa los 9 modulos (solo para Alembic)
│       ├── seeds.py            datos de prueba
│       └── modulos/
│           ├── cuentas/        P1 - identidad, login, registro
│           ├── perfiles/       P1 - los dos perfiles y la ficha publica
│           ├── catalogos/      P2 - materias, etapas, barrios, centros...
│           ├── busqueda/       P2 - los nueve filtros, mapas y ranking
│           ├── agenda/         P3 - disponibilidad y huecos libres
│           ├── clases/         P4 - el ciclo de vida de la clase
│           ├── pagos/          P4 - tarjetas y cobros simulados
│           ├── mensajeria/     P3 - hilos y mensajes
│           └── resenas/        P3 - resenas anonimas en los dos sentidos
│
└── frontend/
    ├── package.json
    ├── vite.config.js          el proxy de /api a localhost:8000
    ├── index.html              carga las tipografias
    └── src/
        ├── main.jsx            punto de entrada
        ├── App.jsx             el mapa de rutas
        ├── estilos/
        │   ├── tokens.css      colores, tipografias, espaciado (y modo oscuro)
        │   ├── componentes.css .btn .input .card .tag .nav ...
        │   ├── auth.css        login y registro
        │   ├── perfil.css      las pantallas de perfil (1e y 1j)
        │   ├── panel.css       el panel del profesor (1d) y sus graficos
        │   └── pagos.css       el checkout (1g) y "Medios de pago" (1e)
        ├── api/
        │   ├── cliente.js      el fetch con token y manejo de errores
        │   ├── mensajes.js     codigo de error -> texto en espanol
        │   ├── auth.js         una funcion por endpoint de cuentas
        │   ├── perfiles.js     una funcion por endpoint de perfiles
        │   ├── clases.js       una funcion por endpoint de clases (P4)
        │   ├── pagos.js        una funcion por endpoint de pagos (P4)
        │   └── agenda.js       por ahora solo verificar (lo usa 1g)
        ├── auth/
        │   ├── ContextoAuth.jsx  quien esta conectado (y su tema)
        │   └── RutaProtegida.jsx rutas que exigen sesion
        ├── componentes/
        │   ├── Layout.jsx        la barra de navegacion
        │   ├── MarcoAuth.jsx     el layout de dos columnas
        │   ├── Campo.jsx         etiqueta + input + error
        │   ├── CampoClave.jsx    con el boton de mostrar/ocultar
        │   ├── CampoSelect.jsx   etiqueta + desplegable + error
        │   ├── ListaEtiquetas.jsx etiquetas que se quitan + "+ Agregar"
        │   ├── Avatar.jsx        la foto o las iniciales, en tres tamanios
        │   ├── InterruptorTema.jsx modo claro / modo oscuro
        │   ├── SelectorRol.jsx   las dos tarjetas del registro
        │   ├── Alerta.jsx        el cartel de error, de exito o de aviso
        │   ├── FormularioTarjeta.jsx los campos de una tarjeta (1g y 1e)
        │   └── EnConstruccion.jsx marcador de las pantallas pendientes
        ├── paginas/
        │   ├── Login.jsx         HECHA
        │   ├── Registro.jsx      HECHA
        │   ├── RecuperarClave.jsx HECHA
        │   ├── PerfilEstudiante.jsx  1e, HECHA
        │   ├── PerfilProfesor.jsx    1j, HECHA
        │   ├── Checkout.jsx      1g, HECHA
        │   ├── PanelProfesor.jsx 1d, HECHA
        │   ├── perfil/           las piezas de 1e y 1j (ver la seccion 7)
        │   ├── checkout/         las piezas de 1g (ver la seccion 9)
        │   └── panel/            las piezas de 1d y sus graficos (seccion 9)
        └── utiles/
            ├── validaciones.js
            ├── formato.js        iniciales, fechas, horas, importes, puntajes
            ├── tarjetas.js       formato y validacion de las tarjetas
            └── imagenes.js       achicar una foto antes de subirla
```

### Cada módulo del backend tiene siempre los mismos cuatro archivos

| Archivo | Qué va adentro | Quién lo puede importar |
|---|---|---|
| `modelos.py` | Las tablas (SQLAlchemy) | **Nadie de afuera del módulo** |
| `esquemas.py` | Los contratos de entrada y salida (Pydantic) | El propio módulo |
| `logica.py` | Las funciones públicas | **Los otros módulos** |
| `rutas.py` | Los endpoints HTTP | El frontend, vía HTTP |

**La regla dura: nadie importa `modelos.py` de otro módulo.** Si el módulo
`clases` necesita saber el precio de un profesor, no lee la tabla
`perfil_profesor`: llama a `perfiles.logica.precio_vigente()`. Así cada uno
puede cambiar sus tablas sin romper a los demás.

Las claves foráneas se declaran **por nombre de tabla**, no importando la clase:

```python
# perfiles/modelos.py
barrio_id: Mapped[int | None] = mapped_column(ForeignKey("barrio.id"))
#                                                        ^^^^^^^^^ texto,
#                                         no una importacion de catalogos
```

La única excepción es `app/registro_modelos.py`, que importa los nueve módulos
en un solo lugar. Existe por un motivo técnico: Alembic necesita ver las 24
tablas juntas para poder comparar los modelos con la base. Si un módulo no
aparece ahí, `autogenerate` cree que sus tablas no existen y escribe un
`DROP TABLE`.

---

## 3. Arquitectura general

```
   NAVEGADOR                        localhost:5173
   ┌──────────────────────────────────────────────┐
   │  React + Vite                                │
   │                                              │
   │  paginas/          las pantallas             │
   │  componentes/      piezas reutilizables      │
   │  auth/             quien esta conectado      │
   │  api/cliente.js    <- TODO fetch pasa por aca│
   └───────────────────┬──────────────────────────┘
                       │  fetch("/api/...")
                       │  Authorization: Bearer <token>
                       ▼
   ┌──────────────────────────────────────────────┐
   │  Proxy de Vite  (solo en desarrollo)         │
   │  /api/*  ->  http://localhost:8000/api/*     │
   └───────────────────┬──────────────────────────┘
                       ▼                localhost:8000
   ┌──────────────────────────────────────────────┐
   │  FastAPI                                     │
   │                                              │
   │   rutas.py     valida la entrada, responde   │
   │      ↓                                       │
   │   logica.py    las reglas del negocio        │
   │      ↓                                       │
   │   modelos.py   las tablas                    │
   └───────────────────┬──────────────────────────┘
                       ▼                localhost:5433
   ┌──────────────────────────────────────────────┐
   │  PostgreSQL 16  (en Docker)                  │
   │  24 tablas, 12 tipos ENUM                    │
   └──────────────────────────────────────────────┘
```

### Por qué el proxy

En React nunca escribimos `http://localhost:8000/api/login`. Escribimos
`/api/login` a secas. Vite ve que empieza con `/api` y lo reenvía al backend.

Dos ventajas: el código no tiene ninguna URL absoluta (el día que se despliegue
no hay que cambiar nada), y el navegador cree que todo viene del mismo origen,
así que no hay problemas de CORS en desarrollo.

Está configurado en `frontend/vite.config.js`.

### El token

No hay sesiones guardadas en la base. El login devuelve un **JWT**, que es un
texto firmado que dice "este es el usuario 12, rol estudiante, válido hasta
mañana". El frontend lo guarda y lo manda en cada llamada:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

El backend verifica la firma y saca de ahí el id y el rol. Como está firmado,
nadie puede fabricar uno ni cambiarle el rol.

**Se guarda en `sessionStorage`, no en `localStorage`**: cerrar la pestaña es
cerrar sesión. Es lo que pide la spec ("no se guarda sesión: vive en el
frontend y vence solo").

Cerrar sesión no tiene endpoint: es borrar el token del navegador.

---

## 4. El backend

### Los nueve módulos y quién los hace

| Módulo | Dueño | Responsabilidad | Tablas |
|---|---|---|---|
| `cuentas` | P1 | Registro, login, token, contraseña, foto, baja | 1 |
| `perfiles` | P1 | Los dos perfiles y toda la oferta del profesor. Sirve la ficha pública | 9 |
| `catalogos` | P2 | Materias, etapas, centros, barrios, idiomas, comisión e IVA | 6 |
| `busqueda` | P2 | Los nueve filtros, orden, paginación, mapas y ranking | 0 |
| `agenda` | P3 | Franjas, bloqueos y el cálculo de huecos libres | 2 |
| `clases` | P4 | El ciclo de vida de la clase y las métricas del panel | 1 |
| `pagos` | P4 | Tarjetas, cobro simulado, reembolso, historial e ingresos | 2 |
| `mensajeria` | P3 | Hilos, mensajes y no leídos | 2 |
| `resenas` | P3 | Reseñas anónimas en los dos sentidos | 1 |

`busqueda` no tiene tablas propias: consulta las de `perfiles` y `catalogos`.

### Quién llama a quién

```
  cuentas ---------------> lo llaman TODOS (obtener_usuario)
     |
     +--> mensajeria.contar_no_leidos()     para GET /usuarios/yo
     +--> perfiles.cabecera_estudiante()    para el saludo de 1a

  perfiles --> lee nombres de los catalogos por nombre de tabla,
               solo lectura (ver la seccion 7)
           --> cuentas.datos_basicos(), es_menor()

  busqueda --> perfiles.ficha_resumida()    completar los resultados
           --> catalogos.centroide_barrio() calcular distancias
           --> agenda.filtrar_con_hueco()   el filtro de disponibilidad

  agenda   --> perfiles.reglas_profesor()   descanso, tope, aviso minimo
           --> clases.clases_aprobadas_entre()  descontar lo ocupado

  clases   --> perfiles.precio_vigente(), reglas_profesor(),
               condiciones_de_reserva()     cotizar
           --> catalogos.parametros_vigentes()  comision e IVA
           --> agenda.verificar()           sigue libre el horario?
           --> pagos.retener/cobrar/liberar/reembolsar()
           --> cuentas y perfiles, en lote  la contraparte de cada clase
           --> resenas.resena_de()          mi_resena

  pagos    --> cuentas.datos_basicos_varios()  el profesor de cada pago
               (lee la tabla clase "de lejos", ver la seccion 9)

  resenas  --> clases.tuvieron_clase()      solo resena quien tuvo clase
           --> perfiles.escribir_puntaje()  guardar el promedio
```

**`cuentas` y `catalogos` bloquean a todos los demás.** Por eso van primero en
el orden de trabajo.

### Cómo se responde un error

Siempre igual, y siempre con un código corto y estable en `snake_case`:

```json
{ "detail": "horario_ocupado" }
```

| Código | Cuándo |
|---|---|
| `400` | Datos inválidos |
| `401` | Sin token, o vencido |
| `402` | El cobro simulado falló |
| `403` | No es tuyo |
| `404` | No existe |
| `409` | Conflicto de estado (`horario_ocupado`, `ya_resenado`, ...) |
| `422` | Falla de validación (la tira FastAPI sola) |

El texto en español **no está en el backend**: está en
`frontend/src/api/mensajes.js`. Así se puede cambiar la redacción sin tocar
Python, y el día que haya otro idioma es un archivo más.

### Las decisiones de modelado que más cuesta entender

**Una tabla `usuario`, dos de perfil.** Estudiante y profesor comparten correo,
clave, nombre, documento y foto. Con dos tablas paralelas habría dos lugares
para hacer login, dos para cambiar la contraseña, y ninguno del cual colgar el
chat, que une a los dos. El rol es una columna, no una tabla.

**La clase es la reserva.** No hay tabla de reservas. Se crea una clase en
estado `pendiente`; el profesor la aprueba y pasa a `aprobada`, o la rechaza y
**la fila se borra**. Cancelar no borra: cambia el estado, porque el historial
y el reembolso lo necesitan.

**Los importes van congelados en la clase.** `precio_hora`, `pct_comision` y
`pct_iva` se copian al crearla. Si mañana el profesor sube su precio, las
clases ya creadas siguen valiendo lo mismo y el comprobante sigue cuadrando.

**La disponibilidad se guarda en positivo.** `franja_disponibilidad` dice
cuándo el profesor **sí** puede, repetido cada semana; `bloqueo` es la
excepción puntual con fecha. Guardando solo "horarios no disponibles" no se
puede dibujar el calendario: no habría forma de distinguir un hueco libre de
uno del que nunca se dijo nada.

**El puntaje está desnormalizado.** `puntaje_promedio` y `cantidad_resenas`
viven en los dos perfiles, y **solo los escribe el módulo `resenas`**.
Calcularlos al vuelo obligaría a recorrer la tabla de reseñas en cada resultado
de búsqueda.

**El autor de la reseña se guarda, aunque sean anónimas.** Hace falta para
exigir una sola por par y para dejar que la edite. El anonimato se resuelve en
la respuesta de la API, no borrando el dato.

**Una sola tabla de plata: `cobro`.** Los ingresos del profesor son
`sum(importe)` sobre sus cobros en estado `cobrado`. El estado del pago no
puede vivir en `clase` porque la clase rechazada se borra y el cobro liberado
tiene que quedar registrado. Por eso `cobro.clase_id` admite NULL, con
`ON DELETE SET NULL`: la migración inicial lo tenía con `CASCADE` y borraba el
cobro junto con la clase; lo arregló la segunda migración (sección 9).

**La restricción `EXCLUDE`.** Es lo único que impide de verdad que dos alumnos
confirmen el mismo horario en el mismo instante:

```sql
ALTER TABLE clase ADD CONSTRAINT clase_sin_superposicion
EXCLUDE USING gist (profesor_id WITH =, tstzrange(inicio, fin) WITH &&)
WHERE (estado = 'aprobada');
```

Validarlo solo en Python deja una ventana de carrera que en la demostración se
puede notar. Va escrita a mano en la migración: Alembic no la genera sola.

### Migraciones

| Comando | Cuándo |
|---|---|
| `alembic revision --autogenerate -m "..."` | Después de cambiar un modelo |
| `alembic upgrade head` | Después de cada `git pull` |
| `alembic downgrade -1` | Para volver atrás mientras se prueba |
| `python -m app.seeds` | Recargar los datos de prueba |

Cuatro reglas:

1. **Una revisión por pull request.** Si una rama trae tres migraciones
   sueltas, el orden se vuelve imposible de seguir al mezclar ramas.
2. **Leer lo que generó el autogenerador.** Alembic interpreta "renombré una
   columna" como "borré una y creé otra", y con eso se pierden los datos.
3. **Nunca editar una migración ya aplicada.** Si otro ya la corrió, editarla
   deja las dos bases distintas con el mismo número de versión. Se arregla con
   una revisión nueva.
4. **Cada uno migra solo sus tablas.** Si P3 necesita una columna en `clase`,
   se la pide a P4.

Dos trampas que ya nos pasaron con la migración inicial:

- **Los tipos ENUM en el `downgrade`.** `drop_table` no borra los ENUM que
  creó la tabla, así que el `downgrade` que escribe el autogenerador deja la
  base a medio limpiar y el siguiente `upgrade` falla con
  `type "..." already exists`. Si tu migración crea un ENUM nuevo, agregá a
  mano el `DROP TYPE` al final del `downgrade`, como en la inicial.
- **Un `server_default` con una función de SQL va con `text()`**:
  `server_default=text("CURRENT_DATE")`. Con la cadena suelta, SQLAlchemy la
  manda entre comillas, como un literal, y PostgreSQL rechaza la tabla. Lo
  mismo para el `postgresql_where` de un índice parcial: `text(...)` en
  minúscula, no `Text`, que es el tipo de columna.

---

## 5. El frontend

Esta sección es la más larga a propósito: es la parte que pediste para
aprender.

### Las cinco piezas de React que hay que entender

Si nunca tocaste React, estas cinco ideas alcanzan para leer todo el código
que hay acá.

#### 1. Un componente es una función que devuelve HTML

```jsx
function Saludo() {
  return <h1>Hola</h1>
}
```

Eso es todo. Se usa como si fuera una etiqueta: `<Saludo />`.

Ese HTML adentro de JavaScript se llama **JSX**. No es HTML de verdad: es
azúcar sintáctico que Vite convierte en llamadas a funciones. Por eso hay dos
diferencias con el HTML normal:

- `class` se escribe `className` (porque `class` es palabra reservada en JS)
- `for` en un label se escribe `htmlFor`

#### 2. Las props son los parámetros

```jsx
function Saludo({ nombre }) {
  return <h1>Hola {nombre}</h1>
}

<Saludo nombre="Martina" />   // muestra "Hola Martina"
```

Las llaves `{}` adentro del JSX quieren decir "acá va JavaScript".

#### 3. El estado es la memoria del componente

```jsx
const [correo, setCorreo] = useState('')
//     ^valor  ^para cambiarlo      ^valor inicial
```

**La regla de oro: nunca se modifica el valor directo.** Se llama a la función
`setX`. Cuando se la llama, React vuelve a ejecutar la función del componente
y redibuja lo que cambió.

Esto está mal y no hace nada:
```jsx
correo = 'ana@mail.com'        // NO
```
Esto está bien:
```jsx
setCorreo('ana@mail.com')      // SI
```

#### 4. Un input controlado

Los inputs de estos formularios funcionan así:

```jsx
<input value={correo} onChange={(e) => setCorreo(e.target.value)} />
```

Se lee: "el valor del input es la variable `correo`, y cuando el usuario
escribe, guardá lo que escribió en `correo`".

El valor **siempre** viene del estado. Si te olvidás el `onChange`, el input
queda congelado: el usuario escribe y no pasa nada, porque React lo redibuja
con el valor viejo.

#### 5. `useEffect` es para lo que pasa "además de dibujar"

Pedirle datos al backend, poner un temporizador, escuchar un evento. Se usa
una sola vez en todo el código actual, en `ContextoAuth.jsx`:

```jsx
useEffect(() => {
  // esto corre DESPUES de que el componente se dibujo
}, [])   // <- el array vacio significa "una sola vez, al montarse"
```

### Seis ideas más, que aparecen en las pantallas de perfil

Con las cinco de arriba se lee el login. Las pantallas de perfil (1e y 1j)
usan además estas seis. Todos los ejemplos son del código real.

#### 6. Mostrar algo solo si se cumple una condición

```jsx
{daOnline && <Campo id="precioOnline" etiqueta="Precio por hora online" ... />}
{foto.es_portada ? <span className="tag">Portada</span> : null}
```

`condicion && <X />` se lee "si la condición es verdadera, dibujá X". Si es
falsa, no se dibuja nada. Para elegir entre dos cosas está el ternario:
`condicion ? esto : aquello`. Así 1j esconde el precio presencial cuando el
profesor da clase solo online (`SeccionEnsena.jsx`).

#### 7. Las listas se dibujan con `map`, y nunca se modifican: se reemplazan

```jsx
{seleccion.map((id) => (
  <button key={id} onClick={() => quitar(id)}>{nombreDe(id)}</button>
))}
```

`map` recorre la lista y devuelve un elemento por cada valor. Para cambiar una
lista del estado **no** se usa `push` ni `splice`: se arma una lista nueva y
se le pasa al `set`.

```js
alCambiar(seleccion.filter((x) => x !== idQuitado))  // sin ese elemento
alCambiar([...seleccion, idNuevo])                   // con uno mas
```

React compara la lista vieja con la nueva para saber qué redibujar. Si se
modifica la misma lista, React no ve el cambio (`ListaEtiquetas.jsx`).

#### 8. `children` es lo que va entre las etiquetas

```jsx
<MenuLateral pestanias={PESTANIAS} activa={pestania} alElegir={setPestania}>
  <div>Perfil 82 % completo</div>      {/* <- esto es children */}
</MenuLateral>
```

Adentro de `MenuLateral`, `{children}` dibuja ese contenido en el lugar que
corresponda. Así el mismo menú sirve para 1e (que no pasa nada) y para 1j
(que pasa la barra de progreso y el botón de publicar).

#### 9. El estado lo guarda quien lo necesita para decidir

```jsx
// PerfilProfesor.jsx
const [pestania, setPestania] = useState('datos')
...
<MenuLateral activa={pestania} alElegir={setPestania} />
{pestania === 'bio' && <SeccionBio ... />}
```

El menú muestra las pestañas, pero **no** guarda cuál está elegida: la que
decide qué sección dibujar es la pantalla, así que el estado vive ahí. El menú
recibe el valor (`activa`) y una función para avisar (`alElegir`). A esto se
le dice "subir el estado". Es la misma idea que un input controlado.

#### 10. `useState` con una función: el valor inicial se calcula una vez

```jsx
const [campos, setCampos] = useState(() => valoresIniciales(usuario, perfil))
```

Si se le pasa una función, React la ejecuta solo la primera vez que dibuja el
componente. Cada sección de perfil arranca así su formulario a partir de lo
que vino del backend, y "Cancelar" vuelve a llamar a `valoresIniciales()`
para descartar lo que se escribió.

#### 11. `async`/`await`, `try`/`catch`/`finally` y `Promise.all`

```js
async function guardar(evento) {
  evento.preventDefault()
  setGuardando(true)
  try {
    await actualizarYo({...})            // espera a que responda
    await guardarPerfilEstudiante({...}) // recien despues, esta
    setMensaje({ tipo: 'ok', texto: 'Listo...' })
  } catch (error) {
    setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
  } finally {
    setGuardando(false)                  // pase lo que pase
  }
}
```

`await` espera la respuesta antes de seguir con la línea siguiente. Si el
backend responde un error, salta al `catch`. El `finally` corre siempre.

Para pedir dos cosas **al mismo tiempo** (y no una detrás de la otra) está
`Promise.all`. Las pantallas de perfil lo usan al entrar:

```js
Promise.all([obtenerMiFicha(), obtenerCatalogos().catch(() => null)])
  .then(([ficha, catalogos]) => { ... })
```

El `.catch(() => null)` de los catálogos hace que, si fallan, la pantalla
siga funcionando igual con `catalogos = null` (ver la sección 7).

### Cómo viaja un dato del formulario al backend

Este es el recorrido completo, con los archivos reales:

```
  El usuario escribe en el input
            |
            v
  Login.jsx        onChange -> setCorreo(...)
            |
            v
  Login.jsx        al enviar el formulario: valida con validaciones.js
            |
            v
  ContextoAuth     entrar(correo, clave)
            |
            v
  api/auth.js      login() arma el cuerpo { correo, clave }
            |
            v
  api/cliente.js   pedir() hace el fetch, agrega el token y las cabeceras
            |
            v
  vite.config.js   el proxy manda /api/... a localhost:8000
            |
            v
  BACKEND          POST /api/auth/login
```

Y la vuelta, si algo falla:

```
  BACKEND      409 { "detail": "credenciales_invalidas" }
            |
            v
  cliente.js   lanza un ErrorAPI con codigo = "credenciales_invalidas"
            |
            v
  Login.jsx    lo agarra en el catch
            |
            v
  mensajes.js  lo traduce a "El correo o la contrasena no son correctos."
            |
            v
  Alerta.jsx   lo muestra arriba del formulario
```

**Nadie hace `fetch()` suelto en una pantalla.** Todo pasa por
`api/cliente.js`. Tres motivos: el token se agrega en un solo lugar, los
errores llegan siempre con la misma forma, y si mañana cambia la URL base se
toca un archivo.

### El contexto de autenticación

`ContextoAuth.jsx` es la pieza central del frontend. Un **contexto** de React
es una forma de compartir un dato con todos los componentes sin pasarlo como
prop de padre a hijo, nivel por nivel.

Acá el dato compartido es "quién está conectado". Desde cualquier pantalla:

```jsx
import { useAuth } from '../auth/ContextoAuth.jsx'

function MiPantalla() {
  const { usuario, salir } = useAuth()
  return <p>Hola {usuario.nombre}</p>
}
```

Expone seis cosas:

| Qué | Para qué |
|---|---|
| `usuario` | El usuario conectado (lo que devuelve `GET /usuarios/yo`), o `null` |
| `cargando` | `true` mientras se averigua si hay sesión |
| `entrar(correo, clave)` | Hace el login y deja la sesión abierta |
| `registrarse(rol, datos)` | Crea la cuenta y deja la sesión abierta |
| `salir()` | Borra el token |
| `refrescar()` | Vuelve a pedir `GET /usuarios/yo`. Se llama después de editar la cuenta (nombre, foto, tema) para que toda la app muestre lo nuevo |

Además, cada vez que cambia el usuario, el contexto escribe su tema en
`<html data-tema="claro|oscuro">`. Así funciona el modo oscuro (ver la
sección 10).

**Por qué existe `cargando`:** al recargar la página, el token está en
`sessionStorage` pero todavía no sabemos si sigue siendo válido. Hay que
preguntarle al backend con `GET /usuarios/yo`. Durante ese instante, sin
`cargando`, se vería el login parpadear antes de entrar. Por eso
`RutaProtegida` muestra "Cargando..." mientras tanto.

### Las rutas

`App.jsx` es el mapa de toda la aplicación. Las rutas **anidadas** heredan del
padre:

```jsx
<Route element={<RutaProtegida rol="estudiante" />}>   // exige sesion + rol
  <Route element={<Layout />}>                          // agrega la barra
    <Route path="/inicio" element={<Inicio />} />       // la pantalla
  </Route>
</Route>
```

Se lee de afuera hacia adentro: para ver `/inicio` hay que tener sesión, ser
estudiante, y la pantalla va a salir con la barra de navegación arriba.

`<Outlet />` es el agujero donde el padre dibuja al hijo. Está en
`RutaProtegida.jsx` y en `Layout.jsx`.

| URL | Pantalla | Mockup | Estado |
|---|---|---|---|
| `/login` | Login | 0 | Hecha |
| `/registro` | Registro | — | Hecha |
| `/recuperar` | Recuperar contraseña | — | Hecha |
| `/inicio` | Inicio del estudiante | 1a | **Hecha**, P2 |
| `/buscar` | Buscar profes | 1c | **Hecha**, P2: filtros, mapa y resultados reales |
| `/profesor/:id` | Detalle del profesor | 1f | **Hecha**, P2; espera horarios y reseñas de P3 |
| `/checkout` | Checkout | 1g | **Hecha**, P4 |
| `/mis-clases` | Mis clases | 1b | Pendiente, P3 |
| `/resenas/redactar/:destinatarioId` | Redactar o editar una reseña | Flujo de 1b y 1i | Pendiente, P3 |
| `/mi-perfil` | Perfil del estudiante | 1e | **Hecha**, P1 (y "Medios de pago", P4) |
| `/panel` | Panel del profesor | 1d | **Hecha**, P4 |
| `/agenda` | Agenda del profesor | 1i | Pendiente, P3 |
| `/perfil-profesor` | Perfil del profesor | 1j | **Hecha**, P1 |
| `/mensajes` | Mensajes | 1h | Pendiente, P3 |

Las pendientes ya están enrutadas y muestran un cartel de `EnConstruccion`. Se
puede navegar por toda la app desde el día uno sin que se rompa nada.

La pantalla de redactar reseña no es una pestaña del menú. Se abre desde el
botón **Calificar** de “Reseñas pendientes” en 1b o desde la persona equivalente
en 1i. El parámetro `destinatarioId` siempre es el `usuario.id` de la persona
calificada, nunca el id de una clase ni el de un perfil.

### Cómo agregar una pantalla nueva

Cinco pasos. Tomemos "Buscar profes" (1c) como ejemplo:

**1.** Crear `src/api/busqueda.js` con una función por endpoint:

```js
import { pedir } from './cliente.js'

export function buscarProfesores(filtros) {
  const params = new URLSearchParams(filtros)
  return pedir(`/api/busqueda/profesores?${params}`)
}
```

**2.** Crear `src/paginas/BuscarProfes.jsx`:

```jsx
import { useEffect, useState } from 'react'
import { buscarProfesores } from '../api/busqueda.js'

export default function BuscarProfes() {
  const [resultados, setResultados] = useState([])
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    buscarProfesores({ materia: 3 })
      .then((r) => setResultados(r.resultados))
      .finally(() => setCargando(false))
  }, [])

  if (cargando) return <p className="text-muted">Cargando...</p>

  return (
    <div>
      {resultados.map((p) => (
        <div key={p.id} className="card">{p.nombre}</div>
      ))}
    </div>
  )
}
```

**3.** Importarla en `App.jsx` y reemplazar el `<EnConstruccion />` de esa ruta.

**4.** Usar las clases del sistema de diseño (`card`, `btn`, `input`, `tag`),
no escribir CSS nuevo salvo que sea algo muy específico de esa pantalla.

**5.** Si hace falta CSS propio, un archivo en `src/estilos/` que use las
variables de `tokens.css`, nunca colores sueltos.

**Dos cosas que siempre se olvidan:**

- El `key` en las listas. React lo necesita para saber qué fila cambió cuando
  la lista se reordena. Usá el `id` del backend, nunca el índice del array.
- El `.finally()` para apagar el `cargando`. Si lo ponés dentro del `.then()`,
  cuando la llamada falle la pantalla queda cargando para siempre.

---

## 6. Login y registro, paso a paso

La spec las marcaba como "sin pantalla en el prototipo", así que se diseñaron
siguiendo el mismo sistema visual que el resto. Después apareció la pantalla
**"0 Ingreso"** en el mockup (`docs/Exonero Demo.html`), y el login se alineó
con ella: los mismos textos y el recuadro de usuarios de prueba. El registro y
recuperar la contraseña siguen sin pantalla en el mockup.

### El layout

Las tres pantallas de autenticación comparten `MarcoAuth.jsx`:

```
┌───────────────────────────┬───────────────────────────┐
│                           │                           │
│  Panel terracota          │  Fondo crema              │
│                           │                           │
│  Exonero                  │   Ingresa a tu cuenta     │
│                           │   Entra con tu correo...  │
│                           │                           │
│                           │   Correo                  │
│                           │   [___________]           │
│                           │   Contrasena              │
│  Clases particulares      │   [________] Mostrar      │
│  con profes de tu barrio  │                           │
│                           │   [    Entrar    ]        │
│  Busca por materia y      │   Usuarios de prueba      │
│  zona, elegi un horario.. │   [Alumno] [Profe]        │
│                           │   No tenes cuenta? Crear  │
└───────────────────────────┴───────────────────────────┘
```

Debajo de 900px de ancho el panel izquierdo se esconde y queda solo el
formulario, centrado. En el celular lo que importa es entrar, no el marketing.

### Login

**Archivo:** `src/paginas/Login.jsx`

Lo que hace, en orden:

1. Si ya hay sesión, redirige al tablero (no tiene sentido mostrar el login).
2. El usuario escribe. Cada tecla actualiza el estado.
3. Al enviar: `preventDefault()` (sin esto el navegador recarga la página y se
   pierde todo), valida en el cliente, y si hay errores los muestra y corta.
4. Llama a `entrar()`, que hace `POST /api/auth/login`, guarda el token y pide
   `GET /api/usuarios/yo`.
5. Si sale bien, navega al tablero del rol. Si venía de una pantalla protegida,
   vuelve ahí (`ubicacion.state.desde`).
6. Si sale mal, muestra el error arriba.

El botón se deshabilita mientras se envía, para que no se pueda hacer doble
clic y mandar dos logins.

Abajo está el recuadro verde de **usuarios de prueba**, como en el mockup.
Sus dos botones (**Alumno** y **Profe**) completan el formulario con
`alumno1@example.com` o `profe1@example.com` y la clave `exonero123`, los
usuarios que crea `python -m app.seeds`. Es solo para probar rápido: no
entran solos, igual hay que apretar "Entrar".

### Registro

**Archivo:** `src/paginas/Registro.jsx`

La spec tiene **dos endpoints** de alta (`/auth/registro/estudiante` y
`/auth/registro/profesor`) pero **un solo cuerpo**: los mismos campos para los
dos. Por eso hay una sola pantalla con un selector arriba, y no dos
formularios.

El rol elegido decide a qué ruta se llama. Va en la **ruta** y no en el
cuerpo, así nadie puede darse de alta como profesor mandando un campo de más.

**Por qué el selector son dos tarjetas grandes y no un desplegable:** la
elección es definitiva. No hay cambio de rol, y quien quiera ser las dos cosas
se crea dos cuentas con dos correos. Una decisión que no se puede deshacer
merece verse, no esconderse en un `<select>`. Debajo del selector hay un aviso
que lo dice.

Los campos son exactamente los de `RegistroIn`
(`backend/app/modulos/cuentas/esquemas.py`):

| Campo | Obligatorio | Nota |
|---|---|---|
| Nombre, Apellido | Sí | |
| Correo | Sí | Es el usuario. No se cambia nunca |
| Contraseña | Sí | Mínimo 8, máximo 72 (el tope de bcrypt) |
| Repetir contraseña | Sí | Solo del lado del cliente; el backend no lo recibe |
| Documento | No | |
| Teléfono | No | |
| Fecha de nacimiento | No | Define si es menor de edad |

Si la fecha de nacimiento da menos de 18 años y el rol es estudiante, aparece
un aviso: después se le van a pedir los datos de un adulto responsable (eso lo
exige `PUT /perfiles/estudiante/yo`).

Los opcionales vacíos se mandan como `null`, no como `""`: el backend los
declara `str | None`.

Al terminar, el registro devuelve el token ya emitido, así que se entra directo
sin pasar por el login. Y como el perfil recién creado está vacío, se navega a
la pantalla de perfil para completarlo.

### Recuperar contraseña

**Archivo:** `src/paginas/RecuperarClave.jsx`

Dos pasos en la misma pantalla.

**Importante para probar:** no hay correo saliente (quedó fuera de alcance).
El backend **imprime el código en su consola**. Hay que ir a la terminal donde
corre `uvicorn`, copiarlo de ahí y pegarlo en el paso 2.

El paso 1 responde `200` exista o no el correo, para no revelar qué cuentas
están registradas. Por eso siempre se pasa al paso 2.

Lo que hay que saber del código (`cuentas/logica.py`):

- Vale **15 minutos** y sirve **una sola vez**.
- Al **quinto intento equivocado se anula**: sin ese tope, un script podría
  probar el millón de combinaciones de 6 dígitos en esos 15 minutos.
- Se guarda **en memoria** (un diccionario), no en una tabla. Si `uvicorn`
  se reinicia, se pierde. Con `--reload`, guardar cualquier archivo `.py`
  reinicia el servidor: si el código "no anda", pedí otro.

### Validación: por qué está en los dos lados

El backend valida porque es **el único que no se puede saltear**. Cualquiera
puede abrir la consola del navegador y mandar lo que quiera; la validación del
cliente no es una defensa.

El frontend valida para **avisarle al usuario al instante**, sin esperar el
viaje de ida y vuelta y sin que pierda lo que escribió.

Las dos validaciones dicen lo mismo a propósito. Si cambian los mínimos en
`cuentas/esquemas.py`, hay que cambiarlos también en `utiles/validaciones.js`.

### Accesibilidad

Está resuelta en los componentes, una sola vez, y sale gratis en cada
formulario:

- Cada `<label>` apunta a su input con `htmlFor` / `id`. Hacer clic en la
  etiqueta enfoca el campo.
- Los campos con error llevan `aria-invalid` y `aria-describedby`, que apunta
  al texto del error.
- El cartel de error tiene `role="alert"`: los lectores de pantalla lo leen
  apenas aparece.
- El selector de rol son `<button>` con `aria-pressed`, no `<div onClick>`.
  Funciona con teclado y se anuncia cuál está elegida.
- El foco del teclado se ve (`:focus-visible`), pero el del clic no. Es la
  diferencia entre `:focus` y `:focus-visible`.
- El botón de mostrar/ocultar contraseña tiene `tabIndex={-1}`: es una ayuda
  visual, no debería estorbar al recorrer los campos con Tab.

---

## 7. Cuentas y perfiles (P1), de punta a punta

Todo lo de P1 está hecho: los módulos `cuentas` y `perfiles`, la resolución
del token (`usuario_actual()` en `dependencias.py`) y las pantallas **1e**
(perfil del estudiante) y **1j** (perfil del profesor). El código está
comentado línea por línea; esta sección es el mapa para leerlo sin perderse.

### Probarlo en dos minutos

1. Levantá todo como dice la sección 1 y cargá los seeds.
2. En el login tocá **Alumno**, después **Entrar**, y andá a **Mi perfil**: es 1e.
3. Cerrá sesión, tocá **Profe**, **Entrar**, y **Mi perfil**: es 1j.

Para probar el backend solo, en `http://localhost:8000/docs`: hacé el
`POST /api/auth/login`, copiá el `token` de la respuesta, y en cualquier ruta
con token completá el campo `authorization` con `Bearer <el token>`.

### El backend en una imagen

Toda request de P1 recorre el mismo camino:

```
  Llega:  PUT /api/perfiles/profesor/yo/precios
          Authorization: Bearer eyJhbGci...
          { "precio_hora_presencial": 900 }
                 |
                 v
  dependencias.py   usuario_actual(): lee el token y busca al usuario  -> 401
                    solo_profesor(): ademas exige el rol              -> 403
                 |
                 v
  esquemas.py       FastAPI valida el JSON contra PreciosIn           -> 422
                 |
                 v
  rutas.py          guardar_precios(): llama a logica y hace el COMMIT
                 |
                 v
  logica.py         guardar_precios(): las reglas, y el cambio en la
                    tabla con flush (NUNCA commit)                    -> 400/409
```

**Por qué el commit va en la ruta y no en la lógica.** El registro crea la
cuenta (en `cuentas`) y el perfil (en `perfiles`). Si cada función hiciera su
propio commit y la segunda fallara, quedaría una cuenta sin perfil. Con un
solo commit al final, en la ruta, se guardan las dos cosas o ninguna. Por eso
las funciones de `logica.py` hacen como mucho `flush()`, que manda el cambio a
la base sin cerrar la transacción (sirve para que la base asigne el `id`).

### Los archivos de P1 en el backend

| Archivo | Qué hay adentro |
|---|---|
| `app/dependencias.py` | `usuario_actual()`, `solo_estudiante()`, `solo_profesor()` y los atajos `Yo`, `Estudiante`, `Profesor` que usan las rutas |
| `cuentas/logica.py` | Alta, login, recuperar clave, editar la cuenta, foto, tema, baja, y lo que leen los otros módulos (`obtener_usuario`, `datos_basicos`, `es_menor`) |
| `cuentas/rutas.py` | Los 11 endpoints de `/api/auth` y `/api/usuarios/yo` |
| `cuentas/esquemas.py` | Las formas de los JSON de entrada y salida |
| `perfiles/logica.py` | Los dos perfiles, la ficha del profesor y su edición por secciones, las fotos, publicar/pausar, y lo que leen los otros módulos |
| `perfiles/rutas.py` | Los 15 endpoints de `/api/perfiles` y `/api/profesores` |
| `perfiles/esquemas.py` | Las formas de los JSON, incluida `MiFichaOut` |

### Los endpoints de `cuentas`

| Método y ruta | Token | Qué hace | Errores propios |
|---|---|---|---|
| `POST /auth/registro/estudiante` | No | Crea la cuenta y el perfil vacío. Devuelve el token | 409 `correo_ya_registrado`, 409 `documento_ya_registrado` |
| `POST /auth/registro/profesor` | No | Igual, con la ficha en borrador | Los mismos |
| `POST /auth/login` | No | Devuelve el token | 409 `credenciales_invalidas` |
| `POST /auth/recuperar` | No | Imprime un código en la consola del backend. Responde 200 siempre | — |
| `POST /auth/restablecer` | No | Con el código, cambia la clave | 409 `codigo_invalido` |
| `GET /usuarios/yo` | Sí | El usuario, con contador de mensajes y cabecera del estudiante | — |
| `PATCH /usuarios/yo` | Sí | Nombre, apellido, documento, teléfono, nacimiento | 400 `nombre_requerido`, 400 `fecha_invalida`, 409 `documento_ya_registrado` |
| `PUT /usuarios/yo/foto` | Sí | Foto de perfil en base64 | 400 `foto_invalida`, 400 `foto_muy_grande` |
| `PUT /usuarios/yo/clave` | Sí | Cambia la clave (pide la actual) | 403 `clave_actual_incorrecta` |
| `PUT /usuarios/yo/tema` | Sí | `claro` u `oscuro` | 422 si es otra cosa |
| `DELETE /usuarios/yo` | Sí | Baja lógica. Si es profesor, pausa su ficha | — |

Todas las rutas con token pueden responder además 401 `sin_token`.

### Los endpoints de `perfiles`

| Método y ruta | Rol | Qué hace | Errores propios |
|---|---|---|---|
| `GET /perfiles/estudiante/yo` | Estudiante | Etapa, nivel, centro, barrio, dirección, adulto | — |
| `PUT /perfiles/estudiante/yo` | Estudiante | Guarda todo eso | 400 `<catalogo>_no_existe`, 400 `adulto_responsable_requerido` |
| `GET /perfiles/profesor/yo` | Profesor | La ficha propia completa (`MiFichaOut`), aunque esté en borrador | — |
| `PATCH /perfiles/profesor/yo/personal` | Profesor | Título, años de experiencia, barrio base | 400 `barrio_no_existe` |
| `PUT /perfiles/profesor/yo/oferta` | Profesor | Materias, etapas con programa, idiomas | 400 `materia_no_existe`, ... |
| `PUT /perfiles/profesor/yo/modalidad` | Profesor | Modalidad, lugar, dirección, zonas, traslado | 400 `barrio_no_existe` |
| `PUT /perfiles/profesor/yo/precios` | Profesor | Precio presencial y online | 422 si es negativo |
| `PUT /perfiles/profesor/yo/reglas` | Profesor | Duraciones, descanso, tope, aviso, formato, cupos | 400 `duraciones_incoherentes`, `duracion_fuera_de_rango`, `cupos_incoherentes` |
| `PUT /perfiles/profesor/yo/bio` | Profesor | Titular, biografía (600), puntos de método | 422 si pasa de 600 |
| `POST /perfiles/profesor/yo/fotos` | Profesor | Agrega una foto. Devuelve `{ id }` | 400 `foto_invalida`, 409 `maximo_fotos` |
| `PUT /perfiles/profesor/yo/fotos/{id}` | Profesor | Epígrafe, orden, portada | 404 `foto_no_existe`, 403 `no_es_tuyo` |
| `DELETE /perfiles/profesor/yo/fotos/{id}` | Profesor | Borra la foto | Los mismos |
| `PUT /perfiles/profesor/yo/estado` | Profesor | `borrador`, `publicada` o `pausada` | 400 `ficha_incompleta` |
| `GET /profesores/resumen?ids=1,2` | — | Versión liviana en lote, en el orden pedido | 400 `ids_invalidos` |
| `GET /profesores/{id}` | — | La ficha pública. Solo si está publicada | 404 `profesor_no_existe` |

"Rol" quiere decir que, además del token, exige ese rol: con el otro rol la
respuesta es 403 `no_es_tuyo`.

### Lo que P1 le ofrece a los otros módulos

Estas son las funciones de `logica.py` que los demás pueden llamar (nunca los
modelos). Están implementadas y probadas:

| Función | La usa | Devuelve |
|---|---|---|
| `cuentas.obtener_usuario(db, id)` | Todos | El `Usuario`, o `None` |
| `cuentas.datos_basicos(db, id)` | mensajería, clases, reseñas | `{id, nombre, apellido, foto_base64, rol}` |
| `cuentas.es_menor(db, id)` | perfiles | `True` si tiene menos de 18 |
| `perfiles.perfil_profesor_de(db, usuario_id)` | agenda | El `PerfilProfesor` (ojo: recibe el id del **usuario**) |
| `perfiles.reglas_profesor(db, perfil_id)` | agenda | Duraciones, descanso, tope y aviso (ojo: recibe el id del **perfil**) |
| `perfiles.precio_vigente(db, usuario_id, modalidad)` | clases | El precio por hora, o `None` si no da esa modalidad |
| `perfiles.ficha_resumida(db, ids)` | búsqueda | La lista liviana, en el mismo orden de `ids` |
| `perfiles.escribir_puntaje(db, usuario_id, promedio, cantidad)` | reseñas | Nada: guarda el puntaje en el perfil que corresponda |

**Los dos ids del profesor.** Un profesor tiene `usuario.id` (la persona: lo
usan las clases, los hilos, las reseñas y la URL `/profesores/12`) y
`perfil_profesor.id` (su ficha: de ahí cuelgan las tablas de la oferta y de
la agenda). Confundirlos es el error más fácil de cometer en todo el sistema.

### Lo que P1 necesita de otros, y cómo anda mientras no está

Se decidió **no tocar los módulos de los demás**. Lo que P1 necesita de ellos
está hecho para tolerar que todavía no exista:

| Qué | De quién | Mientras no está |
|---|---|---|
| `mensajeria.contar_no_leidos()` | P3 | `GET /usuarios/yo` responde `mensajes_no_leidos: 0` (ver `_contar_no_leidos` en `cuentas/rutas.py`). Sin esto, nadie podría entrar a la app |
| `GET /api/catalogos/todo` | P2 | 1e y 1j muestran un aviso, y los desplegables de barrio, centro, etapa, materias e idiomas quedan con el valor actual y deshabilitados. El resto se puede editar |
| Saber si el profesor tiene franjas de disponibilidad | P3 | Para publicar se exige materia y precio, pero todavía no franjas. El lugar del chequeo está marcado en `perfiles/logica.py` (`cambiar_estado_ficha`) |
| Tarjetas guardadas | P4 | **Ya está**: P4 hizo la pestaña "Medios de pago" de 1e (sección 9) |
| Reseñas recibidas | P3 | La pestaña "Mis reseñas" de 1e muestra "pendiente, le toca a P3" |

Cuando cada uno termine su parte, lo de P1 empieza a usarla **sin cambiar nada**:
el `try/except NotImplementedError` deja de activarse solo, y los
desplegables se habilitan apenas `GET /api/catalogos/todo` responda.

### Decisiones que conviene conocer

**Los nombres de los catálogos se leen por nombre de tabla.** La ficha muestra
"Matemática" y "Cordón", pero las tablas de perfiles solo tienen ids. Como no
se puede importar `catalogos/modelos.py`, en `perfiles/logica.py` las tablas
de catálogos se describen a mano, con solo `id` y `nombre`, igual que las
claves foráneas: `table("materia", column("id"), column("nombre"))`. Solo para
leer. Con eso también se valida que un id exista (`_validar_catalogo`).

**Una ficha, dos esquemas.** `ficha_completa()` arma un solo diccionario con
todo, lo público y lo privado. `GET /profesores/{id}` lo devuelve con
`FichaProfesorOut`, y Pydantic descarta solo los campos privados (descanso,
tope diario, estado de la ficha). `GET /perfiles/profesor/yo` usa
`MiFichaOut`, que hereda de la otra y los deja todos. Lo privado nunca sale
en la ficha pública, y hay una sola función que mantener.

**`MiFichaOut` trae ids además de nombres.** La ficha pública dice
`"idiomas": ["Español", "Inglés"]`, y con un nombre no se puede guardar.
Por eso la ficha propia agrega `idioma_ids`, `zona_ids` y `barrio_id`.

**PATCH solo toca lo que viene.** `PATCH /usuarios/yo` y
`PATCH .../personal` usan `model_dump(exclude_unset=True)`: un campo que no
vino no se toca, y uno que vino en `null` se borra (por ejemplo, quitar el
teléfono). Los PUT, en cambio, reemplazan todo.

**Las listas se reemplazan enteras.** Materias, etapas, idiomas, zonas,
duraciones y puntos de método: el frontend manda la lista completa, el
backend borra las filas que había y crea las nuevas (`_reemplazar_filas`).
Más simple y predecible que calcular qué se agregó y qué se quitó.

**Las fotos van en base64 y se achican en el navegador.** Una foto de celular
pesa 3 a 5 MB. Antes de subirla, `utiles/imagenes.js` la achica (400 px la de
perfil, 1200 px las del lugar) y queda en unos 100 KB. El backend rechaza más
de unos 2 MB. Hay un tope de 4 fotos del lugar, la primera que se sube es la
portada, y solo puede haber una portada.

**El mapa usa el centro del barrio.** No hay geocodificación (pasar una
dirección a coordenadas). Cuando se elige un barrio, el frontend manda la
latitud y longitud del centro de ese barrio, que vienen en el catálogo.

**Publicar exige lo mínimo.** Al menos una materia y el precio de cada
modalidad que ofrece (si da presencial y online, los dos precios). Sin eso no
se podría cotizar una clase.

**Darse de baja no borra nada.** La cuenta queda `dada_de_baja`: no puede
entrar y su token deja de servir. Las clases, cobros y reseñas se conservan
para la otra persona. Si es profesor, su ficha pasa a pausada.

**Cambios respecto de los contratos originales.** Al implementar hubo que
ajustar algunos esquemas (todos de P1, ninguno lo consumía nadie todavía):

- `YoOut` suma `documento`, `telefono`, `fecha_nacimiento` y `creado_el`,
  para llenar el formulario de 1e/1j sin otro llamado.
- `nivel` del estudiante guarda solo el año (`"5.o"`); el frontend arma
  "5.o de Bachillerato".
- `FotoEnFicha` suma el `id`, para editar o borrar una foto.
- `MiFichaOut` es nuevo (la respuesta de `GET /perfiles/profesor/yo`).
- El barrio base pasó de `ModalidadIn` a `PersonalProfesorIn`, porque en el
  mockup está en "Información personal".
- `PUT .../fotos/{id}` usa `EditarFotoIn`, sin la imagen: para cambiar un
  epígrafe no hace falta volver a mandar cientos de KB.
- `ReglasIn` suma formato y cupos; `TemaIn` usa el enum `Tema`.

### El frontend: cómo están armadas 1e y 1j

Las dos pantallas tienen el mismo esqueleto, el del mockup:

```
  PerfilEstudiante.jsx / PerfilProfesor.jsx   carga los datos, guarda la
  |                                           pestania elegida
  +-- MenuLateral         las pestanias, modo oscuro, cerrar sesion
  |                       (en 1j, ademas: % completo y publicar/pausar)
  +-- CabeceraPerfil      la tarjeta verde: foto, nombre, etiquetas,
  |                       boton "Cambiar foto"
  +-- la seccion de la pestania elegida (una sola a la vez)
```

Las piezas están en `src/paginas/perfil/`:

| Archivo | Qué es | Lo usa |
|---|---|---|
| `MenuLateral.jsx` | El menú de la izquierda | 1e y 1j |
| `CabeceraPerfil.jsx` | La tarjeta verde con la foto | 1e y 1j |
| `SeccionClave.jsx` | Cambiar la contraseña y darse de baja | 1e y 1j |
| `SeccionPersonalEstudiante.jsx` | "Información personal" del estudiante | 1e |
| `SeccionDatosProfesor.jsx` | "Información personal" del profesor | 1j |
| `SeccionEnsena.jsx` | "Materias y modalidad": la más larga | 1j |
| `SeccionBio.jsx` | Titular, biografía y "cómo es una clase conmigo" | 1j |
| `SeccionFotos.jsx` | Las cuatro fotos del lugar | 1j |
| `opciones.js` | Las listas fijas de los desplegables y el plan B sin catálogos | Las secciones |

La pantalla guarda los datos (el perfil o la ficha) y se los pasa a la sección
por props. Cuando la sección guarda, llama a `alGuardar()`, que es una
función de la pantalla que vuelve a pedir los datos: así el "% completo" y la
cabecera se actualizan solos.

### Qué llamadas hace cada botón de guardar

| Dónde | Botón | Llamadas, en este orden |
|---|---|---|
| 1e Información personal | Guardar cambios | `PATCH /usuarios/yo` y después `PUT /perfiles/estudiante/yo` |
| 1j Información personal | Guardar cambios | `PATCH /usuarios/yo` y después `PATCH .../personal` |
| 1j Materias y modalidad | Guardar cambios | `PUT .../oferta`, `.../modalidad`, `.../precios`, `.../reglas` |
| 1j Biografía | Guardar cambios | `PUT .../bio` |
| 1j Fotos | (subir, portada, quitar) | Al instante: `POST`, `PUT` o `DELETE .../fotos` |
| 1j Fotos | Guardar epígrafes | Un `PUT .../fotos/{id}` por cada foto que cambió |
| Las dos | Guardar contraseña | `PUT /usuarios/yo/clave` |
| Las dos | Modo claro/oscuro | `PUT /usuarios/yo/tema` |
| Las dos | Cambiar foto | `PUT /usuarios/yo/foto` |

**Por qué el orden importa en 1e:** el backend decide si el adulto
responsable es obligatorio mirando la fecha de nacimiento. Si se guardara el
perfil antes que la cuenta, miraría la fecha vieja.

Cuando un botón hace varias llamadas y una falla, las anteriores ya quedaron
guardadas. Se muestra el error y, al volver a guardar, se manda todo de nuevo:
como cada llamada reemplaza lo que había, repetirla no duplica nada.

### Tres recorridos que vale la pena seguir en el código

**Cambiar la foto de perfil.** `CabeceraPerfil.jsx` recibe el archivo →
`achicarImagen()` lo achica (`utiles/imagenes.js`) → `cambiarFoto()` hace el
`PUT` (`api/auth.js`) → `refrescar()` vuelve a pedir el usuario
(`ContextoAuth.jsx`). Como el usuario vive en el contexto, la foto nueva
aparece sola en la cabecera, en el menú lateral y en la barra de arriba.

**El modo oscuro.** `InterruptorTema.jsx` → `cambiarTema()` guarda el tema en
la cuenta → `refrescar()` → `ContextoAuth` ve el usuario nuevo y escribe
`<html data-tema="oscuro">` → `tokens.css` redefine los colores para ese
atributo. Como todo el CSS usa variables, toda la app cambia. Y como el tema
se guarda en la cuenta, sigue al usuario aunque entre desde otra computadora.

**Sin catálogos.** `PerfilProfesor.jsx` pide la ficha y los catálogos con
`Promise.all`; si los catálogos fallan, quedan en `null` → cada desplegable
usa `opcionesDeCatalogo()` (`opciones.js`), que en ese caso arma una sola
opción con el valor actual → los campos se deshabilitan y aparece el aviso.

### Lo del mockup que no está, y por qué

| En el mockup | Por qué no está |
|---|---|
| "Sesiones activas" y "Cerrar sesión en todos los equipos" (1e) | No hay sesiones guardadas: el token vive en el navegador y vence solo (sección 3) |
| "Enviarme un enlace por correo" | No hay correo saliente. En su lugar se explica cómo usar "Olvidé mi contraseña" del login |
| "Cuenta verificada", "Identidad verificada", "Título verificado" | No hay verificación de identidad en el modelo de datos |
| "Materias en las que buscás apoyo" (1e) | No hay tabla para eso en el perfil del estudiante |
| "Cuentas de cobro" del profesor (BROU, Mercado Pago) | El modelo no tiene cuenta bancaria del profesor: los ingresos son la suma de sus cobros |
| "Precio por alumno en grupal" y "misma etapa" | No están en el modelo, y lo grupal está fuera de la v1 |
| "Ver mi ficha pública" (1j) | La ficha pública es la pantalla 1f, que es de P2 y solo pueden abrirla los estudiantes |
| La etapa "Primaria" | Las etapas salen del catálogo, y la lista que manda no la tiene (sección 13) |
| Arrastrar fotos a cada espacio | Se elige el archivo con un clic: más simple y funciona igual con teclado |

---

## 8. Catálogos y búsqueda (P2), de punta a punta

P2 es dueño de `catalogos`, `busqueda` y las pantallas 1a, 1c y 1f. Catálogos,
los cuatro endpoints del backend y las pantallas 1c y 1f ya están
implementados. Los filtros alimentan la tabla y el mapa con datos reales; la
ficha pública consume el perfil, cotiza la reserva y queda preparada para los
horarios y reseñas que implementa P3.

### Probar el panel en dos minutos

1. Levantar PostgreSQL, backend y frontend como explica la sección 1.
2. Entrar con un estudiante.
3. Abrir `http://localhost:5173/buscar`.
4. Comprobar que materia, etapa, barrio y centro educativo tienen datos.
5. Elegir un barrio: el selector de centros debe mostrar solo los de ese
   barrio y limpiar cualquier centro elegido anteriormente.
6. Cambiar precio, modalidad o puntaje; el botón "Limpiar" debe habilitarse.
7. Pulsar "Limpiar": todos los controles deben volver a su valor inicial.
8. Elegir un barrio o centro y comprobar que el mapa se acerca a esa zona.
9. Comprobar que cambian el total, las filas y los pines con cada filtro.
10. Pulsar un pin y abrir su globo; "Ver Profesor" debe navegar a `/profesor/{id}`.

### Los archivos de P2 que participan

| Archivo | Responsabilidad |
|---|---|
| `backend/app/modulos/catalogos/modelos.py` | Tablas de materias, etapas, barrios, centros, idiomas y parámetros |
| `backend/app/modulos/catalogos/esquemas.py` | Contratos que devuelve la API de catálogos |
| `backend/app/modulos/catalogos/logica.py` | Parámetros vigentes, centroide de barrio y validación de ids |
| `backend/app/modulos/catalogos/rutas.py` | `GET /api/catalogos/todo` y las listas individuales |
| `backend/app/modulos/busqueda/esquemas.py` | Contrato de filtros, resultados y pines del mapa |
| `backend/app/modulos/busqueda/logica.py` | Consulta combinada, distancias, ranking, pines y carrusel de cercanos |
| `backend/app/modulos/busqueda/rutas.py` | Los cuatro endpoints HTTP públicos de búsqueda |
| `frontend/src/api/busqueda.js` | Serializa parámetros y llama a resultados, pines, cercanos y ranking |
| `frontend/src/paginas/BuscarProfesores.jsx` | Coordina catálogos, filtros y las dos consultas de 1c |
| `frontend/src/componentes/busqueda/MapaProfesores.jsx` | Mapa Leaflet, radio, pines y globos de profesores |
| `frontend/src/componentes/busqueda/ResultadosProfesores.jsx` | Total, tabla, vacío, error y paginación |
| `frontend/src/estilos/busqueda.css` | Diseño adaptable y panel fijo en escritorio |
| `frontend/src/paginas/PerfilPublicoProfesor.jsx` | Ficha 1f, selectores y armado del enlace al checkout |
| `frontend/src/paginas/InicioEstudiante.jsx` | Coordina la pantalla 1a: próxima clase, mapa, cercanos y ranking |
| `frontend/src/componentes/inicio/MapaInicio.jsx` | Mapa grande de 1a, ubicación del estudiante, pines y leyenda |
| `frontend/src/componentes/perfil-publico/MapaUbicacionProfesor.jsx` | Mapa pequeño de la ubicación aproximada |
| `frontend/src/api/resenas.js` | Lectura de reseñas de 1f; funcionará cuando P3 complete la ruta |
| `frontend/src/estilos/perfil-publico.css` | Diseño adaptable de la ficha pública |
| `frontend/src/componentes/CampoSelect.jsx` | Selector reutilizable que ya compartían los perfiles |
| `frontend/src/api/perfiles.js` | Contiene temporalmente `obtenerCatalogos()` |

En la ficha pública 1f, la galería usa solamente las fotos devueltas por
`ficha.fotos`. Si no hay ninguna, muestra el estado vacío "No se cargaron
fotos del lugar" en vez de simular cuatro imágenes. Los datos de prueba
incluyen una foto del espacio de `profe1@example.com` para poder comprobar el
caso con contenido; los demás profesores permiten probar el estado vacío.

`obtenerCatalogos()` está en `api/perfiles.js` porque P1 lo necesitó primero
para 1e y 1j. Cuando P2 cree `api/catalogos.js`, se mueve ahí y se actualizan
los tres imports; no se duplica la función.

### Cómo está armada la pantalla 1a

```
App.jsx
  Route /inicio, estudiante
    Layout
      InicioEstudiante.jsx
        useAuth()                         saludo y datos de cabecera
        GET /api/perfiles/estudiante/yo  coordenadas e ids de ubicación
        GET /api/clases/proxima          recordatorio o estado sin clase
        GET /api/busqueda/profesores/mapa
          MapaInicio                     pines, ubicación y leyenda
        GET /api/busqueda/cercanos       carrusel de cinco tarjetas
        GET /api/busqueda/mejor-puntuados
          podio de tres o estado sin ranking
```

Las cinco lecturas son independientes: si falla la próxima clase, el mapa y
los profesores cercanos igual se muestran. El carrusel usa primero el centro
educativo del estudiante y, si no tiene, su barrio. El ranking no inventa
resultados: el backend exige al menos cinco reseñas y, mientras P3 no las
cargue, 1a muestra el estado vacío correspondiente.

### Cómo está armada la pantalla 1c

```
App.jsx
  Route /buscar, estudiante
    Layout
      BuscarProfesores.jsx
        GET /api/catalogos/todo
        estado de carga y error
        panel de filtros
          CampoSelect: materia
          CampoSelect: etapa
          rango: precio máximo
          CampoSelect: barrio
          CampoSelect: centro educativo
          radios: modalidad
          radios: puntaje mínimo
        botón Limpiar
        GET /api/busqueda/profesores
        GET /api/busqueda/profesores/mapa
        MapaProfesores
          mapa base de OpenStreetMap
          centro del barrio o centro educativo elegido
          pines y globos
        ResultadosProfesores
          total y orden
          tabla o estado vacío/error
          paginación cuando hay más de 20
```

`BuscarProfesores.jsx` es el coordinador. Guarda el estado general y pasa a
`CampoSelect` el valor actual, la función que lo cambia y las opciones. No
hace `fetch()` directo: las llamadas HTTP pasan por las funciones de `src/api/`
y, finalmente, por `api/cliente.js`.

### Qué ocurre al entrar

```
  Usuario             BuscarProfesores            Backend
     |                       |                        |
     | abre /buscar          |                        |
     |---------------------->|                        |
     |                       | GET /catalogos/todo    |
     |                       |----------------------->|
     |                       | materias, etapas,      |
     |                       | barrios, centros...    |
     |                       |<-----------------------|
     | ve el panel           |                        |
     |<----------------------|                        |
```

Mientras espera se ve "Cargando opciones...". Si la llamada falla, se muestra
el error y no se intenta leer propiedades de un catálogo inexistente. El panel
se renderiza solamente cuando `catalogos` tiene datos.

La respuesta de `/catalogos/todo` tiene esta forma:

```json
{
  "materias": [],
  "etapas": [],
  "barrios": [],
  "centros": [],
  "idiomas": []
}
```

### Los filtros y el dato que guardan

| Control visible | Estado de React | Dato para la API |
|---|---|---|
| Materia | `materiaId` | `materia` |
| Etapa educativa | `etapaId` | `etapa` |
| Precio por hora | `precioMax` | `precio_max` |
| Barrio | `barrioId` | `barrio` |
| Centro educativo | `centroId` | `centro` |
| Modalidad | `modalidad` | `modalidad` |
| Puntaje mínimo | `puntajeMin` | `puntaje_min` |

Los ids de un `<select>` llegan como texto. Eso sirve directamente para
`URLSearchParams`; si una operación numérica los necesitara, se convierten con
`Number(...)` en ese límite y no antes.

### Barrio y centro son dependientes

Los centros traen `barrio_id`. La pantalla filtra la lista antes de convertirla
en opciones:

```jsx
catalogos.centros
  .filter((centro) => !barrioId || String(centro.barrio_id) === barrioId)
  .map((centro) => ({ valor: centro.id, texto: centro.nombre }))
```

Si no hay barrio se ven todos. Si lo hay, se ven solo sus centros. Además,
`cambiarBarrio()` limpia `centroId`; así nunca queda guardado un centro del
barrio anterior.

### El mapa y sus pines

`MapaProfesores.jsx` usa `MapContainer` y `TileLayer` de React Leaflet. Parte
del centro general de Montevideo. `BuscarProfesores.jsx` busca con `find()` el
barrio o centro seleccionado y le pasa ese objeto mediante la prop
`ubicacion`. Como ambos catálogos incluyen latitud y longitud, un componente
interno con `useMap()` llama a `flyTo()` y acerca el mapa.

El zoom con la rueda empieza desactivado en todos los mapas para que Leaflet
no interrumpa el desplazamiento vertical de la página. Con el mapa enfocado,
`Enter` lo activa o desactiva y `Escape` lo apaga. La lógica compartida vive en
`componentes/mapas/ZoomConEnter.jsx`. En el mapa pequeño del perfil, el aviso
usa una versión compacta de una sola línea y los controles de zoom están en la
esquina inferior derecha.

Con los mismos parámetros de la tabla, el frontend pide
`GET /api/busqueda/profesores/mapa`. Cada respuesta se convierte en un
`Marker` con inicial; al tocarlo abre un `Popup` con nombre, puntaje, precio y
enlace al perfil. La zona elegida se dibuja con un `Circle` de tres kilómetros.

### El backend de búsqueda

Los cuatro endpoints son públicos: una persona puede explorar profesores antes
de registrarse.

| Endpoint | Para qué sirve | Respuesta |
|---|---|---|
| `GET /api/busqueda/profesores` | Lista filtrada de 1c | Total, página y hasta 20 resultados |
| `GET /api/busqueda/profesores/mapa` | Pines de 1a, 1c y 1f | Coordenadas y datos mínimos del globo |
| `GET /api/busqueda/cercanos` | Carrusel "Profes cerca de ti" de 1a | Hasta `limite` tarjetas por distancia |
| `GET /api/busqueda/mejor-puntuados` | Podio de 1a | Tres tarjetas por defecto |

`busqueda` no tiene modelos propios. Tampoco importa `perfiles/modelos.py`: en
`logica.py` usa `table()` y `column()` para describir únicamente las columnas
externas que necesita leer. Es el mismo patrón con el que P1 lee los nombres de
los catálogos sin importar sus modelos. Nombre, apellido, foto y materias no se
reconstruyen en P2: se piden en lote a
`perfiles.logica.ficha_resumida()`. Así se conserva la frontera entre módulos y
se evita una consulta por cada profesor.

La búsqueda sigue esta secuencia:

```
query params validados por FiltrosBusqueda
          |
          v
una consulta SQL sobre fichas publicadas
  + EXISTS para materia, etapa, idioma y zona
  + modalidad, precio y puntaje
          |
          v
agenda.filtrar_con_hueco()          solo si vino día o franja
          |
          v
distancia + orden + total
          |
          v
página de 20
          |
          v
perfiles.ficha_resumida()           nombre, foto y materias en lote
          |
          v
PaginaBusqueda
```

Materia, etapa, idioma y zona usan subconsultas `EXISTS` en vez de `JOIN` en la
consulta principal. Un profesor puede tener varias filas de oferta; con un
`JOIN` mal armado aparecería repetido y el total o la paginación quedarían
incorrectos. `EXISTS` responde solamente si hay una coincidencia.

#### Precio y modalidad

Si se pide `modalidad=presencial`, el rango de precio se aplica a
`precio_hora_presencial`; con `online`, al precio online. Sin modalidad se usa
el menor precio disponible del profesor. Un perfil de modalidad `ambas`
participa tanto en búsquedas presenciales como online. `modalidad=ambas`, si se
envía explícitamente, exige que ofrezca las dos.

El rango imposible (`precio_min > precio_max`) responde 400
`rango_precio_invalido`. Los ids de catálogo inexistentes también responden
400 con códigos como `materia_no_existe` o `barrio_no_existe`; valores fuera de
rango y opciones no permitidas los rechaza Pydantic con 422 antes de entrar a
la lógica.

#### Distancia y orden

El centro educativo tiene prioridad como punto de referencia; si no hay centro
se usa el centroide del barrio. La distancia se calcula con Haversine en
kilómetros y se redondea a dos decimales. Sin una ubicación elegida,
`orden=distancia` deja las distancias en `null` y desempata por puntaje.

Los tres órdenes son estables:

- `distancia`: menor distancia, luego mayor puntaje;
- `puntaje`: mayor puntaje, luego mayor cantidad de reseñas;
- `precio`: menor precio aplicable, luego mayor puntaje.

Siempre se usa `usuario.id` en URLs y respuestas. `perfil_profesor.id` queda
adentro de las consultas para unir las tablas de oferta.

#### Pines, cercanos y ranking

El endpoint de mapa acepta los filtros normales o `ids=4,7,9`. Si vienen ids,
ignora los filtros, elimina repetidos, conserva el orden y admite hasta cien.
Solo devuelve profesores publicados con latitud y longitud.

`cercanos` necesita `barrio` o `centro_id`; sin punto de referencia devuelve
una lista vacía. Solo considera fichas con coordenadas. Si `con_hueco=true`,
agrega `primera_hora_libre` mediante agenda.

El ranking exige al menos cinco reseñas. Esto evita que una única calificación
de 5 supere a alguien con muchas reseñas y promedio 4,8. Puede limitarse a una
etapa y desempata por cantidad de reseñas.

#### La dependencia con P3

P2 ya llama a las dos funciones públicas acordadas con agenda. Mientras P3 no
implemente `primera_hora_libre()`, el campo opcional de las búsquedas básicas
sale en `null`; esto permite desarrollar P2 y P3 en paralelo. Los filtros
explícitos `dia` o `franja` sí necesitan `filtrar_con_hueco()` y quedarán
operativos cuando P3 complete esa función. No se duplicó ningún cálculo de
disponibilidad dentro de búsqueda.

### Limpiar sin duplicar estado

`limpiarFiltros()` devuelve cada control a su valor inicial. El botón se
deshabilita con `hayFiltros`, un booleano calculado a partir de los estados
existentes. No se guarda otro `useState` para eso: sería información duplicada
que podría quedar desincronizada.

### El diseño y el modo oscuro

`busqueda.css` se limita con clases como `.filtros-panel`; no cambia los
formularios de P1. Usa variables de `tokens.css`, por lo que acompaña el tema
del usuario y mantiene el panel adaptable en anchos chicos.

La composición replica `Exonero Demo.html`: columna de filtros de `264px`,
separación de `18px`, panel con `18px` de relleno y mapa de `420px` de alto.
No lleva un título introductorio sobre ambas columnas. Debajo de 900 px pasa
a una sola columna para evitar desplazamiento horizontal.

En escritorio el panel de filtros usa `position: sticky`: acompaña el
desplazamiento general de la página y queda quieto al llegar a 18 px del borde
superior, igual que los bloques laterales del perfil público. No tiene una barra
ni un desplazamiento interno propios. En la composición de una columna se
desactiva para mantener el orden natural de la página.

La paleta de la demo ahora vive en `tokens.css` y es global: fondo `#e6edf5`,
paneles `#ffffff`, texto y encabezados `#13284c`, y acento `#4d7fb3`. La
navegación usa el texto oscuro como fondo y el enlace activo usa
`--color-accent-300`. Todas las pantallas consumen las mismas variables; el
modo oscuro las redefine también de forma global.

El encabezado reutiliza el PNG del búho incrustado en la demo, guardado como
`frontend/src/assets/logo-exonero.png`. `Layout.jsx` lo coloca junto a la marca
con las medidas originales del mockup: imagen de `30 x 29px`, separación de
`9px` y texto Caprasimo de `20px`.

La lista abierta de un `<select>` la dibujan el navegador y Windows. Para que
no quede texto claro sobre fondo blanco en modo oscuro, las opciones definen
explícitamente ambos colores con variables del tema.

### Acentos en los catálogos

El frontend ya era UTF-8. Los nombres sin tildes venían de `app/seeds.py`, no
de React. Se corrigieron los datos fuente (`Matemática`, `Español`, `Cordón`,
etc.) y sus referencias internas. Una base ya sembrada conserva los textos
viejos hasta volver a ejecutar los seeds o actualizar esas filas. Ejecutar
`python -m app.seeds` vacía y reconstruye las tablas.

### Qué es real y qué falta

Precio, modalidad y puntaje existen como columnas de `perfil_profesor` y como
parámetros de `FiltrosBusqueda`. El panel ya guarda valores compatibles con
ese contrato.

El backend de P2 está completo: búsqueda, pines, cercanos, ranking, validación,
orden y paginación. Se verificó contra una base sembrada que las fichas no
publicadas quedan afuera, que los filtros SQL se combinan, que los ids del mapa
conservan el orden y que las cuatro respuestas cumplen sus esquemas Pydantic.

La integración de 1c también está completa. `api/busqueda.js` omite parámetros
vacíos; `BuscarProfesores.jsx` pide resultados y pines en paralelo después de
una espera breve; la limpieza del efecto ignora respuestas viejas. La tabla
muestra la primera página de veinte y controles de paginación solo cuando son
necesarios. El mapa usa exactamente los mismos filtros.

Lo único que depende de otro equipo son los filtros de día y franja y la
próxima hora libre: se habilitarán cuando P3 complete las funciones públicas de
agenda. No bloquean materia, etapa, ubicación, precio, modalidad ni puntaje.

---

## 9. Clases y pagos (P4), de punta a punta

Todo lo de P4 está hecho: los módulos `clases` y `pagos`, la migración que
arregla la tabla `cobro`, los seeds con el mismo cálculo de plata que el
checkout, y sus tres pantallas: el checkout **1g**, la pestaña "Medios de pago"
de **1e** y el panel del profesor **1d** (ver "El frontend de P4", más abajo).
Esta sección es el mapa, con la misma forma que la 7.

### Probarlo en dos minutos

En `http://localhost:8000/docs`, con los seeds cargados:

1. `POST /api/auth/login` con `alumno1@example.com` / `exonero123`, y pegá el
   token en el campo `authorization` (`Bearer <el token>`).
2. `POST /api/clases/cotizar` con
   `{"profesor_id": 1, "duracion_min": 60, "modalidad": "presencial"}`. Devuelve
   el desglose, con `"total": "1207.80"`. No pide token.
3. `GET /api/pagos/tarjetas` muestra la tarjeta de prueba (`"ultimos4": "1111"`).
   Con su `id`, `POST /api/clases` crea la clase en `pendiente` con el cobro
   `retenido`.
4. Entrá como `profe1@example.com`: `GET /api/clases/pendientes` muestra la
   solicitud, y `POST /api/clases/{id}/aprobar` la pasa a `aprobada` (cobro
   `cobrado`).
5. `POST /api/clases/{id}/cancelar`, con cualquiera de los dos tokens, responde
   al instante con el reembolso `en_proceso`. Un momento después el cobro ya
   está `reembolsado`: se ve en `GET /api/pagos/historial` con el token del
   alumno.

Para ver el error de pago de 1g: agregá una tarjeta terminada en `0000`
(`POST /api/pagos/tarjetas` con `"numero": "4000 0000 0000 0000"`) y reservá con
ella. Responde 402 `cobro_rechazado` y la clase no se crea.

**Las 276 comprobaciones.** `backend/verificar_p4.py` recorre todos los
endpoints de P4 con los usuarios de los seeds: los flujos de la plata de punta a
punta, los errores de cada uno (roles cruzados, ids que no existen, estados
inválidos), que los importes cuadren al centésimo, la migración de ida y vuelta
y los seeds dos veces seguidas. **Ensucia la base** (crea y cancela clases,
cambia el precio de profe4) y al final la vuelve a sembrar, así que se corre
contra una base aparte, nunca contra la de todos los días (si el `.env` apunta a
`exonero`, se niega a correr):

```bash
docker exec exonero_db psql -U exonero -d exonero -c "CREATE DATABASE exonero_p4"
# BASE_URL apuntando a la base nueva, en las dos terminales (o en el .env de
# otra copia del repo). En PowerShell: $env:BASE_URL = "..."
export BASE_URL=postgresql+psycopg://exonero:exonero@localhost:5433/exonero_p4
cd backend
python -m alembic upgrade head
python -m app.seeds
python -m uvicorn app.main:app --port 8001     # en otra terminal, con el mismo BASE_URL
python verificar_p4.py                          # "276 de 276 comprobaciones pasaron."
```

### El ciclo de vida, en una tabla

| Acción | Quién | La clase | El cobro |
|---|---|---|---|
| `POST /clases` | Alumno | Se crea en `pendiente` | `retenido` |
| `POST /clases/{id}/aprobar` | Profesor | `aprobada`: ocupa el horario | `cobrado` |
| `DELETE /clases/{id}` (rechazar) | Profesor | **Se borra** | `liberado`, con `clase_id` en NULL |
| `POST /clases/{id}/cancelar`, si estaba pendiente | Cualquiera de los dos | `cancelada` | `liberado`, en el momento |
| `POST /clases/{id}/cancelar`, si estaba aprobada | Cualquiera de los dos | `cancelada` | `reembolsado`, en segundo plano |
| `POST /clases/{id}/reprogramar` | Cualquiera de los dos | Otro horario, y vuelve a `pendiente` | No cambia |
| `POST /clases/{id}/completar` | Profesor | `dictada` o `no_asistida` | Sigue `cobrado` |

Solo una `pendiente` se aprueba o se rechaza; solo una `pendiente` o una
`aprobada` se cancela o se reprograma; solo una `aprobada` se completa. Si no,
409 `estado_invalido`.

### Los archivos de P4 en el backend

| Archivo | Qué hay adentro |
|---|---|
| `clases/logica.py` | `desglosar()` y `cotizar()`, crear y las cinco acciones, el calendario, la próxima clase, las solicitudes, las métricas y las series de 1d, y lo que leen agenda y reseñas |
| `clases/rutas.py` | Los 14 endpoints de `/api/clases` |
| `clases/esquemas.py` | Los contratos. `ClaseOut` suma `etapa` |
| `pagos/logica.py` | Las cuatro transiciones del cobro, el reembolso en segundo plano, tarjetas, historial e ingresos |
| `pagos/rutas.py` | Los 5 endpoints de `/api/pagos` |
| `pagos/modelos.py` | `cobro.clase_id` ahora admite NULL (ver abajo) |
| `app/fechas.py` | La zona de Montevideo: rangos de días, los períodos de 1d, las ventanas de los gráficos y el `date_trunc` |
| `alembic/versions/6d0c95b67436_cobro_sobrevive_al_rechazo.py` | La migración de `cobro` |
| `verificar_p4.py` | Las 276 comprobaciones |

### Los endpoints de `clases`

| Método y ruta | Rol | Qué hace | Errores propios |
|---|---|---|---|
| `POST /clases/cotizar` | — (sin token) | El desglose del importe. 1f y 1g | 400 `modalidad_invalida`, 404 `profesor_no_existe`, 400 `duracion_invalida`, 400 `sin_precio` |
| `GET /clases/proxima` | Los dos | La siguiente aprobada, con `minutos_restantes`. **204 sin cuerpo** si no hay | — |
| `GET /clases/pendientes` | Profesor | Las solicitudes por aprobar (1i) | — |
| `GET /clases/metricas?periodo=mes` | Profesor | Los indicadores de 1d con su variación | 400 `periodo_invalido` |
| `GET /clases/series?agrupar=semana` | Profesor | El gráfico de 1d: clases por tramo y por estado | 400 `agrupacion_invalida` |
| `GET /clases/mis-profesores` | Estudiante | Profesores con alguna clase dictada, con `mi_resena` (1b) | — |
| `GET /clases/mis-alumnos` | Profesor | Lo mismo, del otro lado (1i) | — |
| `GET /clases?desde=&hasta=&estado=&pagina=` | Los dos | El calendario, de a 50, por inicio | 400 `estado_no_permitido` |
| `POST /clases` | Estudiante | Crea la clase y retiene el cobro (1g). 201 | Los de cotizar, 400 `materia_no_existe`, 400 `etapa_educativa_no_existe`, 409 `horario_ocupado`, 404 `tarjeta_no_existe`, 402 `tarjeta_vencida`, 402 `cobro_rechazado` |
| `POST /clases/{id}/aprobar` | Profesor | Pendiente → aprobada; cobro → cobrado | 409 `horario_ocupado` |
| `DELETE /clases/{id}` | Profesor | Rechaza: borra la clase y libera el cobro. 204 | — |
| `POST /clases/{id}/cancelar` | Los dos | Pendiente o aprobada → cancelada, con el reembolso | — |
| `POST /clases/{id}/reprogramar` | Los dos | Otro horario; vuelve a pendiente | 400 `duracion_no_modificable`, 409 `horario_ocupado` |
| `POST /clases/{id}/completar` | Profesor | Aprobada → dictada o no_asistida | 400 `estado_no_permitido` |

Las cinco rutas con `{id}` responden además 404 `clase_no_existe`, 403
`no_es_tuyo` (no es parte de la clase) y 409 `estado_invalido` (la clase no
está en el estado que la acción necesita).

### Los endpoints de `pagos`

| Método y ruta | Rol | Qué hace | Errores propios |
|---|---|---|---|
| `GET /pagos/tarjetas` | Estudiante | Las tarjetas activas. **Nunca** el número completo ni el CCV | — |
| `POST /pagos/tarjetas` | Estudiante | Alta. Acepta el número con espacios. 201 | 400 `tarjeta_invalida`, 402 `tarjeta_vencida` |
| `DELETE /pagos/tarjetas/{id}` | Estudiante | Baja lógica. 204 | 404 `tarjeta_no_existe`, 403 `no_es_tuyo` |
| `GET /pagos/historial?desde=&hasta=&pagina=` | Estudiante | Los movimientos de plata, del más nuevo al más viejo (1e) | — |
| `GET /pagos/ingresos?periodo=&agrupar=` | Profesor | Cobrado, pendiente, promedio y la serie del gráfico (1d y 1j) | 400 `periodo_invalido`, 400 `agrupacion_invalida` |

Como en la sección 7: "Rol" quiere decir que con el otro rol la respuesta es
403 `no_es_tuyo`, y toda ruta con token puede responder 401 `sin_token`.

Los importes viajan como **texto** (`"1758.26"`): Pydantic serializa `Decimal`
así para no perder centésimos. Las fechas, en ISO con zona.

### Lo que P4 le ofrece a los otros módulos

| Función | La usa | Devuelve |
|---|---|---|
| `clases.clases_entre(db, usuario_id, desde, hasta, estado=None, pagina=None)` | agenda (el calendario semanal de 1i) | Filas con la forma de `ClaseOut`, por inicio. Sin `pagina`, todas |
| `clases.clases_aprobadas_entre(db, profesor_id, desde, hasta)` | agenda (los huecos libres) | `[{id, inicio, fin, duracion_min, estudiante_id}]` de las **aprobadas** que se cruzan con el rango |
| `clases.tuvieron_clase(db, a_id, b_id)` | reseñas | `True` si hay al menos una clase **dictada** entre los dos, en cualquier sentido |
| `clases.desglosar(precio_hora, duracion_min, costo_traslado, pct_comision, pct_iva)` | seeds | El desglose del importe: el único cálculo de plata del sistema |

Todas reciben ids de **usuario** (no de perfil) e instantes con zona.

### Lo que P4 necesita de otros, y cómo anda mientras no está

| Qué | De quién | Mientras no está |
|---|---|---|
| `agenda.verificar()` | P3 | Crear y reprogramar siguen como si el horario estuviera libre (`_horario_libre` en `clases/logica.py`). No es un agujero: la defensa real es la restricción `EXCLUDE`, que salta al aprobar. Lo que se pierde es el aviso temprano (franjas, bloqueos, aviso mínimo, tope diario) |
| `agenda.hay_bloqueo_encima()` | P3 | Aprobar sigue como si no hubiera bloqueos (`_hay_bloqueo`) |
| `resenas.resena_de()` | P3 | `mi_resena` viene en `null` en mis-profesores y mis-alumnos (`_mis_resenas`) |

Es el mismo truco que usa P1 con `mensajeria.contar_no_leidos()`: un
`try/except NotImplementedError`. Cuando P3 las implemente, P4 las empieza a usar
**sin cambiar nada**.

De P1 hacían falta cinco funciones que no existían. Se **agregaron**, en el
mismo estilo, y ninguna de las que había cambió:

| Función | Para qué |
|---|---|
| `perfiles.condiciones_de_reserva(db, usuario_id)` | Si la ficha está publicada, su modalidad, si se traslada, cuánto cobra por ir y la dirección de su espacio: lo que cotizar necesita además del precio |
| `perfiles.direccion_estudiante(db, usuario_id)` | La ubicación de la clase cuando el profesor va a la casa del alumno |
| `perfiles.cabeceras_estudiantes(db, ids)` | `cabecera_estudiante()` en lote, para la contraparte |
| `perfiles.sumar_clase_dictada(db, usuario_id)` | `clases_dictadas + 1` al completar (P4 no puede tocar esa tabla) |
| `cuentas.telefonos_varios(db, ids)` | El teléfono de varios alumnos en una consulta: 1d lo muestra, y `datos_basicos` no lo trae |

### Decisiones que conviene conocer

**La migración de `cobro`, y por qué.** La migración inicial dejó
`cobro.clase_id` como `NOT NULL ... ON DELETE CASCADE`. Pero al **rechazar**, la
clase se borra y el cobro liberado tiene que quedar registrado (es justamente el
motivo de que la plata viva en su propia tabla, ver la sección 4): con el
`CASCADE`, borrar la clase se llevaba puesto el cobro. La segunda migración
(`6d0c95b67436`) la deja **nullable con `ON DELETE SET NULL`**: la clase
rechazada desaparece y su cobro queda con `clase_id` en NULL. El `UNIQUE` sigue
valiendo, porque PostgreSQL permite varios NULL. El `downgrade` está escrito a
mano: borra antes los cobros sin clase, porque el esquema viejo no tiene forma
de guardarlos. `pagos/modelos.py` y `schema.sql` están al día, y
`alembic check` no encuentra diferencias.

**Un solo cálculo de plata.** `desglosar()` hace las cuentas y nada más (no toca
la base); la usan `cotizar()`, `crear()` (que llama a `cotizar()`) y los seeds.
Todo con `Decimal`, redondeando a dos decimales con `ROUND_HALF_UP` en cada paso,
en el orden del docstring: subtotal, comisión sobre subtotal más traslado, IVA
sobre todo lo anterior. Dos detalles:

- El subtotal sale de los **minutos** (`precio * minutos / 60`), no de las horas
  ya redondeadas: 50 minutos son 0,8333 horas, y con 0,83 una clase de $ 900 la
  hora saldría $ 747 en vez de $ 750. `horas` se informa solo para mostrar.
- Con un precio de 873,45 y 90 minutos: subtotal 1310,175 → 1310,18; comisión
  131,018 → 131,02; IVA 317,064 → 317,06; total **1758,26**. Es el caso con
  decimales que prueba `verificar_p4.py`, contra una cuenta hecha aparte.

Los seeds ya no tienen su propio `_desglose()`: usan `desglosar()`, y sus treinta
clases dan los mismos totales que antes.

**Qué valida cotizar, en orden.** Modalidad `presencial` u `online` (400
`modalidad_invalida`; una clase concreta no puede ser "ambas"); que el profesor
exista y tenga la ficha **publicada** (404 `profesor_no_existe`: la pausada o en
borrador no se puede contratar); que la duración sea una de las que ofrece
(400 `duracion_invalida`); que dé esa modalidad y tenga precio (400
`sin_precio`).

**El traslado.** Se cobra solo en presencial, si el alumno lo pide
(`con_traslado`) y si el profesor se traslada (lugar `a_domicilio` o `ambos`). Si
no, se ignora: no es un error. La ubicación que se guarda en la clase es la
dirección del alumno si el profesor va (o si solo da clases a domicilio), la del
espacio del profesor si no, y un enlace simulado
(`https://meet.exonero.test/clase-<id>`) si es online, igual que en los seeds.

**Crear es una sola transacción.** La clase se inserta, se hace `flush` para
tener su id, y `pagos.retener()` crea el cobro. Si la tarjeta falla, el error
corta antes del commit (que está en la ruta) y la sesión se cierra con rollback:
no queda ni la clase ni el cobro. La tarjeta tiene que ser del alumno y estar
activa; si es de otro, también 404 `tarjeta_no_existe` (no hace falta confirmarle
que existe).

**Dos controles propios, mientras agenda no está.** Un horario que **ya pasó**
nunca está libre: sin agenda nada impediría reservar ayer (cuando P3 implemente
`verificar()` lo rechaza igual, por el aviso mínimo). Y el **mismo alumno** no
puede pedirle dos veces un rato que se cruza al mismo profesor: es un doble clic
en confirmar, y dejaría dos cobros retenidos. Los dos responden 409
`horario_ocupado`. Alumnos distintos sí pueden pedir el mismo horario: el
profesor elige cuál aprueba.

**El cobro simulado y su gancho.** `retener()` siempre sale bien, salvo con una
tarjeta **terminada en `0000`** (402 `cobro_rechazado`) o vencida (402
`tarjeta_vencida`). Es la forma de probar el error de 1g sin tocar código.

**Aprobar: la restricción `EXCLUDE` hace el trabajo.** El `UPDATE` a `aprobada`
va dentro de un `SAVEPOINT` (`db.begin_nested()`). Si ya hay otra aprobada del
mismo profesor que se cruza, PostgreSQL rechaza el `UPDATE` con la restricción
`clase_sin_superposicion`; se atrapa ese `IntegrityError` (solo ese: se mira el
nombre de la restricción) y se responde 409 `horario_ocupado`. El `SAVEPOINT`
deshace solo ese `UPDATE` y deja la sesión sana para responder. Dos pendientes
sobre el mismo horario son legítimas; la segunda que se intenta aprobar es la que
choca.

**Las acciones leen la clase con `FOR UPDATE`.** Si el profesor aprueba y el
alumno cancela en el mismo instante, la segunda espera a que termine la primera y
ve el estado nuevo (y responde 409 `estado_invalido`), en vez de pisarlo.

**Rechazar libera antes de borrar.** Después del `DELETE` ya no habría cómo
encontrar el cobro por la clase. El historial del alumno filtra por
`tarjeta.usuario_id` (la tarjeta es suya, `retener` siempre la guarda y su baja es
lógica) con un `LEFT JOIN` a `clase`: así aparecen también los cobros liberados de
las rechazadas, con `clase_id`, `materia` y `contraparte` en `null`. El frontend
los muestra como "Solicitud rechazada".

**Cancelar: liberado o en proceso.** La decisión la toma el estado del cobro, no
el de la clase. Si estaba `retenido` (la clase todavía pendiente), se **libera en
el momento** y `reembolso.estado` es `"liberado"`. Si estaba `cobrado` (ya
aprobada), se encola `pagos.reembolsar()` como `BackgroundTask` y la respuesta
vuelve al instante con `"en_proceso"`. La tarea corre después del commit de la
ruta, abre su propia `SesionLocal()`, bloquea la fila con `FOR UPDATE`, es
idempotente (si el cobro ya está reembolsado no hace nada) y cierra la sesión
siempre, en un `finally`. El importe es **el total, siempre** (ver la sección
13.2).

**Reprogramar.** Cualquiera de las dos partes, sobre una pendiente o una
aprobada. La clase vuelve a `pendiente` y el profesor la tiene que aprobar de
nuevo; los importes **no** se recalculan (es la misma clase movida de lugar). Por
eso no se puede cambiar la duración: si viene una distinta, 400
`duracion_no_modificable`. Si estaba aprobada, el cobro queda `cobrado`, y por eso
`cobrar()` no hace nada si ya está cobrado: así se puede volver a aprobar sin
cobrar dos veces. Antes de preguntarle a agenda si el horario nuevo está libre,
la clase pasa a pendiente con un `flush`: si no, su propio horario viejo contaría
como ocupado y moverla media hora chocaría consigo misma.

Un caso borde: el profesor **rechaza** la reprogramación de una clase que ya
estaba cobrada. No hay retención que soltar: la plata se cobró y hay que
devolverla. `liberar()` la marca `reembolsado` en el momento (no en segundo
plano, porque la clase se borra enseguida y la tarea no tendría por dónde
encontrar el cobro).

**Completar.** Solo el profesor y solo una aprobada. `dictada` suma uno a
`clases_dictadas` (con `perfiles.sumar_clase_dictada()`, un
`UPDATE ... SET x = x + 1` para que dos a la vez no pierdan una suma) y desde ahí
`tuvieron_clase()` da `True`: el alumno ya puede reseñar. En `no_asistida` no se
suma nada. En los dos casos el cobro queda `cobrado`.

**Las fechas son de Montevideo.** La base guarda `timestamptz` (UTC por dentro),
pero "el 21 de octubre", "la semana" o "el mes" son de acá: una clase a las 23:30
de Montevideo ya es el día siguiente en UTC. Todo eso está en `app/fechas.py`, que
usan `clases` y `pagos` (está afuera de los dos porque `clases` ya importa `pagos`,
y al revés sería una importación circular):

- `?desde=` y `?hasta=` son fechas sin hora, de Montevideo, y **`hasta` es
  inclusive**: el rango es `[desde 00:00, hasta + 1 día 00:00)`.
- Un `inicio` que llega sin zona se interpreta en Montevideo.
- Los períodos de las métricas son **calendario**: el mes en curso contra el
  anterior, el trimestre en curso contra el anterior, el año contra el pasado.
- Las ventanas de los gráficos son las últimas 10 semanas, 12 meses o 5 años,
  **incluido el actual**, enteros.
- Se agrupa con `date_trunc` sobre la hora de Montevideo. La unidad y la zona van
  como texto literal en el SQL y no como parámetros: con parámetros, el `SELECT`
  dice `date_trunc($1, ...)` y el `GROUP BY` `date_trunc($3, ...)`, y PostgreSQL no
  los reconoce como la misma expresión.

**Las métricas de 1d.** Las clases caen en un período por su `inicio`.
`alumnos_atendidos` son los alumnos distintos con alguna clase dictada;
`horas_dictadas`, la suma de las duraciones dictadas; `alumnos_recurrentes`, los
que tuvieron dos o más dictadas; `tasa_cancelacion`, canceladas sobre canceladas
más dictadas, en porcentaje (0 a 100) con un decimal. `variacion` trae el cambio
de cada uno contra el período anterior, en porcentaje con un decimal, o `null` si
el anterior fue 0.

**Los ingresos.** `cobrado` es la suma de los cobros en estado `cobrado` del
profesor, por la fecha en que se cobraron (`cobrado_el`); un reembolsado deja de
contar solo, sin "descontar" nada. `pendiente` es lo retenido en el período (lo
que espera que apruebe). `promedio_por_clase` es cobrado sobre las clases dictadas
del período, o 0. `serie` es lo cobrado por tramo, con la misma ventana y la misma
agrupación que `/clases/series`. Los tramos sin nada no vienen en ninguna de las
dos series: el frontend los completa.

**La contraparte, en lote.** Cada fila del calendario trae a la otra persona: si
mira el profesor, el alumno con etapa, centro, teléfono y puntaje; si mira el
alumno, el profesor con su puntaje y cantidad de reseñas. `armar_clases()` pide
los nombres de materia y etapa, el estado de los cobros y las personas **todos
juntos**, no uno por fila: con 50 clases son unas ocho consultas, no 300.

**Las tablas ajenas, "de lejos".** Igual que perfiles con los catálogos (sección
7): `clases` lee los nombres de materia y etapa, y `pagos` lee la `clase` y la
`materia` del historial y los ingresos, describiendo esas tablas a mano por su
nombre con `table()` y `column()`, solo para leer. `pagos` no puede importar
`clases/logica.py`, porque `clases` ya importa `pagos`.

**Tarjetas.** El número se guarda sin espacios; `GET` y `POST` devuelven solo la
marca (empieza con 4 → Visa, con 5 → Mastercard, el resto → Otra), los últimos
cuatro, el titular y el vencimiento como `"MM/AA"`. Una tarjeta vale hasta el
último día de su mes. El año va con cuatro cifras: con `28`, 400
`tarjeta_invalida`. La baja es lógica: los cobros viejos siguen apuntando a la
fila.

### Cambios respecto de los contratos originales

Al implementar hubo que ajustar algunos contratos. Los que consume el frontend
están marcados:

- **`ClaseOut` suma `etapa`** (y por herencia `ProximaClaseOut`): el nombre de la
  etapa **de la clase**, que la tabla "Reservas de hoy" de 1d muestra como
  "Matemática · Bachillerato". *(frontend)*
- **`MovimientoOut.clase_id` puede venir en `null`**, igual que `materia` y
  `contraparte`: son los cobros de las clases rechazadas. `fecha` es la del
  último movimiento del cobro. *(frontend)*
- **`MetricasOut.variacion`** es `{indicador: número | null}`: los porcentajes
  van como número, no como texto, porque no son plata. *(frontend)*
- `IngresosOut.serie` quedó tipada (`PuntoIngreso`: `etiqueta` e `importe`),
  con la misma forma que antes.
- `ReprogramarIn.duracion_min` sigue siendo opcional, pero si viene tiene que
  ser la de la clase.
- `pagos.retener()` recibe además el `estudiante_id` (para validar que la
  tarjeta sea suya); `pagos.ingresos_de()`, la agrupación de la serie;
  `clases.clases_entre()`, la página; `clases.reprogramar()`, la duración.
- Funciones públicas nuevas: en `pagos`, `cobro_de()` y `estados_de_cobro()`
  (para que `clases` sepa en qué anda la plata sin leer la tabla) y las de
  tarjetas, historial e ingresos; en `clases`, `desglosar()`,
  `importes_congelados()`, `armar_clases()` y las de cada pantalla.
- **Códigos de error nuevos**, ya con su texto en `mensajes.js`:
  400 `periodo_invalido`, 400 `agrupacion_invalida`, 400 `estado_no_permitido`
  (un estado que no corresponde, en el filtro de `/clases` o al completar),
  400 `duracion_no_modificable` y 404 `cobro_no_existe` (defensivo: una clase sin
  cobro solo puede salir de tocar la base a mano). Además se reusan dos que ya
  estaban: 400 `materia_no_existe` y 400 `etapa_educativa_no_existe`.

### El frontend de P4

Tres pantallas, armadas con el mismo esqueleto que 1e y 1j (sección 7). Todas
hablan con el backend a través de `api/clases.js`, `api/pagos.js` y
`api/agenda.js`, y **ninguna hace cuentas de plata**: los importes llegan como
texto (`"1811.70"`) y `pesos()` de `utiles/formato.js` solo les da formato.
`diaYHora()` y `hora()` muestran las fechas siempre en la hora de Montevideo,
aunque la computadora esté en otra zona.

#### 1g · Checkout (`/checkout`, solo estudiante)

**Cómo se llega: el contrato de la URL.** 1f (de P2) navega así:

```
/checkout?profesor=<usuario_id>&materia=<id>&inicio=<ISO 8601 con zona>
         &duracion=<minutos>&modalidad=presencial|online
         [&traslado=1][&etapa=<id>][&tema=<texto>]
```

Va en la URL y no en el `state` del router para que sobreviva a un recargar.
`inicio` tiene que traer la zona (`2026-10-27T18:00:00-03:00`): sin zona, "18:00"
sería la hora de la computadora del alumno. Desde 1f, `URLSearchParams` se
encarga de codificar todo. Si falta algo o no tiene sentido, la pantalla lo dice
y ofrece volver a buscar, sin romperse. El contrato completo está comentado
arriba de `Checkout.jsx`.

1f ya construye ese enlace con `URLSearchParams` cuando el alumno selecciona
un hueco real. Mientras `GET /agenda/profesores/{id}/disponibilidad` siga sin
implementar, muestra el estado de agenda no disponible y mantiene “Reservar”
deshabilitado: no inventa fechas ni crea una reserva inválida.

| Archivo | Qué es |
|---|---|
| `paginas/Checkout.jsx` | La pantalla: lee la URL, carga todo junto y confirma |
| `paginas/checkout/ElegirMedio.jsx` | Las tarjetas guardadas (radios de verdad) o "Agregar tarjeta nueva" con "Guardar esta tarjeta en mi perfil" |
| `paginas/checkout/Resumen.jsx` | El desglose de `cotizar` y "Confirmar reserva" |
| `paginas/checkout/ReservaEnviada.jsx` | El cartel del final: atrapa el foco y deja la página de atrás `inert` |
| `componentes/FormularioTarjeta.jsx` | Los cuatro campos de una tarjeta. **El mismo** en 1g y en 1e |
| `utiles/tarjetas.js` | Formato (espacios cada cuatro, `MM/AA`), validación y el cuerpo para el backend. Duplica `TarjetaIn` para avisar al instante, como `validaciones.js` |
| `estilos/pagos.css` | Lo propio de 1g y de "Medios de pago" |

| Momento | Llamadas |
|---|---|
| Al entrar, las cuatro juntas | `GET /profesores/{id}` (la cabecera), `POST /clases/cotizar` (el desglose, **el mismo cálculo que 1f**), `GET /pagos/tarjetas`, `POST /agenda/verificar` (la segunda verificación) |
| "Confirmar reserva" | `POST /pagos/tarjetas` (solo si es nueva) → `POST /clases` → `DELETE /pagos/tarjetas/{id}` (solo si la nueva **no** se quería guardar) |

Tres detalles:

- **`agenda/verificar` todavía responde 500** (es de P3). El checkout sigue como
  si el horario estuviera libre: `POST /clases` vuelve a chequear y la base
  tiene la `EXCLUDE`. Cuando P3 lo implemente, un `{libre: false, motivo}` muestra
  un mensaje distinto por motivo y deshabilita confirmar.
- **"Guardar esta tarjeta" sin marcar** igual da de alta la tarjeta (el cobro
  necesita una), y la da de baja apenas se crea la clase. Si la reserva falla
  (por ejemplo, la tarjeta rechaza el pago), también se da de baja: no quedan
  tarjetas sueltas. Si **sí** se quería guardar, queda guardada y elegida, así
  reintentar no la da de alta dos veces.
- El doble clic no duplica la reserva: el botón queda `aria-disabled` mientras
  se envía y una `ref` frena el segundo envío.

#### 1e · La pestaña "Medios de pago" (`/mi-perfil`)

`paginas/perfil/SeccionMediosPago.jsx` reemplaza el marcador que había dejado P1.

| Qué | Llamada |
|---|---|
| Las tarjetas guardadas (marca, `•••• ultimos4`, titular, vencimiento) | `GET /pagos/tarjetas` |
| "Quitar", con confirmación en línea (no `window.confirm`) | `DELETE /pagos/tarjetas/{id}` (baja lógica) |
| "Agregar medio de pago", con el mismo `FormularioTarjeta` del checkout | `POST /pagos/tarjetas` |
| "Ver historial de pagos" (`HistorialPagos.jsx`), de a páginas con "Ver más pagos" | `GET /pagos/historial` |

En el historial, el estado del cobro va como etiqueta: retenido = "Pendiente de
aprobación", cobrado = "Pagado", liberado = "Solicitud rechazada · no se
cobró", reembolsado = "Reembolsado". En los liberados, `materia`,
`contraparte` y `clase_id` pueden venir en `null` (la clase se borró).

#### 1d · Panel del profesor (`/panel`, solo profesor)

`paginas/PanelProfesor.jsx` y sus piezas en `paginas/panel/`:

| Bloque | Archivo | Llamada | Lo recarga |
|---|---|---|---|
| Saludo ("Hola, Lucía" y materias · etapas · barrio) | `Saludo.jsx` | `GET /perfiles/profesor/yo` | — |
| Próxima clase | `ProximaClase.jsx` | `GET /clases/proxima` (204 = no hay) | — |
| Cuatro indicadores | `Indicadores.jsx` | `GET /clases/metricas?periodo=` | Mes / Trimestre / Año |
| Indicador de ingresos | `Indicadores.jsx` | `GET /pagos/ingresos?periodo=` | Mes / Trimestre / Año |
| Reservas de hoy | `ReservasDeHoy.jsx` | `GET /clases?desde=hoy&hasta=hoy` | — |
| Ingresos | `Ingresos.jsx` | `GET /pagos/ingresos?periodo=mes&agrupar=` | Semana / Mes / Año |
| Reservas en el tiempo | `ReservasEnElTiempo.jsx` | `GET /clases/series?agrupar=` | 10 semanas / Mes / Año |

Las siete llamadas salen juntas al entrar. **Si una falla, solo ese bloque
muestra su error** y el resto se ve igual. Cada bloque tiene su estado en
`useBloque.js`, un hook propio que además descarta las respuestas viejas (tocar
"Mes" y enseguida "Año"). "Hoy" es el de Montevideo (`panel/fechas.js`, la
misma cuenta que `app/fechas.py`).

**Los gráficos son SVG a mano, sin librerías** (`GraficoBarras.jsx`, simple o
apilado, compartido por los dos):

- `viewBox` y ancho 100 %, así se adaptan solos al celular. Las etiquetas de
  los ejes van en HTML y no adentro del SVG: el texto de un SVG escala con el
  dibujo y en 375 px quedaba ilegible.
- El backend no manda los tramos sin datos: `fechas.tramos()` arma la ventana
  (10 lunes, 12 primeros de mes, 5 eneros) y los completa con 0.
- Colores **solo con variables** de `tokens.css`, así el modo oscuro anda solo.
  "A confirmar" va hueca con borde punteado, como su etiqueta en la tabla.
  Cancelada y no_asistida van juntas como "No se dieron".
- Accesibles: el `svg` es `role="img"` con un resumen, cada columna tiene su
  `<title>` (el cartelito del mouse) y los mismos números van en una tabla
  `oculto-visual`. La leyenda nombra cada serie: el color nunca va solo.

Decisiones del panel: las tres cifras del bloque Ingresos son siempre del mes en
curso ("cobrado este mes", como el mockup); su selector cambia solo la
agrupación de las barras. En la tasa de cancelación, bajar se pinta como bueno.
El resumen de "Reservas de hoy" no cuenta las canceladas, pero la tabla sí las
muestra; en el celular, cada fila pasa a ser una tarjeta. Aprobar y rechazar son
de 1i: "Ver" y "Confirmar" llevan a `/agenda`.

#### Lo del mockup que no está en las pantallas de P4

| En el mockup | Por qué no está |
|---|---|
| El selector "Estudiante / Profesor" de la barra (1d) | No hay cambio de rol: una cuenta es una cosa o la otra |
| "si el pago va por la app · a definir" (1d) y el tag "Depende del pago in-app" (1e) | El pago es siempre por la app |
| El botón "Notas" de las clases dictadas (1d) | No hay notas de clase en el modelo. En su lugar, "Ver" lleva a la agenda |
| La variación de los ingresos ("14 % arriba de agosto") | `/pagos/ingresos` no la trae y la plata no se calcula en el frontend |
| "2 puntos menos" en la tasa de cancelación | La variación del backend es relativa, en %, no en puntos |
| La tarjeta "Principal", "Hacer principal" y "Editar" (1e) | No hay tarjeta principal (se elige en cada reserva) ni endpoint de edición: se quita y se agrega otra |
| Mercado Pago (1e) | Solo hay tarjetas |

### Lo que quedó afuera, y por qué

| Qué | Por qué |
|---|---|
| Reembolsos parciales según la anticipación | La política de cancelación no está decidida (sección 13.2). Hoy se devuelve el total |
| Que la materia de la reserva sea una de las que dicta el profesor | Se valida que exista en el catálogo, no que el profesor la dé: `ficha_resumida()` trae los nombres y no los ids. Se puede sumar con una función chica en perfiles |
| Que las solicitudes pendientes venzan solas | La spec dice "sin expiración automática" |
| Validar el horario contra la agenda | Es de P3 (`agenda.verificar()`); P4 ya la llama y la va a usar sola |
| Reintentar un reembolso que falló | La `BackgroundTask` corre una vez. Si justo se cae el servidor entre la respuesta y la tarea, el cobro queda `cobrado` con la clase `cancelada`. Con un cobro simulado no vale la complejidad; con una pasarela real haría falta una cola con reintentos o un barrido de esos casos |
| Que el promedio por clase cuente solo lo dictado | `promedio_por_clase` es lo cobrado del período sobre las dictadas del período, como pide la spec. Lo cobrado incluye las aprobadas que todavía no se dieron, así que a principio de mes puede salir alto |
| Que el profesor marque como dictada solo una clase que ya pasó | No se exige: con los seeds, las aprobadas están todas en el futuro, y no se podría probar completar |

---

## 10. El sistema de diseño

Los mockups usan un sistema llamado **Organic**. Está copiado tal cual en
`src/estilos/`, así que cualquier pantalla nueva que use estas clases se va a
ver igual al diseño sin esfuerzo.

### Los colores

| Variable | Valor | Para qué |
|---|---|---|
| `--color-bg` | `#f5ead8` | El fondo crema de toda la app |
| `--color-surface` | `#ebddc5` | Tarjetas e inputs, un tono más oscuro |
| `--color-text` | `#201e1d` | Casi negro, cálido |
| `--color-accent` | `#c67139` | Terracota: botones primarios, links, activo |
| `--color-accent-2` | `#7a8a5e` | Verde oliva: acento secundario |

Además hay tres **rampas tonales** de nueve pasos: `--color-neutral-100` a
`900`, `--color-accent-100` a `900`, y `--color-accent-2-100` a `900`. Están
generadas sobre una misma escala de luminosidad, así que el paso 500 del
naranja y el 500 del verde se ven igual de oscuros.

### Las tipografías

| Variable | Fuente | Para qué |
|---|---|---|
| `--font-heading` | Caprasimo | Títulos, botones, nombres. La redonda con personalidad |
| `--font-body` | Figtree | Todo el texto corrido |

Se cargan desde Google Fonts en `index.html`. Si el día de la defensa no hay
internet, se descargan los `.woff2` a `public/` y se cambian los links por un
`@font-face`.

Que los **botones usen la tipografía de títulos** es parte del sistema, no un
error.

### Las clases que hay disponibles

```html
<!-- Botones -->
<button class="btn btn-primary">Reservar</button>
<button class="btn btn-secondary">Cancelar</button>
<button class="btn btn-ghost">Ver mas</button>
<button class="btn btn-primary btn-block">Ocupa todo el ancho</button>

<!-- Formularios -->
<div class="field">
  <label for="x">Etiqueta</label>
  <input id="x" class="input">
  <span class="field-hint">Texto de ayuda</span>
</div>

<!-- Tarjetas -->
<div class="card elev-md">
  <span class="card-kicker">PROXIMA CLASE</span>
  <div class="card-title">Matematica con Lucia</div>
  <p class="card-body">Hoy 18:00</p>
</div>

<!-- Etiquetas -->
<span class="tag tag-accent">Presencial</span>
<span class="tag tag-accent-2">Online</span>
<span class="tag tag-neutral">Pendiente</span>

<!-- Texto secundario -->
<p class="text-muted">Algo menos importante</p>
```

Y estas, que se sumaron con las pantallas de perfil:

```html
<!-- Etiqueta "se puede agregar": borde punteado, sin relleno -->
<span class="tag tag-outline">+ Agregar materia</span>

<!-- Etiqueta que se toca. Con aria-pressed="true" se pinta llena -->
<button class="tag tag-neutral tag-boton" aria-pressed="true">1,5 h</button>

<!-- Aviso tranquilo (no es un error) -->
<div class="alerta alerta-info">...</div>

<!-- Esconde algo a la vista pero no al teclado (los input type="file") -->
<input type="file" class="oculto-visual">
```

Los estilos propios de 1e y 1j (el menú lateral, la cabecera verde, los
paneles, el interruptor) están en `estilos/perfil.css`.

### El modo oscuro

Está en `tokens.css`, debajo de los colores normales:

```css
:root[data-tema='oscuro'] {
  --color-bg: #172235;
  --color-accent: #6a95c4;   /* en oscuro el acento pasa a azul */
  ...
}
```

Cuando `<html>` tiene `data-tema="oscuro"`, se **redefinen las variables**, y
como todo el CSS usa variables y nunca colores sueltos, toda la app cambia de
color sin tocar nada más. Los valores son los del modo oscuro del mockup.

Quién pone ese atributo: `ContextoAuth.jsx`, según `usuario.tema`, que se
cambia con el interruptor del menú lateral de los perfiles. Es la mejor
prueba de por qué existe la regla de no escribir colores sueltos: un solo
color fijo en una pantalla y esa pantalla se ve mal en oscuro.

### Dos detalles del estilo

**Todo lo chico es una píldora.** Botones, inputs, etiquetas y el control
segmentado tienen `border-radius: 999px`. Las tarjetas y los diálogos usan
`calc(var(--radius-lg) * 1.15)`, o sea unos 32px. Es lo que le da el aire
redondeado al diseño.

**Las sombras están tintadas** con el color del texto, no con negro puro. Sobre
un fondo crema, una sombra negra se ve sucia.

### La regla

**Nunca escribas un color suelto.** Ni `#c67139`, ni `rgb(198,113,57)`. Siempre
`var(--color-accent)`. Así cambiar el acento en `tokens.css` lo cambia en toda
la aplicación.

---

## 11. Flujos completos

### Registrarse

```
  Usuario                Frontend                     Backend
    |                        |                           |
    | completa el form       |                           |
    | y aprieta Crear        |                           |
    |----------------------->|                           |
    |                        | valida en el cliente      |
    |                        |                           |
    |                        | POST /auth/registro/{rol} |
    |                        |-------------------------->|
    |                        |                           | crea usuario
    |                        |                           | crea el perfil vacio
    |                        |                           | emite el token
    |                        |<--------------------------|
    |                        | guarda el token           |
    |                        |                           |
    |                        | GET /usuarios/yo          |
    |                        |-------------------------->|
    |                        |<--------------------------|
    |                        | guarda el usuario         |
    |<-----------------------|                           |
    | ve su perfil vacio     |                           |
```

La cuenta y el perfil se crean **en la misma transacción**: o se crean los dos,
o no se crea ninguno. Si fallara en el medio, quedaría un usuario sin perfil y
`GET /usuarios/yo` se rompería.

### Reservar una clase

Es el flujo más largo y el que toca más módulos:

```
  1f Detalle del profesor
     GET /profesores/{id}                     la ficha
     GET /agenda/profesores/{id}/disponibilidad  los huecos libres
     POST /clases/cotizar                     el importe estimado
     POST /agenda/verificar                   sigue libre? (primera vez)
        |
        v
  1g Checkout
     GET /profesores/{id}                     la cabecera del resumen
     POST /clases/cotizar                     el desglose (MISMO calculo)
     GET /pagos/tarjetas                      las tarjetas guardadas
     POST /agenda/verificar                   sigue libre? (SEGUNDA vez)
     POST /clases                             crea la clase
        |
        | estado: pendiente
        | cobro:  retenido
        v
  1i Agenda del profesor
     GET /clases/pendientes                   le llega la solicitud
     POST /clases/{id}/aprobar                acepta
        |
        | estado: aprobada
        | cobro:  cobrado
        v
     El horario queda ocupado en la agenda
```

**Por qué se verifica dos veces.** Entre que el alumno elige el horario en 1f y
aprieta confirmar en 1g pueden pasar minutos. En ese rato otro pudo reservar el
mismo hueco. Y aun verificando dos veces queda una ventana de milisegundos: por
eso existe la restricción `EXCLUDE` en la base, que es la defensa real.

**Por qué el cálculo del importe es el mismo.** El estimado de 1f y el detalle
de 1g salen los dos de `POST /clases/cotizar`. Si alguien reescribiera el
cálculo en el frontend, los dos números diferirían y nadie sabría cuál vale.
La spec lo marca como "el más peligroso de duplicar".

### El dinero

```
  El alumno confirma        -> cobro: retenido
       |
       +-- el profe aprueba -> cobro: cobrado      cuenta en sus ingresos
       |        |
       |        +-- alguien cancela -> cobro: reembolsado  la clase queda en
       |                                                    cancelada, en el
       |                                                    historial
       |
       +-- el profe rechaza -> cobro: liberado     la clase SE BORRA,
       |                                            el cobro queda (sin clase)
       |
       +-- alguien cancela  -> cobro: liberado     todavia no se habia cobrado
           antes de aprobar
```

El reembolso corre como `BackgroundTask`: la respuesta del cancelar vuelve al
instante (con el reembolso `en_proceso`) y el cobro pasa a `reembolsado` un
momento después. Si la clase todavía estaba pendiente no hay nada que
reembolsar: la retención se libera en el momento.

**Ojo con esa función:** no recibe la sesión de la request, porque corre
después de que la respuesta ya se envió y para entonces esa sesión está
cerrada. Tiene que abrir la suya con `SesionLocal()`. Y tiene que ser
idempotente: si se encola dos veces, no puede devolver la plata dos veces.

### El cobro es simulado

No hay pasarela. Los datos de la tarjeta se guardan en la base y el cobro es un
registro que cambia de estado. Siempre responde bien, salvo que se fuerce el
error a propósito para poder probar el caso de fallo en 1g.

**Sobre guardar el número completo y el CCV:** para un trabajo de facultad con
datos inventados está bien y simplifica mucho. Ninguna plataforma real puede
hacerlo, ni siquiera cifrado (lo prohíbe PCI-DSS). Conviene decirlo en la
defensa **antes** de que lo pregunten: muestra que la decisión fue consciente.

Y en la base **no cargar nunca un número de tarjeta real**, ni propio ni de
nadie. Con `4111 1111 1111 1111` alcanza.

### Calcular los huecos libres

Es el cálculo más caro del sistema. Es una resta sucesiva:

```
  1. Las franjas activas de ese dia         "martes de 14 a 18"
  2. menos los bloqueos                     "el 12 de mayo no puedo"
  3. menos las clases APROBADAS             (las pendientes NO ocupan)
  4. menos el descanso entre clases
  5. menos lo que caiga antes de ahora + aviso minimo
  6. si el dia llego al tope, queda sin huecos
  7. de lo que quedo, los tramos donde entre la duracion pedida
```

Las pendientes no ocupan: varias solicitudes sobre el mismo hueco son
legítimas. El profesor elige cuál aprueba.

---

## 12. Qué está hecho y qué falta

### Hecho

- La estructura completa del monorepo
- `docker-compose.yml` con PostgreSQL y las extensiones (`citext`, `btree_gist`)
- Las **24 tablas** modeladas en SQLAlchemy, repartidas en los nueve módulos
- Los **12 tipos ENUM**
- Los **66 endpoints** montados y visibles en `/docs`
- Todos los `esquemas.py` (los contratos de entrada y salida)
- Alembic configurado, leyendo la conexión del `.env`
- **La migración inicial** (`alembic/versions/79d6aea11ac3_esquema_inicial.py`):
  las 24 tablas, los 12 ENUM, los 13 índices de `schema.sql` y la restricción
  `EXCLUDE`
- **La segunda migración** (`6d0c95b67436_cobro_sobrevive_al_rechazo.py`, de
  P4): `cobro.clase_id` nullable con `ON DELETE SET NULL` (ver la sección 9)
- **Los seeds** (`app/seeds.py`): catálogos, veinte usuarios con sus perfiles
  y su oferta, franjas de disponibilidad y treinta clases con su cobro, con los
  importes calculados por `clases.logica.desglosar()`
- `schema.sql` completo, de referencia
- El frontend entero: proxy, rutas, contexto de autenticación, sistema de
  diseño y componentes
- **Login, registro y recuperar contraseña**, funcionando de punta a punta
- **Todo lo de P1** (ver la sección 7): `usuario_actual()`, los módulos
  `cuentas` y `perfiles` completos, y las pantallas **1e** y **1j**, con
  modo oscuro
- **Todo el backend de P2** y las pantallas **1c** y **1f** (ver la sección
  8): filtros, resultados paginados, ficha pública, cotización, mapas y pines
  con datos reales
- **Todo lo de P4** (ver la sección 9): los módulos `clases` y `pagos`
  completos, los 19 endpoints, el cobro simulado con su reembolso en segundo
  plano, las métricas y series del panel, lo que leen agenda y reseñas, y las
  pantallas **1g** (checkout), **1d** (panel del profesor) y la pestaña
  "Medios de pago" de **1e**, con modo oscuro
- Las pantallas restantes enrutadas con un marcador

### Verificado

- El backend importa y monta las 66 rutas (`python -c "from app.main import app"`)
- Las 24 tablas quedan registradas en `Base.metadata`
- Desde un clon limpio, con Python 3.13 y con 3.14: `docker compose up -d`,
  `pip install`, `alembic upgrade head` y `python -m app.seeds` (corrido dos
  veces seguidas, sin duplicar nada)
- `alembic check` no encuentra diferencias entre los modelos y la base, y
  `alembic downgrade base` seguido de `alembic upgrade head` vuelve a andar
- El frontend compila (`npm run build`) sin errores ni advertencias
- Login y registro renderizan con el diseño correcto y la validación funciona
- Sin errores en la consola del navegador
- P1, backend: 93 comprobaciones contra una base real que recorren los 26
  endpoints con sus casos de error (roles, ids inexistentes, menor sin
  adulto, foto de más, código de recuperación vencido o probado cinco veces,
  baja que invalida el token, que la ficha pública no filtre campos privados)
- P1, frontend: recorrido completo en el navegador de 1e y 1j (guardar cada
  sección, subir fotos, publicar y pausar, modo oscuro, cerrar sesión), con y
  sin los catálogos de P2, y en ancho de celular sin scroll horizontal
- P2, backend: **21 comprobaciones** contra la base sembrada: solo fichas
  publicadas; filtros y órdenes de modalidad, precio y distancia; paginación;
  esquema de resultados; pines sin duplicados y en el orden pedido; cercanos;
  ids y rangos inválidos; delegación del filtro de disponibilidad a agenda; y
  ranking con el mínimo de reseñas dentro de una transacción revertida
- P4, backend: **276 comprobaciones** (`backend/verificar_p4.py`) contra una base
  real recién sembrada, que recorren los 19 endpoints con tokens de los usuarios
  de los seeds: el flujo cotizar → crear → aprobar → cancelar con el reembolso
  llegando en segundo plano; crear → rechazar con el cobro liberado en el
  historial; que el total de cotizar y el de la clase sean idénticos y que un
  precio con centavos cuadre al centésimo; dos solicitudes sobre el mismo horario
  (la segunda aprobación da 409); la tarjeta terminada en 0000 y la vencida, sin
  que la clase quede creada; roles cruzados, ids inexistentes y estados
  inválidos; que las tarjetas no filtren el número ni el CCV; reprogramar una
  aprobada y volver a aprobarla; completar (sube `clases_dictadas` y
  `tuvieron_clase` da `True`); métricas, series e ingresos con los tres
  períodos y las tres agrupaciones, contra cuentas hechas en SQL; los bordes de
  los días en Montevideo. Y además: la app importa, `alembic downgrade -1` /
  `upgrade head` / `check` sin diferencias, y los seeds dos veces seguidas sin
  duplicar, con las treinta clases cuadrando con `desglosar()` y los mismos
  totales que antes. Las 276 pasan también sobre el código ya integrado (las
  tres ramas de P4 juntas)
- P4, frontend, en el navegador sobre el código integrado y contra una base
  recién sembrada: **1g** reservando con una tarjeta guardada (la clase queda
  `pendiente` con el cobro `retenido` y el mismo total que la cotización), con
  una tarjeta nueva sin guardar (no queda en el perfil), con una terminada en
  `0000` (mensaje de pago rechazado, la clase no se crea y la tarjeta no queda),
  con una vencida (el campo queda marcado), el mismo horario dos veces (409 con
  "Elegir otro horario") y una URL incompleta; **1e** agregar y quitar una
  tarjeta (nunca se ve el número completo) y el historial con la reserva nueva
  como "Pendiente de aprobación"; **1d** con profe1 y con un profe sin clases
  (todos los estados vacíos y el 204), los tres selectores. Las tres en modo
  oscuro y a 375 px sin scroll horizontal, sin errores de JavaScript, y
  `npm run build` sin advertencias. En la consola solo aparece el 500 de
  `POST /agenda/verificar`, que es de P3 y el checkout tolera

### Falta

Todavía faltan funciones del backend de **P3**. P1, P2 y P4 ya tienen su lógica
y sus rutas; las pantallas 1c y 1f de P2 consumen los endpoints disponibles.
En 1f, el calendario y la lista detallada de reseñas muestran un estado vacío
controlado hasta que P3 complete sus rutas.
Cada pendiente de P3 tiene su docstring con lo que debería hacer y termina con:

```python
raise NotImplementedError("P3 - agenda: calcular los huecos libres")
```

Ese texto dice **quién** la tiene que escribir y **de qué módulo** es.

Para encontrarlas todas:

```bash
grep -rn "TODO (P" backend/app/
grep -rn "NotImplementedError" backend/app/
```

#### Pantalla pendiente de P3: redactar una reseña

La ruta ya reservada es
`/resenas/redactar/:destinatarioId`. Está protegida para los dos roles, usa el
`Layout` común y por ahora muestra `EnConstruccion`. No se agrega al menú: se
abre desde una persona concreta.

En **1b, Mis clases**, P3 debe leer `GET /api/clases/mis-profesores`. La sección
“Reseñas pendientes” muestra las filas cuyo `mi_resena` sea `null`; cada una
tiene el botón **Calificar**, que navega a la ruta anterior usando
`persona.id` como `destinatarioId`. Las filas que ya tengan `mi_resena` deben
permitir **Editar reseña**. En **1i** se repite el mismo flujo con
`GET /api/clases/mis-alumnos`.

El formulario pide un puntaje obligatorio de 1 a 5 y un comentario opcional.
Usa las funciones ya preparadas en `frontend/src/api/resenas.js`:

- `dejarResena(datos)` hace `POST /api/resenas` cuando `mi_resena` es `null`;
- `editarResena(datos)` hace `PUT /api/resenas` cuando ya existe;
- `datos` tiene `{ destinatario_id, puntaje, texto }`.

Al guardar, vuelve a 1b o 1i y recarga la lista para que la persona deje de
aparecer como pendiente. Cancelar vuelve sin escribir. El backend valida que
ambos hayan tenido una clase `dictada`, impide una segunda creación para el
mismo par y mantiene anónimo al autor en las respuestas públicas. Los errores
esperados son `sin_clases_con_esa_persona` y `ya_resenado`, ya traducidos en
`frontend/src/api/mensajes.js`.

El orden de la spec:

| Semana | Qué |
|---|---|
| 1 | Los cuatro juntos: revisar la migración inicial y los seeds (ya están escritos) y el acuerdo escrito de los endpoints compartidos. Nadie escribe lógica |
| 2–3 | P1 termina `cuentas` y el esqueleto de `perfiles`. P2 termina `catalogos`. Los otros dos trabajan contra respuestas fijas |
| 4–6 | P1 la ficha pública. P2 la búsqueda y los mapas. P3 agenda. P4 el ciclo de la clase |
| 7–8 | P3 mensajería y reseñas. P4 checkout, reembolsos y métricas |
| 9 | Integración de las diez pantallas contra datos reales |
| 10 | Corrección, datos de demo y ensayo de la presentación |

### Por dónde empezar

**P1 ya terminó**, así que el login, el registro y el token funcionan: todas
las rutas con `Yo`, `Estudiante` o `Profesor` ya resuelven al usuario. Lo que
más destraba ahora:

**P2**: 1a, 1c y 1f ya están conectadas. Día, franja, próxima hora y reseñas
detalladas dependen de P3.

**P3**: `mensajeria/logica.py` → `contar_no_leidos()`. Hoy el contador de la
barra de arriba muestra siempre 0. Y una función pública en `agenda` para
saber si un profesor tiene franjas, para sumarla al chequeo de publicar.
Además, P4 ya llama a tres funciones de P3 y las va a usar apenas existan, sin
cambiar nada (sección 9): `agenda.verificar()` (hoy crear y reprogramar no
saben de franjas ni bloqueos), `agenda.hay_bloqueo_encima()` y
`resenas.resena_de()`. Lo que agenda y reseñas necesitan de `clases`
(`clases_entre`, `clases_aprobadas_entre`, `tuvieron_clase`) ya está.
En frontend, también le corresponde reemplazar la ruta pendiente
`/resenas/redactar/:destinatarioId` y conectar los botones **Calificar** de 1b
y 1i con `POST` o `PUT /api/resenas`.

**P4**: terminado, backend y pantallas. 1f ya arma el enlace al checkout cuando
Agenda entrega un hueco. Falta que P3 implemente `agenda.verificar()` para que
1g avise antes de confirmar si el horario ya no está libre.

---

## 13. Cosas que hay que decidir

La spec marca tres cosas sin cerrar. Las tres bloquean trabajo.

### 1. La lista definitiva de etapas educativas

El esquema viejo del equipo decía escuela, liceo, orientación y facultad. El
mockup filtra por ciclo básico, bachillerato, UTU, universidad y examen de
ingreso. **Todo el filtrado de 1c depende de que sea una sola lista.**

En `app/seeds.py` está puesta la lista del mockup, que es la que manda:

```python
ETAPAS = [
    ("Ciclo básico", 1, ["1.o", "2.o", "3.o"]),
    ("Bachillerato", 2, ["4.o", "5.o", "6.o"]),
    ("UTU", 3, ["1.o", "2.o", "3.o"]),
    ("Universidad", 4, ["1.o", "2.o", "3.o", "4.o", "5.o"]),
    ("Examen de ingreso", 5, []),
]
```

Si la cambian, hay que cambiarla ahí y recargar los seeds.

### 2. La política de cancelación

¿Se reembolsa el total siempre, o hay un plazo mínimo? Por ejemplo: si cancela
con menos de 24 horas, ¿se le devuelve todo?

**Sigue sin decidir.** Hoy el código hace esto, la cancele quien la cancele:

- Si la clase estaba **pendiente**, no se había cobrado nada: la retención se
  **libera** en el momento.
- Si estaba **aprobada**, se devuelve el **total**, en segundo plano
  (`pagos.logica.reembolsar()`), y la respuesta lo informa como
  `{"estado": "en_proceso", "importe": <total>}`.

Está marcado con un comentario "PENDIENTE DE DECIDIR" en
`pagos.logica.reembolsar()` y en `clases.logica.cancelar()`. Si se decide un
plazo, el lugar es `cancelar()`, que tiene la clase y sabe quién cancela.
Ojo: un reembolso **parcial** no entra en el modelo actual, porque el cobro
tiene un solo `importe` y un estado; haría falta una columna nueva en `cobro`
(por ejemplo, `importe_reembolsado`), o sea una migración.

### 3. Los acentos y las eñes

Las tablas, columnas y rutas van en español **sin tildes ni eñes** en los
identificadores (`resena`, `busqueda`, `anios_experiencia`). Los textos que ve
el usuario sí llevan acentos.

El código y los comentarios de este proyecto están escritos sin acentos para
evitar problemas de codificación entre las máquinas del equipo. Esta
documentación sí los usa.

---

## Apéndice: preguntas que van a aparecer

**El frontend dice "No se pudo conectar con el servidor".**
El backend no está levantado, o no está en el 8000. Probá
`http://localhost:8000/api/salud`.

**`alembic upgrade head` falla con `password authentication failed for user "exonero"`.**
Alembic se está conectando a otro PostgreSQL, casi siempre uno instalado en
Windows que ocupa el 5432. Revisá que `BASE_URL` en tu `.env` diga
`localhost:5433` (si copiaste el `.env.example` antes de que se cambiara el
puerto, dice 5432) y que el contenedor esté levantado: `docker compose ps`
tiene que mostrar `exonero_db` con `0.0.0.0:5433->5432/tcp`. Si lo levantaste
antes con el 5432, `docker compose up -d` lo recrea con el puerto nuevo sin
borrar los datos.

**`pip install -r requirements.txt` falla en `psycopg-binary` o `pydantic-core`.**
Tu Python es de una versión que no está probada, y pip no encuentra esos
paquetes ya compilados. Con 3.13 y 3.14 anda. Instalá una de esas, borrá la
carpeta `.venv` y creala de nuevo (`py -3.13 -m venv .venv`).

**`alembic` no se reconoce como comando.**
El entorno virtual no está activado (`.venv\Scripts\activate`), o el
`pip install` falló antes de llegar a instalar Alembic: mirá su error. También
se puede correr sin activar: `.venv\Scripts\python -m alembic upgrade head`.

**`alembic upgrade head` falla con `relation "..." already exists`.**
Las tablas se crearon por fuera de Alembic (por ejemplo corriendo `schema.sql`
a mano), y Alembic no sabe que ya están. Hay que empezar con la base vacía:
`docker compose down -v`, `docker compose up -d` y de nuevo
`alembic upgrade head`. **Eso borra todos los datos**, así que recargá los
seeds después.

**Cambié un modelo y `autogenerate` no detecta nada.**
El módulo no está importado en `app/registro_modelos.py`.

**Muchos endpoints devuelven 500 `NotImplementedError`.**
Es lo esperado mientras no estén hechos: los cuerpos están vacíos a propósito.
El mensaje del error dice quién la tiene que escribir. En el frontend se ve
como "El servidor tuvo un problema" (código `error_servidor`).

**En 1e o 1j los desplegables de barrio, centro o materias están grises.**
`GET /api/catalogos/todo` (P2) todavía responde 500. La pantalla muestra un
aviso, deja ver lo que ya estaba guardado y no permite cambiar esos campos.
Se habilitan solos cuando P2 lo implemente.

**No puedo publicar mi ficha: "te falta al menos una materia y el precio".**
Para publicar hace falta una materia y el precio de cada modalidad que
ofrecés. Si das "Presencial y online", hacen falta los dos precios.

**Guardé la información personal de un alumno menor y dice que falta el adulto.**
Si la fecha de nacimiento da menos de 18 años, el nombre y el teléfono del
adulto responsable son obligatorios.

**El código de recuperar la contraseña dice que no es válido.**
Vence a los 15 minutos, sirve una sola vez y se anula al quinto intento
equivocado. Además vive en memoria: si `uvicorn --reload` se reinició porque
guardaste un archivo, se perdió. Pedí otro.

**Cambié la foto y en la barra de arriba sigue la vieja.**
No debería pasar: `CabeceraPerfil` llama a `refrescar()` del contexto y la
barra se actualiza sola. Si pasa, mirá la consola del navegador: casi seguro
falló `GET /usuarios/yo`.

**En la pestaña de red veo cada llamada dos veces.**
Es `StrictMode` de React, que en desarrollo corre los efectos dos veces a
propósito para sacar a la luz código que no soporta repetirse. En producción no
pasa.

**El input no me deja escribir.**
Le falta el `onChange`. Un input controlado necesita los dos: `value` y
`onChange`.
