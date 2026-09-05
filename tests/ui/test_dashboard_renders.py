"""The dashboard must actually render (ADR-0027).

WHY THIS TEST EXISTS
    A NameError for `SAMPLE_CSV` shipped and reached the screen. Every other test passed,
    because nothing imported the dashboard: its imports live INSIDE the section functions,
    so a missing name is invisible until Streamlit executes that function at render time.

    Parsing the file proves nothing here - the broken code was syntactically perfect. Only
    running the app catches it, so this runs the app.
"""

from pathlib import Path

import pytest

pytest.importorskip("streamlit.testing.v1", reason="requires Streamlit's test harness")

from streamlit.testing.v1 import AppTest  # noqa: E402

# Resolved from THIS file, not the working directory: pytest may be invoked from anywhere
# and a relative path would make the test pass or fail depending on where you stood.
APP = str(Path(__file__).resolve().parents[2] / "app" / "ui" / "dashboard.py")
TIMEOUT = 180


@pytest.fixture(scope="module")
def app():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    return at


def test_the_dashboard_renders_without_raising(app):
    """The whole point: a render-time NameError must fail the suite, not the demo."""
    assert not app.exception, "\n".join(str(e.value) for e in app.exception)


def test_every_tab_is_present(app):
    labels = [t.label for t in app.tabs]

    assert labels == ["Decision trace", "Experiment", "Live test (CSV)", "Safety", "About"]


def test_the_case_board_and_uploader_both_render(app):
    """Both were added at once; either failing silently would gut the demo screen."""
    headings = [m.value for m in app.markdown if m.value.strip().startswith("####")]
    joined = " ".join(headings)

    assert "Case board" in joined
    assert "Upload a merchant CSV" in joined


def test_the_sandbox_disclosure_is_on_screen(app):
    """INV-1 of this file: every screen states that outcomes are simulated."""
    text = " ".join(m.value for m in app.markdown)

    assert "SANDBOX" in text or "SIMULATED DATA" in text


def test_the_safety_checks_actually_executed(app):
    """A tick must mean the check ran on this render, not that a document claims it."""
    text = " ".join(m.value for m in app.markdown)

    assert "INV-7" in text
    assert "executed checks passing" in text
