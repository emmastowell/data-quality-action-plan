# DQAP Accelerator — Customer Deploy Runbook

This runbook takes you from a fresh clone to a fully running DQAP instance with scheduled daily monitoring. Deployment is a **two-pass** flow (see §4): create the app so Databricks mints its service principal, then deploy the rest bound to that SP — plus a single documented Postgres grant.

---

## 1. Prerequisites

### Tooling

- **Databricks CLI ≥ 0.240** — `databricks --version` to check. Install via [Databricks CLI docs](https://docs.databricks.com/dev-tools/cli/databricks-cli.html).
- **Node.js 18+** — _only_ if you modify the frontend. The repo ships a prebuilt `frontend/dist`, so deploying as-is needs no Node/build step.
- **uv** — to manage Python deps locally if you need to run tests.

### Workspace requirements

Your Databricks workspace must have:

| Requirement | Notes |
|---|---|
| Unity Catalog enabled | The bundle creates a schema and grants in UC |
| A managed **Lakebase Database Instance** | The app and the daily job both connect via Lakebase OAuth. The bundle will create one if it does not exist. |
| A **Serverless SQL warehouse** | Used to execute `measurement_sql` queries on rules. Supply it with `--var warehouse_id=<id>` (a Serverless Starter Warehouse is a good choice). |
| An **app service principal** | **Auto-created by Databricks when the app is created** (§4, pass 1) — you don't pre-create it. It owns the app process, runs the daily job, and holds the Lakebase Postgres role. |

### Service principal permissions

The app service principal needs:

- **Workspace access** — at minimum `CAN_USE` on the workspace so it can mint Lakebase OAuth credentials.
- **SQL warehouse** — `CAN_USE` on the warehouse specified by `warehouse_id`.
- **Unity Catalog** — `USE CATALOG` and `USE SCHEMA` on any catalog/schema the app browses via the data-asset picker; `SELECT` on any tables referenced by `measurement_sql` queries. Keep grants minimal — grant at schema or table level, not catalog-wide.

### The deploying user needs `servicePrincipal.user` on the app SP

Because the daily job's `run_as` is set to the app service principal, whoever runs `databricks bundle deploy` must hold the **account-level `servicePrincipal.user` role** on that SP — otherwise the deploy fails with a 403 when binding `run_as`. (`servicePrincipal.manager` alone is not sufficient.) Grant it once via the account access-control rule-set, preserving any existing roles:

```bash
# Log in with an ACCOUNT-level profile (account console host + account id)
databricks auth login --host https://accounts.cloud.databricks.com --account-id <account-id> -p acct

# Fetch the SP's default rule set, add roles/servicePrincipal.user for the deploying
# user (keep existing principals), then update:
databricks account access-control get-rule-set \
  "accounts/<account-id>/servicePrincipals/<app-sp-client-id>/ruleSets/default" "" -p acct
databricks account access-control update-rule-set --json @rule-set.json -p acct
```

---

## 2. Configure — the five bundle variables

The bundle is parameterised by five variables, set with `--var` on the CLI or a `targets.<target>.variables` block in `databricks.yml`. Most have sensible defaults; `warehouse_id` and `app_service_principal` are required (you supply your own — and `app_service_principal` is obtained in §4 pass 1, since the app's SP is created with the app).

| Variable | Default | Purpose |
|---|---|---|
| `catalog` | `main` | Unity Catalog that holds the mirrored metrics schema |
| `metrics_schema` | `dqap` | Schema (within catalog) for the mirrored app tables |
| `warehouse_id` | _(required)_ | SQL warehouse used to run `measurement_sql` — supply your own |
| `lakebase_instance` | `dqap-accelerator` | Managed Lakebase Database Instance name |
| `app_service_principal` | _(required)_ | Client ID of the app's **auto-created** SP — obtained in §4 pass 1 (run_as, grants, PGUSER) |

The full deploy command lives in **§4 (Deploy)** because `app_service_principal` isn't known until the app is created. The frontend is prebuilt in `frontend/dist`, so no build step is needed (only run `cd frontend && npm run build` first if you changed the frontend). To use a named workspace profile, add `-p <profile>` or set `DATABRICKS_PROFILE=<profile>`.

### Alternative: override in `databricks.yml`

Instead of passing `--var` flags each time, add a target block to `databricks.yml`:

```yaml
targets:
  prod:
    variables:
      catalog: my_catalog
      metrics_schema: dqap
      warehouse_id: "abc123def456"
      lakebase_instance: dqap-prod
      app_service_principal: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

Then deploy with `databricks bundle deploy -t prod`.

### App process environment (`app.yaml`)

Two values in `app.yaml` are read by the running app process — edit these to match your deployment:

| env var | Default | Notes |
|---|---|---|
| `LAKEBASE_INSTANCE_NAME` | `dqap-accelerator` | Must match `lakebase_instance`; used to mint short-lived OAuth credentials |
| `WAREHOUSE_ID` | _(set your own)_ | Must match `warehouse_id`; used to execute `measurement_sql` queries |

---

## 3. The one manual step — grant the app SP its Postgres role

The `dqap` UC schema and its `USE_SCHEMA` / `CREATE_TABLE` grants are handled automatically by the bundle. However, one grant is a **Postgres-internal operation** against the Lakebase instance — it cannot be expressed as a Databricks bundle resource, so it must be run once by the Lakebase instance admin.

### Why this is needed

Lakebase is a managed PostgreSQL service. The app service principal connects using a short-lived OAuth token translated to a Postgres role. Postgres schema-level `USAGE` and `CREATE` privileges are granted within Postgres itself, not via Unity Catalog, so no DAB resource can express them.

### Run once as the Lakebase instance admin

Connect to the Lakebase instance using its `read_write_dns` hostname (found under **Compute** → **Databases** → your instance → connection details):

```bash
psql "host=<read_write_dns> dbname=databricks_postgres user=<admin-user> sslmode=require"
```

Then run — substituting your SP client ID for `<app-sp-client-id>`:

```sql
GRANT USAGE, CREATE ON SCHEMA public TO "<app-sp-client-id>";
GRANT ALL ON ALL TABLES IN SCHEMA public TO "<app-sp-client-id>";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "<app-sp-client-id>";
```

> The SP client ID is the UUID value of `app_service_principal`. To confirm the client ID used by the running app: `databricks apps get dqap-accelerator | grep service_principal`.

**Timing:** Apply this grant between pass 1 and pass 2 (§4). If the app's first boot fails with *permission denied for schema public*, apply the grant and redeploy — a stop/start alone is not sufficient because bootstrap only runs on deploy.

---

## 4. Deploy (two passes)

A Databricks App's **service principal is created together with the app** — you don't pre-create it, and its client ID doesn't exist until the app does. Because the daily job's `run_as` and the UC schema grant target that SP, deploy in two passes.

### Pass 1 — create the app (mints its service principal)

```bash
databricks apps create dqap-accelerator
```

Then read the auto-created SP's client ID — this is your `app_service_principal` for pass 2:

```bash
databricks apps get dqap-accelerator | grep service_principal
```

### Grant the SP its Postgres role

Apply the one-time Lakebase grant from **§3** using that client ID (and the deploying-user `servicePrincipal.user` role from **§1**, which also applies to this SP).

### Pass 2 — deploy everything, bound to the SP

```bash
databricks bundle deploy \
  --var app_service_principal=<client-id-from-pass-1> \
  --var warehouse_id=<your-warehouse-id> \
  --var catalog=<your-catalog> \
  --var metrics_schema=dqap \
  --var lakebase_instance=dqap-accelerator
```

This deploys the app code and provisions the rest, all bound to the app SP:

| Resource | Name | Notes |
|---|---|---|
| Databricks App | `dqap-accelerator` | Created in pass 1; pass 2 deploys the code |
| Lakebase Database Instance | `<lakebase_instance>` | CU_1 managed Postgres; created if absent |
| UC Schema | `<catalog>.<metrics_schema>` | `USE_SCHEMA` + `CREATE_TABLE` granted to the app SP |
| Daily Job | `dqap-measure-refresh` | Two tasks, unpaused, 06:00 Europe/London, `run_as` the app SP |

> If pass 2 reports the app already exists (it was created in pass 1), deploy the app code with `databricks apps deploy dqap-accelerator --source-code-path <synced path>` and let the bundle manage the schema + job.

---

## 5. First boot — self-install and seed

On first deploy the app bootstraps its own tables and (optionally) seeds the UK Ship Register worked example. This is controlled by two env vars in `app.yaml`:

| Variable | First-boot value | After first boot |
|---|---|---|
| `RUN_SETUP_ON_START` | `true` | Set to `false` |
| `SEED_ON_START` | `true` | Set to `false` |

The bootstrap call is idempotent (`reset=False`) — it creates any missing tables but never drops existing data. Setting `RUN_SETUP_ON_START=false` after the first boot is good practice but will not wipe data if left on.

**To start empty** (no seed data for your own organisation): set `SEED_ON_START=false` before the first deploy.

After the first successful boot, edit `app.yaml` to set both flags to `false` and redeploy:

```bash
# Edit app.yaml: RUN_SETUP_ON_START -> false, SEED_ON_START -> false
databricks bundle deploy
```

---

## 6. Verify the deployment

1. **Open the app URL** — find it under **Apps** → **dqap-accelerator** in the Databricks workspace UI. You should see the DQAP dashboard with the GOV.UK-blue data-quality tick favicon.
2. **Run the job once to verify end-to-end connectivity:**
   ```bash
   databricks bundle run dqap_measure_refresh
   ```
   Both tasks (`run_measures` → `sync_to_uc`) should complete successfully.
3. **Confirm UC tables were written:**
   ```sql
   SELECT count(*) FROM <catalog>.<metrics_schema>.data_assets;
   -- Should return > 0 rows after first successful run
   ```
   All 7 app tables are mirrored: `data_assets`, `quality_rules`, `measurements`, `issues`, `actions`, `asset_step_status`, `asset_tables`.
4. **Confirm the favicon renders** — the browser tab should show the GOV.UK-blue data-quality tick favicon.

---

## 7. What runs on a schedule

The `dqap_measure_refresh` job runs **daily at 06:00 Europe/London** (`0 0 6 * * ?` in Quartz cron notation). It has two sequential tasks:

| Task | Script | What it does |
|---|---|---|
| `run_measures` | `jobs/run_measures.py` | Executes each rule's `measurement_sql` against the SQL warehouse and writes results to Lakebase |
| `sync_to_uc` | `jobs/sync_to_uc.py` | Mirrors all 7 Lakebase tables to `<catalog>.<metrics_schema>.*` in Unity Catalog |

Both tasks run as the `app_service_principal`.

### Changing the cadence

Edit `databricks.yml` and redeploy:

```yaml
jobs:
  dqap_measure_refresh:
    schedule:
      quartz_cron_expression: "0 0 8 * * ?"   # 08:00 UTC instead
      timezone_id: "UTC"
      pause_status: UNPAUSED
```

### Pausing the schedule

Set `pause_status: PAUSED` in `databricks.yml` and redeploy:

```yaml
      pause_status: PAUSED
```

Or pause it directly from the Databricks Jobs UI without touching the bundle.

---

## 8. Monitoring over time

Once the daily job is running, the `<catalog>.<metrics_schema>.*` tables are queryable from any Databricks SQL tool:

- **`measurements`** (with `measured_at` timestamp) is the primary time series — use it to trend quality scores per rule, asset, or dimension over time.
- All 7 tables are ready for a **Lakeview dashboard** — connect a Databricks SQL warehouse to `<catalog>.<metrics_schema>` and build charts directly.
- Tables can also serve as the input to **Lakehouse Monitoring** for statistical drift detection on quality scores.

Example trend query:

```sql
SELECT
    da.name          AS asset,
    qr.dimension,
    m.measured_at::date AS day,
    AVG(m.score)     AS avg_score
FROM measurements m
JOIN quality_rules qr ON qr.id = m.rule_id
JOIN data_assets   da ON da.id = qr.asset_id
WHERE m.measured_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
```

Run this against `<catalog>.<metrics_schema>` (Unity Catalog) or directly against the Lakebase instance for the latest unmirrored data.
