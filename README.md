# URL Shortener 

API de acortador de URLs con analítica básica, construida como el primer proyecto de un roadmap de portafolio DevOps enfocado en contenedores, bases de datos, caché, control de versiones y (más adelante) Kubernetes y despliegue en servidor real.

## Por qué este proyecto

Un acortador de URLs es un problema fácil de explicar en una frase, pero para resolverlo bien requiere casi todo lo que necesita un backend real: persistencia de datos, una capa de caché para tráfico alto, empaquetado reproducible con contenedores, y un flujo de trabajo con control de versiones profesional. Se eligió a propósito un caso de uso simple para poder enfocar el esfuerzo en la infraestructura y las buenas prácticas alrededor, en vez de en lógica de negocio compleja.

## Stack y por qué se eligió cada pieza

| Tecnología | Rol en el proyecto |
- **Python (FastAPI)** — API REST
- **PostgreSQL** — almacenamiento persistente de URLs y contador de clics
- **Redis** — caché de lecturas frecuentes (evita ir a Postgres en cada redirección)
- **Nginx** — reverse proxy: único punto de entrada expuesto al exterior (puerto 80); la API queda solo accesible dentro de la red interna de Docker
- **Docker + Docker Compose** — contenerización de todo el stack
- **Git/GitHub** — control de versiones (siguiente paso: pipeline de CI/CD)

## Estructura del proyecto

```text
├── app/
│ ├── main.py # endpoints de la API
│ ├── config.py # configuración (variables de entorno)
│ ├── database.py # conexión a Postgres (SQLAlchemy)
│ ├── models.py # modelo de la tabla urls
│ ├── schemas.py # esquemas de entrada/salida (Pydantic)
│ └── redis_client.py # cliente de Redis
├── nginx/
│ └── nginx.conf # configuración del reverse proxy
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```


## Cómo funciona la caché (patrón cache-aside)

1. Llega un pedido de redirección para un código corto.
2. La API pregunta primero a Redis. Si está ahí, redirige al instante sin tocar Postgres.
3. Si no está en Redis, busca en Postgres, guarda el resultado en caché (por 1 hora), y redirige.

Esto significa que solo las URLs que de verdad se están usando ocupan espacio en la caché, y la base de datos solo se consulta en la primera visita de cada una — el resto del tráfico se resuelve desde memoria, mucho más rápido.

**Limitación conocida y a propósito:** el contador de clics que ves en `/api/urls/{code}` solo se actualiza en la visita que no estuvo cacheada. Las visitas que sí pegan en caché incrementan un contador aparte dentro de Redis (`clicks:{code}`), que todavía no se sincroniza automáticamente con Postgres. Sincronizar ambos contadores con un proceso en segundo plano queda como mejora pendiente.


## Cómo correrlo (con Docker, recomendado)

Requisitos: Docker y Docker Compose instalados (en tu PC con Ubuntu, o en el VPS).

```bash
cp .env.example .env
docker compose up -d --build
```

Esto levanta 4 contenedores: `nginx` (único puerto expuesto al host, el **80**), `api`, `postgres` y `redis` (estos tres últimos solo visibles entre sí dentro de la red interna de Docker). Verifica que todo esté sano:

```bash
curl http://localhost/health
```

## Endpoints

| Método | Ruta                  | Descripción                                  |
|--------|-----------------------|-----------------------------------------------|
| POST   | `/api/urls`           | Crea una URL corta. Body: `{"target_url": "https://..."}` |
| GET    | `/api/urls/{code}`    | Info de una URL corta (clics, fecha, destino) |
| GET    | `/{code}`             | Redirige a la URL original (307)              |
| GET    | `/health`             | Chequeo de salud (Postgres + Redis)           |
| GET    | `/metrics`            | Métricas en formato Prometheus                |

Ejemplo:

```bash
curl -X POST http://localhost/api/urls \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://www.google.com"}'

# -> {"short_code": "uL3Z7Kv", "short_url": "http://localhost/uL3Z7Kv", ...}

curl -i http://localhost/uL3Z7Kv
# -> 307 redirect a https://www.google.com/
```

## Variables de entorno relevantes

`BASE_URL` (en `.env`) define el host que se usa para armar el `short_url` que devuelve la API. Debe coincidir con la puerta de entrada real del stack: `http://localhost` en local (vía Nginx, puerto 80 implícito), y el dominio real con `https://` una vez desplegado en el VPS con TLS.

## Cómo se probó este proyecto

Todo el stack (`nginx`, `api`, `postgres`, `redis`) se levantó con `docker compose up -d --build` y se probó de extremo a extremo a través del reverse proxy: creación de URL, redirección (307), caché en Redis y chequeo de salud, todo pasando únicamente por el puerto 80 de Nginx — la API ya no queda expuesta directamente al host.


## Qué demuestra

Contenedores en producción, integración de una API con una base de datos relacional y una caché, diseño de un esquema con migraciones, y las bases para observabilidad y despliegue continuo — todo documentado y reproducible con un solo comando.