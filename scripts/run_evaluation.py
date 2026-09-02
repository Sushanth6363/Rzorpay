"""Batch Evaluation Entrypoint — produces the submission's measured outcome artifact.

Runs the pre-registered arm comparison over a deterministic synthetic batch and writes
`results/report.json` plus a human-readable `results/RESULTS.md`.

INVARIANTS:
1. DETERMINISTIC: same --seeds, --events and --reference-timestamp produce a byte-identical
   batch, verified by `batch_content_hash`. No wall-clock reads enter the batch.
2. IDENTICAL INPUTS ACROSS ARMS: every arm consumes the same event list. The batch hash is
   recorded so baseline fairness is provable rather than asserted (07_EXPERIMENT_METHODOLOGY).
3. INTEGER PAISE: all monetary values are integers. No floats enter the batch.
4. SYNTHETIC PROVENANCE: every figure produced here describes an authored simulation.
   No claim of production recovery uplift is made or supported by this artifact.
5. NO FABRICATION: results are whatever the runner computes, including INCONCLUSIVE and
   INSUFFICIENT_SAMPLE verdicts. Nothing is tuned to produce a favourable verdict.

Usage:
    python scripts/run_evaluation.py
    python scripts/run_evaluation.py --events 200 --seeds 21-40
    python scripts/run_evaluation.py --out results/report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.domain.enums import EventType  # noqa: E402
from app.experiment.runner import ExperimentRunner  # noqa: E402

# --- Batch generation parameters (authored; see docs/EXPERIMENT_METHODOLOGY.md) -------------
FAILURE_REASONS = [
    "INSUFFICIENT_FUNDS",
    "PAYMENT_METHOD_FAILURE",
    "AUTHENTICATION_FAILURE",
    "EXPIRED_METHOD",
    "GATEWAY_FAILURE",
]
# Amount bands in integer paise. Right-skewed, as real recovery populations are.
AMOUNT_BANDS_PAISE = [
    (50_000, 200_000),      # Rs 500 - Rs 2,000
    (200_000, 1_000_000),   # Rs 2,000 - Rs 10,000
    (1_000_000, 5_000_000),  # Rs 10,000 - Rs 50,000
]
AMOUNT_BAND_WEIGHTS = [0.55, 0.35, 0.10]
MERCHANTS = ["merch_alpha", "merch_beta"]

# Batch composition. Declared here and echoed into the report, because an ablation can
# only measure a capability if the batch contains cases that capability acts on.
PHANTOM_SHARE = 0.15    # already-paid: Stage 0 gate should decline to chase these
OUTAGE_SHARE = 0.15     # inside a gateway outage: downtime signal should suppress
OUTAGE_GATEWAY = "razorpay_outage_sim"


def parse_seeds(spec: str) -> List[int]:
    """Parse '21-40' or '21,22,23' into a seed list."""
    spec = spec.strip()
    if "-" in spec and "," not in spec:
        lo, hi = spec.split("-", 1)
        return list(range(int(lo), int(hi) + 1))
    return [int(s) for s in spec.split(",") if s.strip()]


def generate_batch(
    num_events: int,
    batch_seed: int,
    reference_timestamp: str,
) -> List[Dict[str, Any]]:
    """Generate a deterministic synthetic opportunity batch.

    Determinism: one RNG substream per event, keyed by (batch_seed, index), so generation
    is order-independent and reproducible across processes and calendar days.
    """
    events: List[Dict[str, Any]] = []
    for i in range(num_events):
        stream = hashlib.sha256(f"{batch_seed}|evt_{i}".encode()).hexdigest()
        rng = random.Random(int(stream[:16], 16))

        merchant_id = MERCHANTS[rng.randrange(len(MERCHANTS))]
        band = rng.choices(AMOUNT_BANDS_PAISE, weights=AMOUNT_BAND_WEIGHTS, k=1)[0]
        amount_paise = rng.randrange(band[0], band[1])  # int paise, never float

        event: Dict[str, Any] = {
            "merchant_id": merchant_id,
            "customer_id": f"cust_{i % max(1, num_events // 3):04d}",
            "event_id": f"evt_{i:05d}",
            "event_type": EventType.FAILED_PAYMENT.value,
            "amount_paise": amount_paise,
            "currency": "INR",
            "occurred_at": reference_timestamp,
            "failure_reason": FAILURE_REASONS[rng.randrange(len(FAILURE_REASONS))],
            "gateway": "razorpay",
        }

        # The batch MUST contain the cases each ablation is meant to catch, or the
        # comparison measures nothing. Composition is fixed and declared in the report.
        draw = rng.random()
        if draw < PHANTOM_SHARE:
            # Already paid before any decision. Only an arm with the Stage 0 GATE
            # active declines to chase this -> makes A2 vs A2ns measurable.
            event["is_paid"] = True
            event["paid_at"] = reference_timestamp
            event["payment_status"] = "SUCCESS"
            event["batch_case"] = "PHANTOM_ALREADY_PAID"
        elif draw < PHANTOM_SHARE + OUTAGE_SHARE:
            # Failure occurring inside a gateway outage window, but reported with an
            # ORDINARY failure code. This is the only case where the downtime signal is
            # worth anything: if the error already said GATEWAY_FAILURE, any scorer that
            # respects the diagnosis reaches the same decision without the signal, and
            # A3 vs A2 measures zero. The signal earns its place precisely when the
            # outage is NOT evident from the error code (the narrow form of D2:
            # detection is not the gap - consuming it at the recovery layer is).
            event["failure_reason"] = "INSUFFICIENT_FUNDS"
            event["gateway"] = OUTAGE_GATEWAY
            event["batch_case"] = "OUTAGE_MASKED_AS_ORDINARY_FAILURE"
        else:
            event["batch_case"] = "GENUINE_FAILURE"

        events.append(event)
    return events


def canonical_hash(obj: Any) -> str:
    """SHA-256 over canonical JSON: sorted keys, no whitespace drift, integers only."""
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def git_commit() -> str:
    """Real commit hash, never hardcoded. Returns UNKNOWN if unavailable."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return "UNKNOWN"


def git_dirty() -> bool:
    """True if the working tree has uncommitted changes (results would not be reproducible)."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
        )
        return bool(out.stdout.strip())
    except Exception:
        return False


def package_versions() -> Dict[str, str]:
    versions: Dict[str, str] = {}
    for name in ("numpy", "pandas", "scipy", "sklearn", "catboost"):
        try:
            mod = __import__(name)
            versions[name] = getattr(mod, "__version__", "unknown")
        except Exception:
            versions[name] = "not installed"
    return versions


def rupees(paise: int) -> str:
    return f"Rs {paise / 100:,.2f}"


def render_markdown(report: Dict[str, Any]) -> str:
    """Human-readable results, with the synthetic caveat attached to every figure block."""
    env = report["environment"]
    prov = report["provenance"]
    primary = report["primary_comparison"]

    lines: List[str] = []
    lines.append("# EVALUATION RESULTS — Unified Recovery Engine")
    lines.append("")
    lines.append("> **All figures below were produced under the synthetic data-generating process.**")
    lines.append("> Interventions, customer responses and recovery outcomes are simulated. This")
    lines.append("> artifact does not measure, and cannot measure, real Razorpay recovery uplift.")
    lines.append("")
    lines.append("## Provenance")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| Generated at | {report['generated_at']} |")
    lines.append(f"| Commit | `{prov['commit_hash']}`{' **(DIRTY WORKING TREE)**' if prov['working_tree_dirty'] else ''} |")
    lines.append(f"| Batch content hash | `{prov['batch_content_hash'][:16]}…` |")
    lines.append(f"| Dataset type | {prov['dataset_type']} |")
    lines.append(f"| Events | {report['config']['num_events']} |")
    lines.append(f"| Seeds | {report['config']['seeds'][0]}–{report['config']['seeds'][-1]} (n={len(report['config']['seeds'])}) |")
    lines.append(f"| Reference timestamp | {report['config']['reference_timestamp']} |")
    lines.append(f"| Python | {env['python_version'].split()[0]} |")
    lines.append("")
    lines.append("## Arm metrics")
    lines.append("")
    lines.append("| Arm | Opportunities | Recoveries | Recovery rate | Attributed | Self-cured | Abstentions |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for arm, m in report["arm_metrics"].items():
        lines.append(
            f"| {arm} | {m['total_opportunities']} | {m['successful_recoveries']} | "
            f"{m['recovery_rate']:.4f} | {rupees(m['attributed_recovered_paise'])} | "
            f"{m['self_cured_count']} | {m.get('abstention_count', 0)} |"
        )
    lines.append("")
    lines.append("## Contact efficiency")
    lines.append("")
    lines.append("> Recovery rate alone cannot show what this engine is for. Every safety control")
    lines.append("> suppresses a contact, so on that metric more safety can only ever look worse.")
    lines.append("> The claim is *comparable recovery for materially fewer customer contacts* —")
    lines.append("> which is what this table measures.")
    lines.append("")
    lines.append("| Arm | Outbound contacts | Contacts / customer | Recovery per contact | Contact rate |")
    lines.append("|---|---:|---:|---:|---:|")
    for arm, m in report["arm_metrics"].items():
        lines.append(
            f"| {arm} | {m.get('outbound_contacts', 0)} | {m.get('contacts_per_customer', 0):.2f} | "
            f"{rupees(int(m.get('recovery_per_contact_paise', 0)))} | {m.get('contact_rate', 0):.1%} |"
        )
    lines.append("")
    lines.append("An outbound contact is a customer-facing message that was actually executed. "
                 "`RECOMMEND_RETRY` is excluded: it is a recommendation to the payment "
                 "infrastructure, not a message to a person.")
    lines.append("")
    lines.append("## Primary comparison — PRE-REGISTERED")
    lines.append("")
    lines.append(f"**{primary['comparison_id']}** · metric: incremental recovery rate · unit of analysis: opportunity")
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append(f"| Treatment rate | {primary['treatment_recovery_rate']:.4f} |")
    lines.append(f"| Baseline rate | {primary['baseline_recovery_rate']:.4f} |")
    lines.append(f"| **Incremental recovery rate** | **{primary['incremental_recovery_rate']:+.4f}** |")
    lines.append(f"| 95% CI | [{primary['confidence_interval_95'][0]:.4f}, {primary['confidence_interval_95'][1]:.4f}] |")
    lines.append(f"| p-value | {primary['p_value']:.4f} |")
    lines.append(f"| **Verdict** | **{primary['status']}** |")
    lines.append("")
    lines.append(f"> {primary['explanation']}")
    lines.append("")
    lines.append("## Secondary comparisons — Holm-Bonferroni corrected")
    lines.append("")
    lines.append("| Comparison | Incremental rate | 95% CI | p | Verdict |")
    lines.append("|---|---:|---|---:|---|")
    for c in report["secondary_comparisons"]:
        ci = c["confidence_interval_95"]
        lines.append(
            f"| {c['comparison_id']} | {c['incremental_recovery_rate']:+.4f} | "
            f"[{ci[0]:.4f}, {ci[1]:.4f}] | {c['p_value']:.4f} | {c['status']} |"
        )
    lines.append("")
    lines.append("## What this does not show")
    lines.append("")
    lines.append("- Real Razorpay recovery uplift · real payer-response accuracy · production ROI")
    lines.append("- Confidence intervals quantify sampling error **within the simulation only**.")
    lines.append("  They say nothing about distance from a real-world value.")
    lines.append("- An `INCONCLUSIVE` verdict means the difference is unresolved at this sample")
    lines.append("  size. It is **not** evidence of no effect.")
    lines.append("")
    lines.append("## Reproduce")
    lines.append("")
    lines.append("```bash")
    lines.append(f"python scripts/run_evaluation.py --events {report['config']['num_events']} "
                 f"--seeds {report['config']['seeds'][0]}-{report['config']['seeds'][-1]}")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the batch evaluation and write results.")
    parser.add_argument("--events", type=int, default=120, help="opportunities in the batch")
    parser.add_argument("--seeds", type=str, default="21-30", help="e.g. 21-40 or 21,22,23")
    parser.add_argument("--batch-seed", type=int, default=42, help="seed for batch generation")
    parser.add_argument("--reference-timestamp", type=str, default="2026-01-01T00:00:00+00:00")
    parser.add_argument("--experiment-id", type=str, default="E001_PRIMARY_A2_VS_A1")
    parser.add_argument("--out", type=str, default="results/report.json")
    args = parser.parse_args()

    seeds = parse_seeds(args.seeds)
    if not seeds:
        print("ERROR: no seeds parsed", file=sys.stderr)
        return 2

    print(f"[1/4] Generating deterministic batch: {args.events} events, batch_seed={args.batch_seed}")
    events = generate_batch(args.events, args.batch_seed, args.reference_timestamp)
    batch_hash = canonical_hash(events)
    print(f"      batch_content_hash = {batch_hash[:32]}...")

    commit = git_commit()
    dirty = git_dirty()
    if dirty:
        print("      WARNING: working tree is dirty — this run is not reproducible from the commit alone")

    print(f"[2/4] Running arms across {len(seeds)} seeds (identical batch per arm)")
    runner = ExperimentRunner(experiment_id=args.experiment_id)
    summary = runner.run_paired_experiment(
        events=events,
        seeds=seeds,
        commit_hash=commit,
        dataset_version=f"synthetic-batch-{batch_hash[:8]}",
    )

    print("[3/4] Assembling report")
    report = summary.to_dict()
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["config"] = {
        "num_events": args.events,
        "seeds": seeds,
        "batch_seed": args.batch_seed,
        "reference_timestamp": args.reference_timestamp,
        "experiment_id": args.experiment_id,
        "batch_composition": {
            "phantom_already_paid_share": PHANTOM_SHARE,
            "gateway_outage_share": OUTAGE_SHARE,
            "genuine_failure_share": round(1.0 - PHANTOM_SHARE - OUTAGE_SHARE, 4),
        },
    }
    report["provenance"] = {
        "commit_hash": commit,
        "working_tree_dirty": dirty,
        "batch_content_hash": batch_hash,
        "dataset_type": "SYNTHETIC",
        "identical_batch_across_arms": True,
        "disclosure": (
            "All interventions, customer responses and recovery outcomes are synthetic. "
            "Figures describe an authored data-generating process and do not measure "
            "real-world recovery uplift."
        ),
    }
    report["environment"] = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "packages": package_versions(),
    }

    out_path = REPO_ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    md_path = out_path.parent / "RESULTS.md"
    md_path.write_text(render_markdown(report), encoding="utf-8")

    print(f"[4/4] Wrote {out_path.relative_to(REPO_ROOT)} and {md_path.relative_to(REPO_ROOT)}")
    print()

    p = report["primary_comparison"]
    ci = p["confidence_interval_95"]
    print("=" * 70)
    print(f"PRIMARY  {p['comparison_id']}  (pre-registered)")
    print(f"  incremental recovery rate : {p['incremental_recovery_rate']:+.4f}")
    print(f"  95% CI                    : [{ci[0]:.4f}, {ci[1]:.4f}]")
    print(f"  p-value                   : {p['p_value']:.4f}")
    print(f"  VERDICT                   : {p['status']}")
    print("=" * 70)
    print("All figures under the synthetic data-generating process. Not production evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
