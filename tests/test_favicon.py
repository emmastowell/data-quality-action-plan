import pathlib
import xml.etree.ElementTree as ET

_PUBLIC = pathlib.Path(__file__).resolve().parents[1] / "frontend" / "public" / "favicon.svg"
_DIST = pathlib.Path(__file__).resolve().parents[1] / "frontend" / "dist" / "favicon.svg"


def test_favicon_is_wellformed_svg():
    root = ET.fromstring(_PUBLIC.read_text())
    assert root.tag.endswith("svg")


def test_favicon_uses_govuk_blue():
    text = _PUBLIC.read_text().lower()
    assert "#1d70b8" in text


def test_favicon_is_self_contained():
    text = _PUBLIC.read_text().lower()
    # no external resource references — inline only
    assert "<image" not in text
    assert "xlink:href" not in text
    assert 'href="http' not in text
    assert 'src="http' not in text
    assert "url(http" not in text


def test_dist_matches_public_after_build():
    assert _DIST.exists(), "run `npm run build` in frontend/ to regenerate dist"
    assert _DIST.read_text() == _PUBLIC.read_text()
