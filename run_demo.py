"""Command-Line Demo Launcher for Unified Recovery Engine.

Executes environment verification and launches the Streamlit Judge Audit App.

Usage:
    python run_demo.py
"""

import os
import subprocess
import sys


def main():
    print("=" * 70)
    print(" UNIFIED RECOVERY ENGINE — JUDGE DEMO LAUNCHER")
    print("=" * 70)
    print("1. Running Environment & Quality Gate Verification...")

    # Run verification script
    verify_script = os.path.join("scripts", "verify_environment.py")
    res = subprocess.run([sys.executable, verify_script])
    if res.returncode != 0:
        print("❌ Environment verification failed. Please inspect requirements.")
        sys.exit(1)

    print("\n2. Environment Verified. Launching Streamlit Judge App...")
    print("   URL: http://localhost:8501")
    print("   Press Ctrl+C to stop the dashboard.\n")

    subprocess.run([sys.executable, "-m", "streamlit", "run", "ui_app.py"])


if __name__ == "__main__":
    main()
