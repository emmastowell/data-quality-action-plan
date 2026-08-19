from server.errors import AppError, not_found


def test_not_found_builds_404():
    err = not_found("asset")
    assert isinstance(err, AppError) and err.status == 404 and err.code == "not_found"
