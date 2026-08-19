# Data Quality Action Plan (DQAP) Accelerator

A reusable **Databricks solution accelerator** that implements the GOV.UK *[Data Quality Action Plan](https://www.gov.uk/government/publications/guidance-on-implementing-a-data-quality-action-plan)* methodology. It is a governance and workflow tool for UK government organisations to define and monitor critical data assets, track quality improvements, and report on progress.

**Design spec:** see [`docs/superpowers/specs/2026-08-11-dqap-accelerator-design.md`](docs/superpowers/specs/2026-08-11-dqap-accelerator-design.md)

## What It Is

### The GOV.UK Methodology

The DQAP framework guides organisations through seven steps to improve and maintain data quality:

1. **Identify critical data** — register data assets essential to operations
2. **Identify data quality rules** — define rules against six quality dimensions
3. **Assess current data quality** — measure scores against each rule
4. **Prioritise improvements and set goals** — backlog actions with priority
5. **Identify root cause and take action** — log issues and implement fixes
6. **Report on data quality** — portfolio scorecard across all assets
7. **Repeat / measure over time** — trend analysis and continuous improvement

### The Six Quality Dimensions

Rules are tagged to one of these government-standard dimensions:
- **Completeness** — required fields are populated
- **Accuracy** — values match the source of truth
- **Validity** — values conform to format and constraints
- **Timeliness** — data is current (within SLA of source/refresh)
- **Uniqueness** — no duplicate records
- **Consistency** — values match across related systems

### Architecture

```
[ React SPA (GOV.UK Design System) ]  --HTTPS/JSON-->  [ FastAPI backend ]  -->  [ Lakebase / Postgres ]
```

**Frontend:** React with [GOV.UK Design System](https://design-system.service.gov.uk/) components. Single-page app for asset registration, rule definition, score entry, and portfolio reporting.

**Backend:** FastAPI service that owns the Lakebase connection pool, enforces authentication (via forwarded Databricks App identity headers), and exposes REST API. Implements the **assessment-provider seam** (see below).

**Database:** PostgreSQL (Lakebase) for system of record. All tables carry `created_at`, `updated_at`, `created_by`, `updated_by` for audit trail.

### The Assessment-Provider Seam (Longevity Design)

Quality scores live in a time-series `measurements` table. *How* those scores are produced is swappable:

- **MVP ships `ManualProvider`** — a user records a score and evidence note for each rule; the setup script seeds ~6 months of history so trends render immediately.
- **Phase 2 (designed, not built):**
  - `WarehouseSqlProvider` — runs each rule's SQL against a Databricks SQL warehouse and appends the result
  - `LakehouseMonitoringProvider` — reads Databricks Lakehouse Monitoring metric tables and maps them onto rules

Both phase-2 providers append to the *same* `measurements` table, so "connect into Databricks quality metrics" becomes "add one provider class + a scheduled refresh," with no UI or schema change.

**How to add a provider:**
1. Create a new provider class in `server/providers/` implementing the `AssessmentProvider` protocol:
   ```python
   @dataclass
   class Measurement:
       score: float
       measured_at: datetime
       method: str
       source: str
       evidence_note: Optional[str] = None
       sample_size: Optional[int] = None

   class AssessmentProvider(Protocol):
       def measure(self, rule: dict, payload: dict) -> Measurement: ...
   ```
2. Register it in `server/providers/__init__.py`:
   ```python
   _REGISTRY = {
       "manual": ManualProvider,
       "warehouse": WarehouseSqlProvider,  # Phase 2
       "monitoring": LakehouseMonitoringProvider,  # Phase 2
   }
   ```
3. Deploy with `ASSESSMENT_PROVIDER=warehouse` (or `monitoring`) in `app.yaml`.

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (or Postgres.app on macOS)
- `uv` ([install](https://github.com/astral-sh/uv)) for Python dependency management

### First Time Setup

1. **Create the test database:**
   ```bash
   createdb dqap_test
   ```

2. **Install Python dependencies:**
   ```bash
   uv sync
   ```

3. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### Running Tests

```bash
# Run the full backend test suite against the local test database
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_assets.py -v

# Run tests matching a pattern
uv run pytest -k "test_bootstrap" -v
```

Tests use PostgreSQL (default `postgresql://localhost/dqap_test`). Override with `TEST_DATABASE_URL=postgresql://<user>:<pass>@<host>/<db> uv run pytest`.

### Seeding the Test Database

```bash
# Create schema + seed the UK Ship Register worked example
uv run python setup.py --seed

# Create schema only (empty)
uv run python setup.py

# Reset: drop all tables, recreate schema, and seed
uv run python setup.py --reset --seed
```

### Running the Backend

The backend requires either a running local Postgres instance (for local dev) or a Lakebase endpoint (for Databricks deployment).

**Local Postgres path** — set `LOCAL_DATABASE_URL` to bypass Lakebase:
```bash
# First, create and seed the DB (only needed once or after a reset):
createdb dqap_test
LOCAL_DATABASE_URL=postgresql://localhost/dqap_test uv run python setup.py --seed

# Then start the server:
LOCAL_DATABASE_URL=postgresql://localhost/dqap_test uv run uvicorn app:app --port 8000 --reload

# Open http://localhost:8000/api/health to confirm it's running
```

**Without `LOCAL_DATABASE_URL`** the app expects Lakebase environment variables (`LAKEBASE_INSTANCE_NAME`, `PGHOST`, `PGUSER`, `PGPORT`, `PGDATABASE`) and will fail at startup if they are absent. Running `uv run uvicorn app:app` alone against local Postgres will not work.

### Running the Frontend

In a second terminal:
```bash
cd frontend

# Development server (http://localhost:5173)
npm run dev

# The dev server proxies /api/* to http://localhost:8000
```

### Local E2E Test

1. Seed the database: `uv run python setup.py --seed`
2. Start backend: `uv run uvicorn app:app --port 8000` (terminal 1)
3. Start frontend: `cd frontend && npm run dev` (terminal 2)
4. Open [http://localhost:5173](http://localhost:5173)
5. You should see the dashboard with seeded UK Ship Register scores
6. Click into an asset to see the 7-step task list and per-rule trend charts
7. Test add/record/resolve/advance controls; download the CSV export

### Building Frontend for Production

```bash
cd frontend
npm run build

# Output goes to frontend/dist/, served by app.py in production
```

## Deployment to Databricks

The accelerator is designed to be deployed by any UK government customer with one command. See **[`docs/DEPLOY.md`](docs/DEPLOY.md)** for the complete customer runbook.

### Quick summary

1. **Build the frontend:**
   ```bash
   cd frontend && npm run build && cd ..
   ```

2. **Deploy with `databricks bundle deploy`**, overriding the five bundle variables for your environment:
   ```bash
   databricks bundle deploy \
     --var catalog=my_catalog \
     --var metrics_schema=dqap \
     --var warehouse_id=<id> \
     --var lakebase_instance=<instance> \
     --var app_service_principal=<sp-client-id>
   ```
   The bundle creates the app, Lakebase instance, UC schema (with `USE_SCHEMA`/`CREATE_TABLE` grants), and the daily monitoring job.

3. **One manual Postgres grant** — once, as the Lakebase instance admin:
   ```sql
   GRANT USAGE, CREATE ON SCHEMA public TO "<app-sp-client-id>";
   GRANT ALL ON ALL TABLES IN SCHEMA public TO "<app-sp-client-id>";
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "<app-sp-client-id>";
   ```
   This is a Postgres-internal grant that no bundle resource can express. The `dqap` UC schema grants are handled by the bundle automatically.

4. **First boot** — the app self-installs its tables and seeds the UK Ship Register example. Set `RUN_SETUP_ON_START=false` and `SEED_ON_START=false` in `app.yaml` after first boot, then redeploy.

For the full runbook including prerequisites, variable reference, and scheduled-job configuration, see [`docs/DEPLOY.md`](docs/DEPLOY.md).

## Reset for a New Organisation

### Option A: Start from Scratch (Recommended for Multi-Org Deployments)

1. **In the deployed app, set `RUN_SETUP_ON_START=false` and `SEED_ON_START=false`** (to prevent auto-wipe on boot)
2. **Manually reset the database:**
   ```bash
   # If you have shell access to the workspace or Postgres:
   psql -h <pghost> -U <pguser> -d <pgdatabase>
   DROP TABLE IF EXISTS actions, issues, measurements, quality_rules, data_assets CASCADE;
   ```
   Or use `python setup.py --reset` from local dev.

3. The app will show an empty dashboard on next boot.

### Option B: Auto-Bootstrap with Empty State

Set `RUN_SETUP_ON_START=true` and `SEED_ON_START=false`:
- App creates schema on boot
- No seed data — start completely empty

## Swapping the Worked Example

The MVP ships with the **UK Ship Register** as a seeded example. To use your own data:

1. **Create your own seed module** at `seed/my_dataset.py`:
   ```python
   def seed(conn):
       """Populate the database with your organisation's critical data assets and rules."""
       # Example:
       conn.execute(
           "INSERT INTO data_assets (id, name, description, ...) VALUES (%s, %s, %s, ...)",
           [uuid.uuid4(), "My Asset", "Description", ...]
       )
       conn.execute(
           "INSERT INTO quality_rules (id, asset_id, dimension, name, ...) VALUES (%s, %s, %s, %s, ...)",
           [uuid.uuid4(), asset_id, "completeness", "Check for nulls", ...]
       )
       # ... add measurements, issues, actions, etc.
   ```

2. **Update `setup.py`** to import your seed:
   ```python
   if seed:
       from seed.my_dataset import seed as seed_example
       seed_example(conn)
   ```

3. **Deploy with `SEED_ON_START=true`** on first boot to load your data.

See [`seed/uk_ship_register.py`](seed/uk_ship_register.py) for a full worked example with all six dimensions.

## API Endpoints

All endpoints are under `/api` and return JSON. Standard CRUD:

- **Assets:** `GET/POST /api/assets`, `GET/PATCH/DELETE /api/assets/{id}`
- **Rules:** `GET/POST /api/assets/{id}/rules`, `PATCH/DELETE /api/rules/{id}`
- **Measurements:** `GET/POST /api/rules/{id}/measurements` (POST uses active `AssessmentProvider`)
- **Issues:** `GET/POST /api/assets/{id}/issues`, `PATCH/DELETE /api/issues/{id}`
- **Actions:** `GET/POST /api/assets/{id}/actions`, `PATCH/DELETE /api/actions/{id}`
- **Dashboard:** `GET /api/dashboard` (aggregated scorecard across all assets)
- **Export:** `GET /api/assets/{id}/export` (DQAP in CSV format)

All requests must include the `X-Forwarded-Email` header (provided by the Databricks App wrapper in production; set manually in dev/tests).

## Testing

### Backend Test Suite

```bash
# Full suite
uv run pytest -v

# With coverage
uv run pytest --cov=server tests/

# Specific tests
uv run pytest tests/test_assets.py tests/test_rules.py -v
```

Tests use a transactional test fixture (`db_conn` in `tests/conftest.py`) so each test is isolated and rolls back automatically.

### Frontend Tests

```bash
cd frontend
npm run test
```

### Production Build Verification

```bash
# Build frontend
cd frontend && npm run build && npm run test -- --run

# Ensure backend tests pass
cd .. && uv run pytest -v

# If all green, the app is ready to deploy
```

## Project Structure

```
├── app.py                          # FastAPI entry point, lifespan + static serving
├── app.yaml                        # Databricks App config (Option B auth)
├── databricks.yml                  # Asset Bundle definition
├── setup.py                        # Setup CLI (--reset, --seed)
├── pyproject.toml                  # Python dependencies (uv)
│
├── server/
│   ├── app.py                      # (Aliased in root app.py)
│   ├── config.py                   # IS_DATABRICKS_APP, ASSESSMENT_PROVIDER
│   ├── db.py                       # Lakebase pool, connection helpers
│   ├── models.py                   # Pydantic schemas
│   ├── schema.sql                  # Database tables + types
│   ├── bootstrap.py                # Self-install logic (RUN_SETUP_ON_START)
│   ├── identity.py                 # Forwarded identity helpers
│   ├── errors.py                   # Error handlers (JSON shape)
│   ├── providers/                  # Assessment provider seam
│   │   ├── base.py                 # AssessmentProvider protocol
│   │   ├── manual.py               # ManualProvider (MVP)
│   │   └── __init__.py             # Registry
│   ├── repositories/               # Data access layer (CRUD helpers)
│   ├── routes/                     # API endpoints
│   │   ├── assets.py               # Asset CRUD
│   │   ├── rules.py                # Rule CRUD
│   │   ├── measurements.py         # Measurement CRUD + AssessmentProvider call
│   │   ├── issues.py               # Issue CRUD
│   │   ├── actions.py              # Action CRUD
│   │   ├── dashboard.py            # Scorecard aggregation
│   │   └── export.py               # CSV export
│   └── __init__.py
│
├── frontend/
│   ├── index.html                  # Entry point
│   ├── package.json                # npm dependencies (React, Vite, GOV.UK)
│   ├── src/
│   │   ├── main.tsx                # React entry
│   │   ├── App.tsx                 # Router
│   │   ├── components/             # React components
│   │   ├── pages/                  # Page components (Dashboard, Assets, Detail, Export)
│   │   ├── lib/                    # Helpers (API client, formatting)
│   │   └── styles/                 # CSS (GOV.UK overrides)
│   ├── public/                     # Static assets (GOV.UK fonts, images)
│   ├── dist/                       # Production build output
│   └── tsconfig.json
│
├── seed/
│   ├── uk_ship_register.py         # Worked example (all 6 dimensions)
│   └── __init__.py
│
├── tests/
│   ├── conftest.py                 # Fixtures (db_conn, client)
│   ├── test_*.py                   # Unit + integration tests per resource
│   └── __init__.py
│
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-08-11-dqap-accelerator-design.md  # Full design spec
```

## For More Information

- **Design spec:** [`docs/superpowers/specs/2026-08-11-dqap-accelerator-design.md`](docs/superpowers/specs/2026-08-11-dqap-accelerator-design.md)
- **GOV.UK guidance:** [Implement a data quality action plan](https://www.gov.uk/government/publications/guidance-on-implementing-a-data-quality-action-plan)
- **GOV.UK Design System:** [design-system.service.gov.uk](https://design-system.service.gov.uk/)

## License

TBD

