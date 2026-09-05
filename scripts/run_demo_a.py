#!/usr/bin/env python3
"""DEMO A — merchant CSV to a real PAY NOW email, through the real engine.

WHAT THIS DOES
    1. validates a merchant CSV, showing every rejected row and why
    2. creates durable Customers and Cases
    3. runs the EXISTING Recovery Engine per case - Stage 0, diagnosis, candidates,
       safety filter, escalation ceiling, EV ranking
    4. creates a real Razorpay TEST Payment Link for whatever it decided to send
    5. dispatches through ChannelDispatcher, which re-reads case state first
    6. schedules the next review
    7. prints the case timeline

    It then waits. The loop CLOSES when the customer pays and Razorpay's webhook reaches
    the running server - which is the point, and the reason this script does not pretend
    to close it itself.

SAFETY
    Dry run unless --send is passed AND RECOVERY_DISPATCH_ENABLED=true. Both are required:
    a flag alone cannot start emailing people, and neither can an env var left set from a
    previous session.

Usage:
    python scripts/run_demo_a.py --csv demo_customers.csv            # dry run
    python scripts/run_demo_a.py --csv demo_customers.csv --send     # really sends
    python scripts/run_demo_a.py --watch                             # tail case states
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app import config_env  # noqa: E402,F401  (loads .env)

from app.agent.loop import RecoveryAgent  # noqa: E402
from app.cases.csv_ingest import create_cases, parse_csv  # noqa: E402
from app.cases.models import CaseStatus  # noqa: E402
from app.cases.repository import CaseRepository  # noqa: E402
from app.dispatch.dispatcher import ChannelDispatcher  # noqa: E402
from app.realtime import config, ingest  # noqa: E402

RULE = "=" * 78


def rupees(paise: int) -> str:
    return f"Rs {paise / 100:,.2f}"


def show_posture(sending: bool) -> None:
    print(RULE)
    print(" DEMO A - CSV -> agent -> payment link -> email -> webhook -> case closed")
    print(RULE)
    posture = config.describe()
    print(f"  database        : {posture['db_path']}")
    print(f"  dispatch enabled: {posture['dispatch_enabled']}")
    print(f"  webhook secret  : {'configured' if posture['webhook_secret_configured'] else 'MISSING'}")
    print(f"  this run        : {'SENDING REAL MESSAGES' if sending else 'DRY RUN - nothing is sent'}")
    print()


def ingest_csv(path: Path, repo: CaseRepository, merchant_id: str):
    report = parse_csv(path.read_bytes())

    if report.missing_columns:
        print(f"  CSV REFUSED - missing required column(s): {', '.join(report.missing_columns)}")
        print("  Expected: customer_id, name, email, phone, amount, due_date")
        return []

    print(f"  {len(report.valid)} valid row(s), {rupees(report.total_paise)} at risk")
    for row in report.valid:
        overdue = f"{row.days_overdue}d overdue" if row.days_overdue else "not yet due"
        print(f"    line {row.line}: {row.name or '(no name)':18s} {row.email or row.phone:26s} "
              f"{rupees(row.amount_paise):>14s}  {overdue}")

    if report.rejected:
        print()
        print(f"  {len(report.rejected)} row(s) REJECTED - shown, never silently dropped:")
        for bad in report.rejected:
            print(f"    line {bad.line}: {bad.reason}")

    print()
    return create_cases(repo, report.valid, merchant_id=merchant_id)


def run_agent(agent: RecoveryAgent, repo: CaseRepository, cases) -> None:
    for case in cases:
        customer = repo.get_customer(case.merchant_id, case.customer_id)
        name = (customer.name if customer else "") or case.customer_id
        print(f"  -- {name} · {rupees(case.amount_paise)} " + "-" * 30)

        result = agent.run_cycle(case.case_id)

        if result.skipped_reason and not result.action:
            print(f"     skipped: {result.skipped_reason}")
            print()
            continue

        print(f"     decision : {result.action}")
        print(f"     why      : {result.reasoning}")
        if result.payment_url:
            print(f"     PAY NOW  : {result.payment_url}")
        status = result.dispatch.get("status", "-")
        print(f"     dispatch : {status} - {result.dispatch.get('reason', '')}")
        if result.skipped_reason:
            print(f"     note     : {result.skipped_reason}")
        print()


def show_timelines(repo: CaseRepository, cases) -> None:
    print(RULE)
    print(" CASE TIMELINES")
    print(RULE)
    for case in cases:
        current = repo.get_case(case.case_id)
        print(f"  {case.case_id[:52]}  [{current.status.value}]")
        for event in repo.timeline(case.case_id):
            print(f"     {event.at[11:19]}  {event.kind.value:22s} {event.summary}")
        print()


def watch(repo: CaseRepository, merchant_id: str, seconds: int = 600) -> int:
    """Poll case states until everything is settled, or the time runs out.

    The webhook closes cases from the SERVER process; this only observes. If nothing
    changes when you pay, the problem is the webhook registration, not the engine - and
    scripts/send_test_webhook.py will tell you which.
    """
    print(RULE)
    print(f" WATCHING for payment webhooks (up to {seconds}s). Ctrl+C to stop.")
    print(" Pay a PAY NOW link above with Razorpay's TEST card 4111 1111 1111 1111.")
    print(RULE)
    seen: dict = {}
    deadline = time.time() + seconds

    while time.time() < deadline:
        settled = 0
        for case in repo.list_cases(merchant_id):
            if seen.get(case.case_id) != case.status:
                stamp = time.strftime("%H:%M:%S")
                print(f"  {stamp}  {case.customer_id:14s} {rupees(case.amount_paise):>14s}  "
                      f"-> {case.status.value}")
                seen[case.case_id] = case.status
            if case.status in (CaseStatus.PAID, CaseStatus.CLOSED):
                settled += 1
        if seen and settled == len(seen):
            print()
            print("  All cases settled. CASE CLOSED.")
            return 0
        time.sleep(3)

    print()
    print("  Timed out. If you paid and nothing changed, check in this order:")
    print("    1. is the tunnel window still open?")
    print("    2. was the webhook registered in TEST mode?")
    print("    3. python scripts/send_test_webhook.py --url <tunnel>   (should be 200)")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=str, default="", help="path to the merchant CSV")
    parser.add_argument("--send", action="store_true",
                        help="really send. ALSO requires RECOVERY_DISPATCH_ENABLED=true")
    parser.add_argument("--merchant", type=str, default="merch_demo")
    parser.add_argument("--watch", action="store_true", help="watch for payment webhooks")
    parser.add_argument("--watch-seconds", type=int, default=600)
    args = parser.parse_args()

    # BOTH gates. A flag alone cannot start emailing people, and neither can a stale env var.
    sending = args.send and config.DISPATCH_ENABLED
    show_posture(sending)

    if args.send and not config.DISPATCH_ENABLED:
        print("  --send was passed but RECOVERY_DISPATCH_ENABLED is not true.")
        print("  Set it in .env and re-run. Running as a DRY RUN for now.")
        print()

    conn = ingest.get_conn()
    repo = CaseRepository(conn)
    agent = RecoveryAgent(
        conn, repository=repo,
        dispatcher=ChannelDispatcher(conn, repository=repo, dry_run=not sending),
    )

    cases = []
    if args.csv:
        path = Path(args.csv)
        if not path.exists():
            print(f"  ERROR: {path} not found")
            return 2
        print(f"  Reading {path}")
        cases = ingest_csv(path, repo, args.merchant)
        if not cases:
            return 1
        print(RULE)
        print(" AGENT DECISIONS")
        print(RULE)
        run_agent(agent, repo, cases)
        show_timelines(repo, cases)

    if args.watch or (cases and sending):
        return watch(repo, args.merchant, args.watch_seconds)

    if cases and not sending:
        print("  DRY RUN complete. To send for real:")
        print("    1. set RECOVERY_DISPATCH_ENABLED=true in .env")
        print("    2. re-run with --send")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
