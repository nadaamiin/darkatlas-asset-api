# DarkAtlas Asset Management API

A REST API for managing internet-facing security assets, built as part of the DarkAtlas Attack Surface Monitoring (ASM) platform by Buguard.

## Tech Stack

- **Python 3.11** + **FastAPI** — API framework
- **PostgreSQL** — Database
- **SQLAlchemy** — ORM
- **Alembic** — Database migrations
- **Docker** + **Docker Compose** — Containerization
- **pytest** — Testing

---

## Project Structure
darkatlas-asset-api/

├── app/

│   ├── main.py          # FastAPI app entry point

│   ├── config.py        # Environment variables

│   ├── database.py      # Database connection

│   ├── auth.py          # API key authentication

│   ├── models/          # SQLAlchemy database models

│   ├── schemas/         # Pydantic request/response schemas

│   ├── routers/         # API endpoints

│   └── services/        # Business logic

├── alembic/             # Database migrations

├── tests/               # pytest tests

├── Dockerfile

├── docker-compose.yml

└── requirements.txt

---

## Setup & Run

### Option A — Docker (recommended)

The easiest way to run the project. Requires Docker Desktop.

1. Clone the repository:
```bash
git clone https://github.com/nadaamiin/darkatlas-asset-api.git
cd darkatlas-asset-api
```

2. Create your environment file:
```bash
cp .env.example .env
```

3. Start everything with one command:
```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`

---

### Option B — Local development

1. Clone the repository:
```bash
git clone https://github.com/nadaamiin/darkatlas-asset-api.git
cd darkatlas-asset-api
```

2. Create and activate virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create your environment file:
```bash
cp .env.example .env
```

5. Create the PostgreSQL database:
```bash
sudo -u postgres psql
CREATE USER assetuser WITH PASSWORD 'assetpass';
CREATE DATABASE assetdb OWNER assetuser;
GRANT ALL PRIVILEGES ON DATABASE assetdb TO assetuser;
\q
```

6. Run database migrations:
```bash
alembic upgrade head
```

7. Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://assetuser:assetpass@localhost/assetdb` |
| `API_KEY` | Secret key for write operations | `dev-secret-key` |
| `DEBUG` | Enable debug mode | `True` |

---

## API Documentation

FastAPI generates interactive documentation automatically:

- **Swagger UI** → `http://localhost:8000/docs`
- **ReDoc** → `http://localhost:8000/redoc`

---

## Authentication

Write operations require an API key in the request header:
X-API-Key: your-api-key

Read operations (`GET`) are public and require no authentication.

---

## API Endpoints

### Assets
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/assets/` | No | List assets with filtering, sorting, pagination |
| GET | `/assets/{id}` | No | Get a single asset |
| POST | `/assets/` | Yes | Create a new asset |
| PATCH | `/assets/{id}` | Yes | Update an asset |
| DELETE | `/assets/{id}` | Yes | Delete an asset |
| POST | `/assets/bulk` | Yes | Bulk import assets |
| POST | `/assets/mark-stale` | Yes | Mark old assets as stale |

### Relationships
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/assets/relationships` | Yes | Create a relationship |
| GET | `/assets/{id}/relationships` | No | Get asset relationships |
| GET | `/assets/{id}/graph` | No | Get asset + connected assets |

---

## Filtering & Pagination

The `GET /assets/` endpoint supports:
/assets/?type=domain

/assets/?status=active

/assets/?tag=prod

/assets/?value_contains=example

/assets/?sort_by=last_seen&sort_order=desc

/assets/?page=1&page_size=20

---

## Bulk Import

Import multiple assets at once. Handles deduplication automatically:

```bash
curl -X POST http://localhost:8000/assets/bulk \
  -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '[
    {"id": "a1", "type": "domain", "value": "example.com", "source": "scan", "tags": ["root"], "metadata": {}},
    {"id": "a2", "type": "subdomain", "value": "api.example.com", "source": "scan", "tags": ["prod"], "metadata": {}}
  ]'
```

Response:
```json
{
  "created": 2,
  "updated": 0,
  "failed": 0,
  "errors": []
}
```

---

## Running Tests

```bash
# Create test database first
sudo -u postgres psql -c "CREATE DATABASE assetdb_test OWNER assetuser;"

# Run all tests
pytest tests/ -v
```

Expected output: 16 passed in 3.12s

---

## Design Decisions & Assumptions

### Deduplication strategy
Assets are deduplicated by `value + type` combination. Re-importing the same asset updates `last_seen`, merges tags (no duplicates), and merges metadata (new values override old ones).

### ID handling
- Regular `POST /assets/` always auto-generates a UUID
- `POST /assets/bulk` preserves IDs from the dataset if provided, generates UUID if not

### Lifecycle
- `first_seen` is set once at creation and never changes
- `last_seen` is updated on every re-sighting
- Assets not seen for 30 days (configurable) can be marked stale via `POST /assets/mark-stale`
- A stale asset that reappears in an import is automatically reactivated

### Relationships
- Relationships are directional (source → target)
- Deleting an asset cascades and deletes its relationships automatically

### Authentication
- Read operations are public
- All write operations require `X-API-Key` header
- API key is loaded from environment variable

### Error handling
- Bulk import never crashes on a single bad record — it skips and reports failures
- All endpoints return consistent JSON error responses
- 404 for missing resources, 401 for missing/invalid auth, 422 for validation errors