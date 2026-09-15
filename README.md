# URL Shortener 

API de acortador de URLs con analítica básica, construida como el primer proyecto de un roadmap de portafolio DevOps enfocado en contenedores, bases de datos, caché, control de versiones y (más adelante) Kubernetes y despliegue en servidor real.

## Por qué este proyecto

Un acortador de URLs es un problema fácil de explicar en una frase, pero para resolverlo bien requiere casi todo lo que necesita un backend real: persistencia de datos, una capa de caché para tráfico alto, empaquetado reproducible con contenedores, y un flujo de trabajo con control de versiones profesional. Se eligió a propósito un caso de uso simple para poder enfocar el esfuerzo en la infraestructura y las buenas prácticas alrededor, en vez de en lógica de negocio compleja.

## Stack y por qué se eligió cada pieza

| Tecnología | Rol en el proyecto |
|---|---|
| **FastAPI** (Python) | Framework de API moderno, rápido y muy usado en la industria hoy en día. |
| **PostgreSQL** | Persistencia real: las URLs y su historial de clics sobreviven a un reinicio del servicio. |
| **Redis** | Caché de lecturas frecuentes — evita golpear la base de datos en cada clic, clave para tráfico alto. |
| **Docker + Docker Compose** | Empaqueta los tres servicios para que corran igual en cualquier máquina, sin el clásico "en mi PC funciona". |
| **Git + GitHub** | Ramas por funcionalidad y Pull Requests, el mismo flujo de trabajo que se usa en equipos de desarrollo reales. |

## Estructura del proyecto

```text
url-shortener/
├── app/
│ ├── main.py # endpoints de la API
│ ├── config.py # configuración (variables de entorno)
│ ├── database.py # conexión a Postgres (SQLAlchemy)
│ ├── models.py # modelo de la tabla urls
│ ├── schemas.py # esquemas de entrada/salida (Pydantic)
│ └── redis_client.py # cliente de Redis
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

## Cómo correrlo

Requisitos: Docker y Docker Compose instalados.

```bash
cp .env.example .env
docker compose up -d --build
curl http://localhost:8000/health
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/urls` | Crea una URL corta. Body: `{"target_url": "https://..."}` |
| GET | `/api/urls/{code}` | Info de una URL corta (clics, fecha, destino) |
| GET | `/{code}` | Redirige a la URL original (307) |
| GET | `/health` | Chequeo de salud (Postgres + Redis) |

Ejemplo:

```bash
curl -X POST http://localhost:8000/api/urls \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://www.anthropic.com"}'

curl -i http://localhost:8000/uL3Z7Kv
# -> 307 redirect a https://www.anthropic.com/
```

## Mejoras pendientes (siguientes fases del roadmap)

- [ ] Reverse proxy con Nginx + TLS (Let's Encrypt) delante de la API.
- [ ] Desplegar en un VPS Ubuntu con Docker.
- [ ] Dashboard en Grafana leyendo métricas vía Prometheus.
- [ ] Pipeline de CI/CD en GitHub Actions (test + build + deploy).
- [ ] Sincronizar el contador de clics cacheado en Redis con Postgres.
- [ ] Migrar el esquema con Alembic en vez de `create_all`.
- [ ] Backups automáticos de Postgres.