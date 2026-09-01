"""Streamlit Judge Audit App Entrypoint for Unified Recovery Engine.

Launch command:
    streamlit run ui_app.py
"""

from app.ui.dashboard import render_dashboard

if __name__ == "__main__":
    render_dashboard()
