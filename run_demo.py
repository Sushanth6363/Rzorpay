"""Command-line demo launcher for the Unified Recovery Engine.

Runs the environment quality gate, then launches the Streamlit judge dashboard.
The gate runs FIRST and a failure aborts the launch, so a dashboard that opens is
always backed by a green suite.

Usage:
    python run_demo.py

Port 8555 is the single canonical demo port across `run_demo.py`, `make demo`, and
the direct `streamlit run` commands in README.md. Do not change it in one place only.

Output is deliberately plain ASCII: this is the judge-facing entrypoint and a legacy
Windows console code page raises UnicodeEncodeError on box-drawing characters and emoji.
"""

import os
import subprocess
import sys

DEMO_PORT = 8555


def main():
    print("=" * 70)
    print(" UNIFIED RECOVERY ENGINE - JUDGE DEMO LAUNCHER")
    print("=" * 70)
    print("1. Running environment & quality gate verification...")

    verify_script = os.path.join("scripts", "verify_environment.py")
    res = subprocess.run([sys.executable, verify_script])
    if res.returncode != 0:
        print("\n[FAILED] Environment verification failed - not launching the dashboard.")
        print("         Run 'python scripts/bootstrap.py' to build a supported .venv,")
        print("         then re-run this launcher with that interpreter.")
        sys.exit(1)

    print("\n2. Environment verified. Launching the Streamlit judge dashboard...")
    print(f"   URL: http://localhost:{DEMO_PORT}")
    print("   Press Ctrl+C to stop.\n")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "ui_app.py",
            "--server.port",
            str(DEMO_PORT),
        ]
    )


if __name__ == "__main__":
    main()
