import os

IS_DATABRICKS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))
ASSESSMENT_PROVIDER = os.environ.get("ASSESSMENT_PROVIDER", "manual")
