"""Streamlit Community Cloud root entrypoint for the Unified Recovery Engine.

WHY THIS FILE IS FOUR LINES OF CODE
    It used to render the dashboard in BOTH branches of an if/else:

        if __name__ == "__main__": render_dashboard()
        else:                      render_dashboard()   # "in case Streamlit imports it"

    Two call sites for one render is a duplicated-UI bug waiting for the day both
    conditions are somehow satisfied - and the `else` branch made merely IMPORTING this
    module paint a whole dashboard, so any tool that imported it (a test, a linter, a
    doc builder) would execute the entire app as a side effect.

    A Streamlit entrypoint is meant to render when it is executed. So it renders, once,
    unconditionally, and the file has no branch that can disagree with itself.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.ui.dashboard import render_dashboard  # noqa: E402

render_dashboard()
