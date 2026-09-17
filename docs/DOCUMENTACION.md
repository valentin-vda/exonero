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
7. [El sistema de diseño](#7-el-sistema-de-diseño)
8. [Flujos completos](#8-flujos-completos)
9. [Qué está hecho y qué falta](#9-qué-está-hecho-y-qué-falta)
10. [Cosas que hay que decidir](#10-cosas-que-hay-que-decidir)

---

## 1. Qué es esto y cómo se levanta

Exonero es una plataforma de clases particulares: un alumno busca profesores
por materia, barrio, precio y horario, mira la agenda real del profe, reserva
un hueco y paga. El profesor aprueba o rechaza cada solicitud.

El proyecto es un **monorepo**: frontend, backend y `docker-compose.yml` en el
mismo lugar, una rama principal y un *pull request* por pantalla.

### Levantarlo por primera vez

```bash
# 1. La base de datos (es lo unico que corre en Docker)
docker compose up -d

# 2. El backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # en Windows
pip install -r requirements.txt
copy .env.example .env          # y revisar los valores
alembic upgrade head            # crea las tablas
python -m app.seeds             # carga los datos de prueba
uvicorn app.main:app --reload   # queda en http://localhost:8000

# 3. El frontend, en otra terminal
cd frontend
npm install
npm run dev                     # queda en http://localhost:5173
```

Abrí `http://localhost:5173` y te va a recibir el login.

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
│   ├── docker/init.sql         extensiones citext y btree_gist
│   ├── alembic/
│   │   ├── env.py              lee la conexion del .env
│   │   └── versions/           una migracion por pull request
│   └── app/
│       ├── main.py             crea la app y monta los routers
│       ├── config.py           toda la configuracion, leida del .env
│       ├── db.py               engine, sesion y la clase Base
│       ├── enums.py            los 13 tipos ENUM de PostgreSQL
│       ├── seguridad.py        hash bcrypt y firma de tokens
│       ├── errores.py          ErrorAPI y el formato unico de error
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
        │   ├── tokens.css      colores, tipografias, espaciado
        │   ├── componentes.css .btn .input .card .tag .nav ...
        │   └── auth.css        login y registro
        ├── api/
        │   ├── cliente.js      el fetch con token y manejo de errores
        │   ├── mensajes.js     codigo de error -> texto en espanol
        │   └── auth.js         una funcion por endpoint de cuentas
        ├── auth/
        │   ├── ContextoAuth.jsx  quien esta conectado
        │   └── RutaProtegida.jsx rutas que exigen sesion
        ├── componentes/
        │   ├── Layout.jsx        la barra de navegacion
        │   ├── MarcoAuth.jsx     el layout de dos columnas
        │   ├── Campo.jsx         etiqueta + input + error
        │   ├── CampoClave.jsx    con el boton de mostrar/ocultar
        │   ├── SelectorRol.jsx   las dos tarjetas del registro
        │   ├── Alerta.jsx        el cartel de error
        │   └── EnConstruccion.jsx marcador de las pantallas pendientes
        ├── paginas/
        │   ├── Login.jsx         HECHA
        │   ├── Registro.jsx      HECHA
        │   └── RecuperarClave.jsx HECHA
        └── utiles/
            └── validaciones.js
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
                       ▼                localhost:5432
   ┌──────────────────────────────────────────────┐
   │  PostgreSQL 16  (en Docker)                  │
   │  24 tablas, 13 tipos ENUM                    │
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

  perfiles --> catalogos.existe()           validar ids

  busqueda --> perfiles.ficha_resumida()    completar los resultados
           --> catalogos.centroide_barrio() calcular distancias
           --> agenda.filtrar_con_hueco()   el filtro de disponibilidad

  agenda   --> perfiles.reglas_profesor()   descanso, tope, aviso minimo
           --> clases.clases_aprobadas_entre()  descontar lo ocupado

  clases   --> perfiles.precio_vigente()
           --> catalogos.parametros_vigentes()  comision e IVA
           --> agenda.verificar()           sigue libre el horario?
           --> pagos.retener/cobrar/liberar/reembolsar()

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
tiene que quedar registrado.

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

Expone cinco cosas:

| Qué | Para qué |
|---|---|
| `usuario` | El usuario conectado, o `null` |
| `cargando` | `true` mientras se averigua si hay sesión |
| `entrar(correo, clave)` | Hace el login y deja la sesión abierta |
| `registrarse(rol, datos)` | Crea la cuenta y deja la sesión abierta |
| `salir()` | Borra el token |

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
| `/login` | Login | — | Hecha |
| `/registro` | Registro | — | Hecha |
| `/recuperar` | Recuperar contraseña | — | Hecha |
| `/inicio` | Inicio del estudiante | 1a | Pendiente, P2 |
| `/buscar` | Buscar profes | 1c | Pendiente, P2 |
| `/profesor/:id` | Detalle del profesor | 1f | Pendiente, P2 |
| `/checkout` | Checkout | 1g | Pendiente, P4 |
| `/mis-clases` | Mis clases | 1b | Pendiente, P3 |
| `/mi-perfil` | Perfil del estudiante | 1e | Pendiente, P1 |
| `/panel` | Panel del profesor | 1d | Pendiente, P4 |
| `/agenda` | Agenda del profesor | 1i | Pendiente, P3 |
| `/perfil-profesor` | Perfil del profesor | 1j | Pendiente, P1 |
| `/mensajes` | Mensajes | 1h | Pendiente, P3 |

Las pendientes ya están enrutadas y muestran un cartel de `EnConstruccion`. Se
puede navegar por toda la app desde el día uno sin que se rompa nada.

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

Estas dos pantallas **no existían en el prototipo de mockups** (la spec las
marca como "sin pantalla en el prototipo" y dice que bloquean a P1 en la
semana 2). Están diseñadas siguiendo el mismo sistema visual que el resto.

### El layout

Las tres pantallas de autenticación comparten `MarcoAuth.jsx`:

```
┌───────────────────────────┬───────────────────────────┐
│                           │                           │
│  Panel terracota          │  Fondo crema              │
│                           │                           │
│  Exonero                  │      Entrar               │
│                           │      Bienvenido de vuelta │
│  Clases particulares,     │                           │
│  cerca tuyo.              │      Correo               │
│                           │      [___________]        │
│  Encontra profes de tu    │                           │
│  materia en tu barrio...  │      Contrasena           │
│                           │      [________] Mostrar   │
│  1 Busca por materia...   │                           │
│  2 Elegi un hueco...      │      [    Entrar    ]     │
│  3 El profe confirma      │                           │
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

## 7. El sistema de diseño

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

## 8. Flujos completos

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
       |
       +-- el profe rechaza -> cobro: liberado     la clase SE BORRA,
       |                                            el cobro queda
       |
       +-- alguien cancela  -> cobro: reembolsado  la clase queda en
                                                    cancelada, en el historial
```

El reembolso corre como `BackgroundTask`: la respuesta del cancelar vuelve al
instante y el cobro pasa a `reembolsado` unos segundos después.

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

## 9. Qué está hecho y qué falta

### Hecho

- La estructura completa del monorepo
- `docker-compose.yml` con PostgreSQL y las extensiones (`citext`, `btree_gist`)
- Las **24 tablas** modeladas en SQLAlchemy, repartidas en los nueve módulos
- Los **13 tipos ENUM**
- Los **66 endpoints** montados y visibles en `/docs`
- Todos los `esquemas.py` (los contratos de entrada y salida)
- Alembic configurado, leyendo la conexión del `.env`
- `schema.sql` completo, de referencia
- El frontend entero: proxy, rutas, contexto de autenticación, sistema de
  diseño y componentes
- **Login, registro y recuperar contraseña**, funcionando y conectadas
- Las otras diez pantallas enrutadas con un marcador

### Verificado

- El backend importa y monta las 66 rutas (`python -c "from app.main import app"`)
- Las 24 tablas quedan registradas en `Base.metadata`
- El frontend compila (`npm run build`) sin errores ni advertencias
- Login y registro renderizan con el diseño correcto y la validación funciona
- Sin errores en la consola del navegador

### Falta

Todos los cuerpos de las funciones del backend. Cada una tiene su docstring
con lo que debería hacer, numerado paso a paso, y termina con:

```python
raise NotImplementedError("P1 - cuentas: crear la cuenta")
```

Ese texto dice **quién** la tiene que escribir y **de qué módulo** es.

Para encontrarlas todas:

```bash
grep -rn "TODO (P" backend/app/
grep -rn "NotImplementedError" backend/app/
```

El orden de la spec:

| Semana | Qué |
|---|---|
| 1 | Los cuatro juntos: la migración inicial, el script de seeds y el acuerdo escrito de los endpoints compartidos. Nadie escribe lógica |
| 2–3 | P1 termina `cuentas` y el esqueleto de `perfiles`. P2 termina `catalogos`. Los otros dos trabajan contra respuestas fijas |
| 4–6 | P1 la ficha pública. P2 la búsqueda y los mapas. P3 agenda. P4 el ciclo de la clase |
| 7–8 | P3 mensajería y reseñas. P4 checkout, reembolsos y métricas |
| 9 | Integración de las diez pantallas contra datos reales |
| 10 | Corrección, datos de demo y ensayo de la presentación |

### Por dónde empezar

**P1**, que es quien bloquea a todos:

1. `app/dependencias.py` → `usuario_actual()`. Sin esto no anda ninguna ruta
   con token.
2. `cuentas/logica.py` → `crear_cuenta()` y `autenticar()`.
3. `cuentas/rutas.py` → el registro y el login.
4. `perfiles/logica.py` → `crear_perfil_estudiante()` y `crear_perfil_profesor()`.
5. `cuentas/rutas.py` → `GET /usuarios/yo`.

Con esos cinco, **el login y el registro que ya están hechos empiezan a
funcionar de punta a punta**. Es la forma más rápida de ver el proyecto vivo.

**P2** en paralelo: `catalogos/logica.py` y `catalogos/rutas.py`, que no
dependen de nadie.

---

## 10. Cosas que hay que decidir

La spec marca tres cosas sin cerrar. Las tres bloquean trabajo.

### 1. La lista definitiva de etapas educativas

El esquema viejo del equipo decía escuela, liceo, orientación y facultad. El
mockup filtra por ciclo básico, bachillerato, UTU, universidad y examen de
ingreso. **Todo el filtrado de 1c depende de que sea una sola lista.**

En `app/seeds.py` está puesta la lista del mockup, que es la que manda:

```python
ETAPAS = [
    ("Ciclo basico", 1, ["1.o", "2.o", "3.o"]),
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

P4 lo necesita para escribir `pagos.logica.reembolsar()`. Hoy el código asume
**total siempre**, y está marcado con un comentario en esa función.

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

**`alembic upgrade head` falla con "extension citext does not exist".**
El contenedor de la base se creó sin correr `docker/init.sql`. Se ejecuta una
sola vez, cuando el volumen se crea vacío. Si ya existía, hay que borrar el
volumen (`docker compose down -v`) y volver a levantar. **Eso borra todos los
datos**, así que recargá los seeds después.

**Cambié un modelo y `autogenerate` no detecta nada.**
El módulo no está importado en `app/registro_modelos.py`.

**Todos los endpoints devuelven 500 `NotImplementedError`.**
Es lo esperado: los cuerpos están vacíos a propósito. El mensaje del error dice
quién la tiene que escribir.

**En la pestaña de red veo cada llamada dos veces.**
Es `StrictMode` de React, que en desarrollo corre los efectos dos veces a
propósito para sacar a la luz código que no soporta repetirse. En producción no
pasa.

**El input no me deja escribir.**
Le falta el `onChange`. Un input controlado necesita los dos: `value` y
`onChange`.
