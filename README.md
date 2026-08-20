# Data Quality Action Plan (DQAP) Accelerator

A reusable **Databricks solution accelerator** that implements the GOV.UK *[Data Quality Action Plan](https://www.gov.uk/government/publications/guidance-on-implementing-a-data-quality-action-plan)* methodology. It is a governance and workflow tool for UK government organisations to define and monitor critical data assets, track quality improvements, and report on progress.

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

**Frontend:** React with the [GOV.UK Design System](https://design-system.service.gov.uk/). Single-page app for asset registration, rule definition, score entry, and portfolio reporting.

**Backend:** FastAPI service that owns the Lakebase connection pool, derives the acting user from the forwarded Databricks App identity header, and exposes a REST API.

**Database:** PostgreSQL (Lakebase) as the system of record. All tables carry `created_at`, `updated_at`, `created_by`, `updated_by` for an audit trail.

**Measurement & monitoring.** Quality scores live in a time-series `measurements` table. A score can be recorded **manually**, or computed **automatically**: attach a read-only SQL statement (`SELECT`/`WITH`) to a rule and the app runs it on a Databricks SQL warehouse and records the result. A scheduled Databricks Job refreshes those SQL-based measures and mirrors the full application state into Unity Catalog Delta tables, so quality can be tracked over time with native Databricks tooling (AI/BI dashboards, Lakehouse Monitoring). Data assets can also be linked to real Unity Catalog tables, and each asset carries a customisable RACI matrix.

## Deploying to Databricks

The accelerator deploys in **two passes** — because a Databricks App's service principal is created *with* the app, so you can't supply it up front. See **[`docs/DEPLOY.md`](docs/DEPLOY.md)** for the complete runbook.

> The repo ships a **prebuilt `frontend/dist`**, so you can deploy as-is — no frontend build required. Only rebuild (`cd frontend && npm run build`) if you change the frontend.

### Quick summary

1. **Create the app** (Databricks mints its service principal automatically) and read the SP's client ID:
   ```bash
   databricks apps create dqap-accelerator
   databricks apps get dqap-accelerator | grep service_principal
   ```

2. **Grant that SP its Postgres role** — once, as the Lakebase instance admin:
   ```sql
   GRANT USAGE, CREATE ON SCHEMA public TO "<app-sp-client-id>";
   GRANT ALL ON ALL TABLES IN SCHEMA public TO "<app-sp-client-id>";
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "<app-sp-client-id>";
   ```
   This is a Postgres-internal grant that no bundle resource can express. The UC schema grant is handled by the bundle automatically.

3. **Deploy the rest**, bound to that SP — this deploys the app code and provisions the Lakebase instance, the UC metrics schema (+grant), and the daily monitoring job:
   ```bash
   databricks bundle deploy \
     --var app_service_principal=<sp-client-id-from-step-1> \
     --var warehouse_id=<your-warehouse-id> \
     --var catalog=<your-catalog> \
     --var metrics_schema=dqap \
     --var lakebase_instance=dqap-accelerator
   ```
   `catalog` and `metrics_schema` default to `main`/`dqap` if omitted; `warehouse_id` and `app_service_principal` are required.

4. **First boot** — the app self-installs its tables and seeds the UK Ship Register example. Set `RUN_SETUP_ON_START=false` and `SEED_ON_START=false` in `app.yaml` after first boot, then redeploy.

## Resetting for a New Organisation

### Option A: Start from scratch (recommended for multi-org deployments)

1. In the deployed app, set `RUN_SETUP_ON_START=false` and `SEED_ON_START=false` (to prevent auto-wipe on boot).
2. Manually reset the database:
   ```bash
   psql -h <pghost> -U <pguser> -d <pgdatabase>
   DROP TABLE IF EXISTS actions, issues, measurements, quality_rules, asset_tables, asset_step_status, data_assets CASCADE;
   ```
   Or use `python setup.py --reset` from local dev.
3. The app shows an empty dashboard on next boot.

### Option B: Auto-bootstrap with empty state

Set `RUN_SETUP_ON_START=true` and `SEED_ON_START=false` — the app creates the schema on boot with no seed data.

## Swapping the Worked Example

The accelerator ships with the **UK Ship Register** as a seeded example. To use your own data:

1. **Create your own seed module** at `seed/my_dataset.py`:
   ```python
   def seed(conn):
       """Populate the database with your organisation's critical data assets and rules."""
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

All endpoints are under `/api` and return JSON.

- **Assets:** `GET/POST /api/assets`, `GET/PATCH/DELETE /api/assets/{id}`
- **Rules:** `GET/POST /api/assets/{id}/rules`, `PATCH/DELETE /api/rules/{id}`
- **Measurements:** `GET/POST /api/rules/{id}/measurements` (record a score)
- **Automatic measures:** `POST /api/rules/{id}/measure/run`, `POST /api/assets/{id}/measure/run-all` (run a rule's SQL on the warehouse and record the result)
- **Unity Catalog:** `GET /api/uc/catalogs|schemas|tables` (browse), `GET/POST/DELETE /api/assets/{id}/tables` (link UC tables to an asset)
- **Journey:** `GET /api/assets/{id}/journey`, `PUT /api/assets/{id}/journey/{item_key}` (7-step progress)
- **Issues:** `GET/POST /api/assets/{id}/issues`, `PATCH/DELETE /api/issues/{id}`
- **Actions:** `GET/POST /api/assets/{id}/actions`, `PATCH/DELETE /api/actions/{id}`
- **RACI:** `GET /api/raci`, `POST/DELETE /api/raci/roles`, `PATCH /api/raci/roles/{id}`, `PUT /api/raci/cells`
- **Dashboard:** `GET /api/dashboard` (aggregated scorecard across all assets)
- **Export:** `GET /api/assets/{id}/export` (DQAP in CSV format)

In production the Databricks App wrapper supplies the `X-Forwarded-Email` header (used for the audit trail); it is set manually in dev/tests.

## Project Structure

```
├── app.py                          # FastAPI entry point, lifespan + SPA static serving
├── app.yaml                        # Databricks App config
├── databricks.yml                  # Asset Bundle (app, Lakebase instance, UC schema, job)
├── setup.py                        # Setup CLI (--reset, --seed)
├── pyproject.toml / requirements.txt
│
├── server/
│   ├── config.py                   # IS_DATABRICKS_APP, ASSESSMENT_PROVIDER
│   ├── db.py                       # Lakebase pool, connection helpers
│   ├── models.py                   # Pydantic schemas
│   ├── schema.sql                  # Database tables + types
│   ├── bootstrap.py                # Self-install logic (RUN_SETUP_ON_START)
│   ├── identity.py                 # Forwarded identity helper
│   ├── errors.py                   # Error handlers (JSON shape)
│   ├── uc.py                       # Unity Catalog browse (SDK)
│   ├── raci_content.py             # Canonical RACI activities + default seed
│   ├── providers/                  # Score providers (manual, warehouse SQL)
│   ├── repositories/               # Data access layer (CRUD helpers)
│   └── routes/                     # API endpoints (assets, rules, measurements, issues,
│                                   #   actions, dashboard, export, asset_tables, uc, raci)
│
├── jobs/                           # Scheduled job: run SQL measures + mirror state to UC
│   ├── run_measures.py
│   ├── sync_to_uc.py
│   └── uc_sync_tables.py
│
├── frontend/
│   ├── index.html                  # Entry point
│   ├── package.json                # npm dependencies (React, Vite, GOV.UK)
│   ├── src/
│   │   ├── main.tsx / App.tsx       # React entry + router
│   │   ├── api/                     # API client + types
│   │   ├── components/              # React components
│   │   └── pages/                   # Dashboard, Assets, Detail, Export
│   ├── public/                      # Static assets (GOV.UK fonts, images)
│   └── dist/                        # Production build output (served by app.py)
│
├── seed/uk_ship_register.py        # Worked example (all 6 dimensions)
├── tests/                          # Backend (pytest) + frontend (vitest) tests
└── docs/DEPLOY.md                  # Customer deploy runbook
```

## Testing

**Backend** (pytest, against a local Postgres):
```bash
uv run pytest -v                      # full suite
uv run pytest tests/test_assets.py    # a single file
uv run pytest -k test_bootstrap        # by pattern
```
Tests use a transactional fixture (`db_conn` in `tests/conftest.py`) so each test is isolated and rolls back automatically. Default DB `postgresql://localhost/dqap_test`; override with `TEST_DATABASE_URL`.

**Frontend** (vitest):
```bash
cd frontend && npm run test
```

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (or Postgres.app on macOS)
- `uv` ([install](https://github.com/astral-sh/uv)) for Python dependency management

### First-time setup

```bash
createdb dqap_test          # create the local database
uv sync                     # install Python dependencies
cd frontend && npm install && cd ..   # install frontend dependencies
```

### Seed the database

```bash
uv run python setup.py --seed          # schema + UK Ship Register example
uv run python setup.py                 # schema only (empty)
uv run python setup.py --reset --seed  # drop, recreate, reseed
```

### Run it locally

`LOCAL_DATABASE_URL` bypasses Lakebase and points the app at local Postgres:

```bash
# Terminal 1 — backend
LOCAL_DATABASE_URL=postgresql://localhost/dqap_test uv run python setup.py --seed   # once
LOCAL_DATABASE_URL=postgresql://localhost/dqap_test uv run uvicorn app:app --port 8000 --reload

# Terminal 2 — frontend (proxies /api/* to :8000)
cd frontend && npm run dev
```

Open [http://localhost:5173](http://localhost:5173) — you should see the dashboard with seeded scores; click into an asset for the 7-step journey, per-rule trend charts, issues, actions, and the RACI matrix.

Without `LOCAL_DATABASE_URL`, the app expects the Lakebase environment variables injected by the Databricks App and will not start against a bare local Postgres.

### Build the frontend for production

```bash
cd frontend && npm run build   # output to frontend/dist/, served by app.py
```

## More Information

- **GOV.UK guidance:** [Implement a data quality action plan](https://www.gov.uk/government/publications/guidance-on-implementing-a-data-quality-action-plan)
- **GOV.UK Design System:** [design-system.service.gov.uk](https://design-system.service.gov.uk/)
- **Deploy runbook:** [`docs/DEPLOY.md`](docs/DEPLOY.md)

## License

TBD
