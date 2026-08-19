import pathlib
import yaml

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BUNDLE = _ROOT / "databricks.yml"
_DEPLOY = _ROOT / "docs" / "DEPLOY.md"


def test_deploy_doc_exists():
    assert _DEPLOY.exists()


def test_every_bundle_variable_is_documented():
    variables = yaml.safe_load(_BUNDLE.read_text())["variables"]
    text = _DEPLOY.read_text()
    missing = [name for name in variables if name not in text]
    assert not missing, f"undocumented bundle variables: {missing}"


def test_deploy_doc_covers_the_manual_postgres_grant_and_bundle_deploy():
    text = _DEPLOY.read_text().lower()
    assert "databricks bundle deploy" in text
    assert "grant" in text and "schema public" in text  # the one manual Lakebase grant
