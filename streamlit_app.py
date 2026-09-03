"""Streamlit Community Cloud Root Entrypoint for Unified Recovery Engine."""

import sys
import os

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.ui.dashboard import render_dashboard

if __name__ == "__main__":
    render_dashboard()
else:
    # Called when Streamlit imports the file directly
    render_dashboard()
