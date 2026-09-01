"""Smoke test verifying application package import and initial package metadata."""

import app


def test_app_import_and_version():
    """Verify that the core `app` package imports cleanly and exports a version string."""
    assert hasattr(app, "__version__")
    assert isinstance(app.__version__, str)
    assert app.__version__ == "0.1.0"
