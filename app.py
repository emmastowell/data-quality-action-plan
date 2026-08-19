import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse

from server.config import IS_DATABRICKS_APP
from server.errors import install_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    if IS_DATABRICKS_APP:
        from server.db import init_pool, get_conn_ctx
        init_pool().open(wait=True, timeout=30.0)
        from server.bootstrap import maybe_bootstrap
        with get_conn_ctx() as conn:
            print("bootstrap:", maybe_bootstrap(conn))
    yield
    from server.db import pool
    if pool is not None:
        pool.close()


app = FastAPI(title="DQAP Accelerator", lifespan=lifespan)
install_handlers(app)


@app.get("/api/health")
def health():
    return {"status": "ok"}


from server.routes import assets, rules, measurements, issues, actions, dashboard, export, asset_tables, uc, raci
app.include_router(assets.router, prefix="/api")
app.include_router(rules.router, prefix="/api")
app.include_router(measurements.router, prefix="/api")
app.include_router(issues.router, prefix="/api")
app.include_router(actions.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(asset_tables.router, prefix="/api")
app.include_router(uc.router, prefix="/api")
app.include_router(raci.router, prefix="/api")

# --- SPA static serving (production build) ---
# We use a single catch-all rather than app.mount("/assets", StaticFiles(...))
# because that mount would shadow the React Router client routes that also live
# under /assets/* (e.g. /assets/<uuid>), causing deep-link refreshes to 404.
# The /api/* routers and /api/health are registered above and always win.
_frontend = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend", "dist"))
if os.path.isdir(_frontend):

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        # Serve a real built file when it exists (assets/*.js|css, assets/fonts/*,
        # assets/images/*, favicon.svg); otherwise return index.html so React Router
        # client routes (/assets/:id, /assets/:id/export, ...) resolve on direct load
        # or refresh.
        if full_path:
            candidate = os.path.normpath(os.path.join(_frontend, full_path))
            if candidate.startswith(_frontend + os.sep) and os.path.isfile(candidate):
                return FileResponse(candidate)
        return FileResponse(os.path.join(_frontend, "index.html"))
