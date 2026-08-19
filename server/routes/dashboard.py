from fastapi import APIRouter
from server.db import get_conn_ctx
from server.models import DashboardSummary
from server.repositories.dashboard import dashboard_summary

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard():
    with get_conn_ctx() as conn:
        return dashboard_summary(conn)
