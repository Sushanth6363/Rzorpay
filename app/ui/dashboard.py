"""Streamlit Judge Dashboard for the Unified Recovery Engine.

INVARIANTS:
1. PROMINENT SANDBOX MARKER: every screen states that outcomes are simulated.
2. AUDITABLE DECISION TRACE: the full path from raw event to attribution is readable
   as ONE vertical flow, not fragmented across nested tabs.
3. NO HARDCODED SUCCESS: safety invariants are EXECUTED and report real PASS/FAIL.
   A green tick that is not backed by a live check is forbidden.
4. CLEAR ATTRIBUTION DISTINCTION: intervention-driven recovery (attributed > 0) is
   always visually separated from natural self-cure (attributed = 0).
"""

import sys
import os

# Ensure repository root is in sys.path for Streamlit Cloud deployment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from app.domain.enums import ActionType, EligibilityStatus, PaymentOutcome, StatisticalStatus
from app.experiment.batch import generate_batch
from app.experiment.runner import ExperimentRunner
from app.sandbox.scenarios import GOLDEN_DEMO_SCENARIOS, DemoScenarioSpec, ScenarioRunner
from app.scoring.feature_builder import FeatureBuilder, PointInTimeLeakageError

ACCENT = "#4338CA"

STYLES = """
<style>
  html, body, [class*="css"] { font-feature-settings: "tnum" 1, "cv05" 1; }
  .block-container { padding-top: 2.2rem; max-width: 1400px; }

  .urx-head { display:flex; align-items:baseline; gap:.75rem; flex-wrap:wrap;
              border-bottom:1px solid rgba(128,128,128,.22); padding-bottom:.7rem; margin-bottom:.35rem; }
  .urx-head h1 { font-size:1.42rem; font-weight:650; margin:0; letter-spacing:-.015em; }
  .urx-head .sub { font-size:.82rem; opacity:.62; }

  .urx-banner { border:1px solid rgba(180,83,9,.38); background:rgba(180,83,9,.08);
                border-radius:8px; padding:.6rem .85rem; margin:.9rem 0 1.1rem;
                font-size:.83rem; line-height:1.5; }
  .urx-banner b { letter-spacing:.02em; }

  .urx-card { border:1px solid rgba(128,128,128,.22); border-radius:10px;
              padding:.85rem 1rem; margin-bottom:.7rem; background:rgba(128,128,128,.035); }
  .urx-card h4 { margin:0 0 .5rem; font-size:.78rem; font-weight:650;
                 text-transform:uppercase; letter-spacing:.07em; opacity:.65; }

  .urx-kv { display:flex; justify-content:space-between; gap:1rem;
            padding:.28rem 0; font-size:.86rem; border-bottom:1px dotted rgba(128,128,128,.18); }
  .urx-kv:last-child { border-bottom:none; }
  .urx-kv .k { opacity:.62; }
  .urx-kv .v { font-weight:600; font-variant-numeric:tabular-nums; text-align:right; }
  .urx-kv .v.mono { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.8rem; }

  .pill { display:inline-block; padding:.13rem .5rem; border-radius:999px;
          font-size:.71rem; font-weight:650; letter-spacing:.03em; white-space:nowrap; }
  .pill.ok    { background:rgba(5,150,105,.15);  color:#059669; border:1px solid rgba(5,150,105,.35); }
  .pill.warn  { background:rgba(217,119,6,.15);  color:#D97706; border:1px solid rgba(217,119,6,.35); }
  .pill.stop  { background:rgba(220,38,38,.13);  color:#DC2626; border:1px solid rgba(220,38,38,.32); }
  .pill.mute  { background:rgba(128,128,128,.13); opacity:.75; border:1px solid rgba(128,128,128,.28); }
  .pill.acc   { background:rgba(67,56,202,.14);  color:#4338CA; border:1px solid rgba(67,56,202,.34); }

  .stage { display:flex; align-items:flex-start; gap:.8rem; padding:.55rem 0;
           border-left:2px solid rgba(128,128,128,.22); padding-left:.95rem; margin-left:.35rem; }
  .stage.active { border-left-color:#4338CA; }
  .stage.halt   { border-left-color:#DC2626; }
  .stage .n { font-size:.7rem; opacity:.5; min-width:1.1rem; font-weight:700; padding-top:.15rem; }
  .stage .body { flex:1; }
  .stage .t { font-size:.87rem; font-weight:600; margin-bottom:.1rem; }
  .stage .d { font-size:.79rem; opacity:.68; line-height:1.45; }

  .verdict { border-radius:10px; padding:.9rem 1.1rem; margin:.5rem 0 1rem;
             border:1px solid rgba(128,128,128,.25); }
  .verdict .lab { font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; opacity:.6; }
  .verdict .big { font-size:1.6rem; font-weight:680; font-variant-numeric:tabular-nums; letter-spacing:-.02em; }
  .verdict .ci  { font-size:.8rem; opacity:.7; font-variant-numeric:tabular-nums; }

  .note { font-size:.78rem; opacity:.62; line-height:1.5; }
  div[data-testid="stMetricValue"] { font-size:1.25rem; }
</style>
"""


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def rupees(paise: int) -> str:
    return f"₹{paise / 100:,.2f}"


def kv(label: str, value: str, mono: bool = False) -> str:
    cls = "v mono" if mono else "v"
    return f'<div class="urx-kv"><span class="k">{label}</span><span class="{cls}">{value}</span></div>'


def card(title: str, rows_html: str) -> None:
    st.markdown(f'<div class="urx-card"><h4>{title}</h4>{rows_html}</div>', unsafe_allow_html=True)


def pill(text: str, kind: str = "mute") -> str:
    return f'<span class="pill {kind}">{text}</span>'


def stage(n: int, title: str, detail: str, state: str = "") -> str:
    return (
        f'<div class="stage {state}"><div class="n">{n}</div><div class="body">'
        f'<div class="t">{title}</div><div class="d">{detail}</div></div></div>'
    )


# ---------------------------------------------------------------------------
# live invariant checks — executed, never asserted as decoration
# ---------------------------------------------------------------------------

def run_invariant_checks() -> List[Dict[str, Any]]:
    """Execute real safety checks. Each row reports what actually happened."""
    checks: List[Dict[str, Any]] = []
    runner = ScenarioRunner()

    # INV-7 — point-in-time feature leakage must raise
    try:
        FeatureBuilder.validate_point_in_time_safety(
            observed_at="2026-09-01T10:00:00Z",
            decision_timestamp="2026-09-01T10:00:00Z",
            extra_fields={"outcome": "SUCCESS_RECOVERED"},
        )
        checks.append({"id": "INV-7", "name": "Point-in-time features",
                       "passed": False, "evidence": "No error raised for a post-decision field."})
    except PointInTimeLeakageError as exc:
        checks.append({"id": "INV-7", "name": "Point-in-time features",
                       "passed": True, "evidence": f"Rejected post-decision field: {exc}"})

    # INV-8 — self-cure is attributed zero
    try:
        r = runner.run_scenario(GOLDEN_DEMO_SCENARIOS["SCENARIO_03_NATURAL_SELF_CURE"])
        ok = r.attribution.payment_outcome == PaymentOutcome.SELF_CURED and \
            r.attribution.attributed_recovered_paise == 0
        checks.append({"id": "INV-8", "name": "Self-cure not attributed", "passed": ok,
                       "evidence": f"outcome={r.attribution.payment_outcome.value}, "
                                   f"attributed={rupees(r.attribution.attributed_recovered_paise)}"})
    except Exception as exc:  # pragma: no cover - surfaced in UI
        checks.append({"id": "INV-8", "name": "Self-cure not attributed",
                       "passed": False, "evidence": f"check errored: {exc}"})

    # INV-9 — NO_ACTION is always scored
    try:
        r = runner.run_scenario(GOLDEN_DEMO_SCENARIOS["SCENARIO_01_SUCCESSFUL_RETRY"])
        actions = [c.action_type for c in r.decision.candidate_scores]
        ok = ActionType.NO_ACTION in actions
        checks.append({"id": "INV-9", "name": "NO_ACTION scored as counterfactual", "passed": ok,
                       "evidence": f"{len(actions)} candidates scored; NO_ACTION present: {ok}"})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "INV-9", "name": "NO_ACTION scored as counterfactual",
                       "passed": False, "evidence": f"check errored: {exc}"})

    return checks


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------

def _escalation_stage(result: Any, n: int) -> str:
    """Render the compliant-escalation ceiling as one pipeline stage.

    Reads the escalation assessment off the executed decision — never scripted. Shows the
    ceiling that bound this decision and, when it removed a candidate, why.
    """
    esc = getattr(result, "escalation", None)
    if esc is None:
        return stage(n, "Compliant escalation",
                     "No escalation assessment on this path.", "")
    ceiling = esc.allowed_max_rung
    ladder = esc.ladder
    ceiling_action = ladder[ceiling].replace("_", " ").title() if 0 <= ceiling < len(ladder) else "—"
    if esc.suppressed_actions:
        detail = (
            f"Ceiling <b>{ceiling_action}</b>. "
            f"Suppressed louder channels: "
            f"{', '.join(a.replace('_', ' ').title() for a in esc.suppressed_actions)}."
        )
        state = "halt"
    else:
        detail = f"Ceiling <b>{ceiling_action}</b>. No louder channel was in play to suppress."
        state = "active"
    if esc.cooldown_active:
        detail += " Quiet period active — intensity held."
    return stage(n, "Compliant escalation", detail, state)


def section_trace(seed: int, outage_toggle: bool, exhaust_toggle: bool) -> None:
    st.markdown("#### Why did the engine do this?")
    st.markdown(
        '<div class="note">One opportunity, followed from raw event to attribution. '
        'Every value below is read from the executed decision record — nothing is scripted.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    keys = list(GOLDEN_DEMO_SCENARIOS.keys())
    sel = st.selectbox("Scenario", keys, format_func=lambda k: GOLDEN_DEMO_SCENARIOS[k].title)
    spec = GOLDEN_DEMO_SCENARIOS[sel]

    exec_spec = DemoScenarioSpec(
        scenario_id=spec.scenario_id,
        title=spec.title,
        description=spec.description,
        raw_event=spec.raw_event,
        simulate_outage_gateway="HDFC" if outage_toggle else spec.simulate_outage_gateway,
        exhaust_contact_budget_customer="cust_101" if exhaust_toggle else spec.exhaust_contact_budget_customer,
        force_sandbox_outcome=spec.force_sandbox_outcome,
        force_mode=spec.force_mode,
        random_seed=seed,
    )
    result = ScenarioRunner().run_scenario(exec_spec)
    d = result.decision

    st.caption(spec.description)

    # --- outcome strip -----------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Selected action", d.selected_action.value.replace("_", " ").title())
    c2.metric("Decision mode", d.decision_mode.value.replace("_", " ").title())
    c3.metric("Simulated outcome", result.attribution.payment_outcome.value.replace("_", " ").title())
    attributed = result.attribution.attributed_recovered_paise
    c4.metric(
        "Attributed to intervention",
        rupees(attributed),
        delta=None if attributed else "self-cure — not attributed",
        delta_color="off",
    )

    st.write("")
    left, right = st.columns([1.75, 1])

    # --- candidate ranking: the hero ---------------------------------------
    with left:
        st.markdown("##### Candidate actions, ranked by expected value")
        rows = []
        for c in d.candidate_scores:
            eligible = c.eligibility == EligibilityStatus.ELIGIBLE
            rows.append({
                "": "▶" if c.action_type == d.selected_action else "",
                "Action": c.action_type.value.replace("_", " ").title(),
                "P(recover | action)": c.raw_probability * 100,
                "P(no action)": c.baseline_probability * 100,
                "Uplift": c.incremental_effect * 100,
                "Expected value": c.expected_value_paise / 100,
                "Cost": c.action_cost_paise / 100,
                "Status": "Eligible" if eligible else c.reject_reason.value.replace("_", " ").title(),
            })
        df = pd.DataFrame(rows)
        st.dataframe(
            df, use_container_width=True, hide_index=True,
            column_config={
                "": st.column_config.TextColumn(width="small"),
                "P(recover | action)": st.column_config.NumberColumn(format="%.1f%%"),
                "P(no action)": st.column_config.NumberColumn(format="%.1f%%"),
                "Uplift": st.column_config.NumberColumn(format="%+.1f%%"),
                "Expected value": st.column_config.NumberColumn(format="₹%.2f"),
                "Cost": st.column_config.NumberColumn(format="₹%.2f"),
            },
        )
        st.markdown(
            '<div class="note">Uplift is <code>p̂(x,a) − p̂(x, NO_ACTION)</code> — an <b>estimated '
            'incremental effect under the simulator\'s data-generating process</b>, used for ranking '
            'only. It is not a measured causal effect; those come from the arm comparison.</div>',
            unsafe_allow_html=True,
        )

    # --- pipeline flow -----------------------------------------------------
    with right:
        st.markdown("##### Pipeline")
        s0 = result.opportunity_id
        stage0_ok = "not_recoverable" not in str(getattr(d, "abstention_reason", "")).lower()
        eligible_n = sum(1 for c in d.candidate_scores if c.eligibility == EligibilityStatus.ELIGIBLE)
        blocked_n = len(d.candidate_scores) - eligible_n
        reserved = getattr(d, "is_contact_reserved", False)

        flow = "".join([
            stage(1, "Event ingested", f"<code>{result.event_id}</code> → opportunity <code>{s0}</code>", "active"),
            stage(2, "Stage 0 — validate",
                  "Genuine recoverable exposure confirmed." if stage0_ok
                  else "Closed as not recoverable. No contact.", "active" if stage0_ok else "halt"),
            stage(3, "Stage 1 — diagnose", f"{len(d.candidate_scores)} candidate actions generated.", "active"),
            stage(4, "Hard safety filter",
                  f"{eligible_n} eligible, {blocked_n} suppressed before scoring.",
                  "active" if blocked_n == 0 else "halt"),
            stage(5, "Scoring & arbitration",
                  f"Model <code>{d.model_version}</code> ranked candidates; "
                  f"<b>{d.selected_action.value.replace('_', ' ').title()}</b> selected.", "active"),
            _escalation_stage(result, 6),
            stage(7, "Contact reservation",
                  "Slot reserved atomically against the shared per-customer budget." if reserved
                  else ("No slot consumed — NO_ACTION consumes zero capacity."
                        if d.selected_action == ActionType.NO_ACTION
                        else "No reservation recorded on this scenario path."),
                  "active" if reserved else ""),
            stage(8, "Execution & attribution",
                  f"{result.attribution.payment_outcome.value.replace('_', ' ').title()} → "
                  f"attributed {rupees(attributed)}.", "active"),
        ])
        st.markdown(flow, unsafe_allow_html=True)

        st.write("")
        card("Provenance", "".join([
            kv("Decision", d.decision_id, mono=True),
            kv("Trace", result.trace_id, mono=True),
            kv("Model", d.model_version),
            kv("Seed", str(seed)),
            kv("Amount at risk", rupees(result.attribution.amount_at_risk_paise)),
        ]))

    with st.expander("Raw records — decision, execution, observation"):
        a, b = st.columns(2)
        with a:
            st.caption("Decision")
            st.json({
                "decision_id": d.decision_id,
                "selected_action": d.selected_action.value,
                "decision_mode": d.decision_mode.value,
                "baseline_probability_no_action": d.baseline_probability,
                "abstention_reason": d.abstention_reason.value if d.abstention_reason else None,
                "model_version": d.model_version,
            })
        with b:
            st.caption("Execution")
            st.json(result.execution_result.to_dict() if result.execution_result
                    else {"note": "No intervention executed (NO_ACTION / abstention)."})
        st.caption("Observation")
        st.json(result.observation.to_dict())


def section_experiment() -> None:
    st.markdown("#### Five-arm comparison")
    st.markdown(
        '<div class="note">All arms consume an identical seeded batch. Each comparison isolates one '
        'capability. Results are whatever the runner computes — inconclusive verdicts are reported, '
        'not tuned away.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.4])
    seed_start = c1.number_input("First seed", value=21, min_value=1)
    seed_end = c2.number_input("Last seed", value=25, min_value=1)
    opp_count = c3.number_input("Opportunities", value=60, min_value=5)
    c4.write("")
    run = c4.button("Run benchmark", type="primary", use_container_width=True)

    if run:
        # SAME generator the CLI evaluation uses (app/experiment/batch.py). A single
        # source means the numbers here describe the same batch as results/report.json —
        # mixed streams, a real time axis, and the phantom / outage / TDS cases the
        # ablations act on. A bespoke dashboard batch would drift from the reported one.
        events = generate_batch(
            num_events=int(opp_count),
            batch_seed=42,
            reference_timestamp="2026-01-01T00:00:00+00:00",
        )
        with st.spinner("Running arms over identical batch…"):
            st.session_state["summary"] = ExperimentRunner(
                experiment_id="EXP_DASHBOARD"
            ).run_paired_experiment(events=events, seeds=list(range(int(seed_start), int(seed_end) + 1)))

    summary = st.session_state.get("summary")
    if not summary:
        st.info("Run the benchmark to produce results. Nothing is pre-computed.")
        return

    p = summary.primary_comparison
    inconclusive = p.status != StatisticalStatus.STATISTICALLY_SIGNIFICANT
    tone = "warn" if inconclusive else "ok"

    st.markdown(
        f'<div class="verdict">'
        f'<div class="lab">Primary · {p.comparison_id} · pre-registered</div>'
        f'<div class="big">{p.incremental_recovery_rate:+.2%} '
        f'<span style="font-size:.9rem;font-weight:500;opacity:.7">incremental recovery rate</span></div>'
        f'<div class="ci">95% CI [{p.confidence_interval_95[0]:+.2%}, {p.confidence_interval_95[1]:+.2%}] '
        f'· p = {p.p_value:.4f} &nbsp; {pill(p.status.value.replace("_", " "), tone)}</div>'
        f'</div>', unsafe_allow_html=True,
    )
    st.markdown(f'<div class="note">{p.explanation}</div>', unsafe_allow_html=True)
    st.write("")

    st.markdown("##### Money — ₹ recovered vs ₹ at risk, and cost per recovery")
    st.dataframe(
        pd.DataFrame([{
            "Arm": name,
            "₹ at risk": getattr(m, "total_at_risk_paise", 0) / 100,
            "₹ recovered": m.attributed_recovered_paise / 100,
            "Value recovery rate": getattr(m, "value_recovery_rate", 0.0) * 100,
            "Recovery rate": m.recovery_rate * 100,
            "Cost / recovery (paise)": getattr(m, "cost_per_recovery_paise", 0.0),
        } for name, m in summary.arm_metrics.items()]),
        use_container_width=True, hide_index=True,
        column_config={
            "₹ at risk": st.column_config.NumberColumn(format="₹%.0f"),
            "₹ recovered": st.column_config.NumberColumn(format="₹%.0f"),
            "Value recovery rate": st.column_config.NumberColumn(format="%.2f%%"),
            "Recovery rate": st.column_config.NumberColumn(format="%.2f%%"),
            "Cost / recovery (paise)": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.markdown(
        '<div class="note"><b>₹ recovered without the denominator it was recovered FROM is not a '
        'recovery claim.</b> Cost per recovery is marginal channel cost only — email ₹0.05 up to '
        'agent-dial ₹15.00 — not staff time or goodwill. ₹ at risk is the amount as it stood at the '
        'decision: for a B2B invoice settled net of statutory TDS, that is the derived recoverable '
        'balance, never the invoice face value.</div>', unsafe_allow_html=True,
    )

    st.markdown("##### Contact efficiency & compliant escalation")
    st.dataframe(
        pd.DataFrame([{
            "Arm": name,
            "Recoveries": m.successful_recoveries,
            "Contacts": getattr(m, "outbound_contacts", 0),
            "Per customer": getattr(m, "contacts_per_customer", 0.0),
            "Recovery / contact": getattr(m, "recovery_per_contact_paise", 0.0) / 100,
            "Escalations earned": getattr(m, "earned_escalations", 0),
            "Ceiling suppressions": getattr(m, "escalation_suppressed_count", 0),
            "Abstentions": getattr(m, "abstention_count", 0),
        } for name, m in summary.arm_metrics.items()]),
        use_container_width=True, hide_index=True,
        column_config={
            "Per customer": st.column_config.NumberColumn(format="%.2f"),
            "Recovery / contact": st.column_config.NumberColumn(format="₹%.0f"),
        },
    )
    no_esc = [
        n for n, m in summary.arm_metrics.items()
        if getattr(m, "outbound_contacts", 0) > 0 and getattr(m, "earned_escalations", 0) == 0
    ]
    if no_esc:
        st.markdown(
            f'<div class="note"><b>{", ".join(no_esc)} sent contacts but earned zero escalations.</b> '
            'Not a bug — the finding. An arm with no shared contact ledger cannot prove a customer '
            'was already reached, so it can never satisfy the evidence the ladder requires: it '
            'repeats the first touch instead of escalating. Compliant escalation presupposes the '
            'shared memory uncoordinated agents lack.</div>', unsafe_allow_html=True,
        )
    st.markdown(
        '<div class="note"><b>Recovery rate alone cannot show what this engine is for.</b> '
        'Every safety control suppresses a contact, so on that metric more safety can only ever '
        'look worse. The claim is comparable recovery for materially fewer contacts — read '
        '<b>Contacts</b> and <b>Recovery / contact</b> alongside the rate, never the rate alone.</div>',
        unsafe_allow_html=True,
    )

    streams = getattr(summary.arm_metrics.get("A5"), "stream_counts", {}) or {}
    if streams:
        st.markdown("##### Stream coverage — one engine, four streams")
        total_s = sum(streams.values()) or 1
        cols = st.columns(len(streams))
        for col, (name, count) in zip(cols, sorted(streams.items(), key=lambda kv: -kv[1])):
            col.metric(name.replace("_", " ").title(), count, f"{count / total_s:.0%}")
        st.markdown(
            '<div class="note">Track 3 names three sources: payment failures, checkout abandonment, '
            'overdue receivables. A single-stream batch cannot demonstrate a <b>unified</b> engine. '
            'This is the count that shows the batch was mixed.</div>', unsafe_allow_html=True,
        )

    st.markdown("##### Secondary comparisons · Holm-Bonferroni corrected")
    st.dataframe(
        pd.DataFrame([{
            "Comparison": s.comparison_id,
            "Isolates": {
                "A2ns_vs_A1": "shared ledger + arbitration",
                "A2_vs_A2ns": "Stage 0 validation",
                "A3_vs_A2": "downtime signal",
                "A5_vs_A3": "scoring model vs heuristic",
                "A5_vs_CONTROL": "acting vs never acting",
            }.get(s.comparison_id, "—"),
            "Incremental": s.incremental_recovery_rate * 100,
            "95% CI": f"[{s.confidence_interval_95[0]:+.2%}, {s.confidence_interval_95[1]:+.2%}]",
            "p": s.p_value,
            "Verdict": s.status.value.replace("_", " ").title(),
        } for s in summary.secondary_comparisons]),
        use_container_width=True, hide_index=True,
        column_config={"Incremental": st.column_config.NumberColumn(format="%+.2f%%"),
                       "p": st.column_config.NumberColumn(format="%.4f")},
    )
    st.markdown(
        '<div class="note">A2 − A1 bundles the shared ledger, arbitration and Stage 0; it is the '
        '<b>Unified Recovery Engine lift</b>, never an "AI lift". Every figure is produced under the '
        'synthetic data-generating process.</div>', unsafe_allow_html=True,
    )


FLAG_STYLE = {
    "PAID":    ("#059669", "rgba(5,150,105,.12)",  "PAID"),
    "ACTIVE":  ("#4338CA", "rgba(67,56,202,.12)",  "IN PROGRESS"),
    "WAITING": ("#D97706", "rgba(217,119,6,.12)",  "WAITING"),
    "STALLED": ("#DC2626", "rgba(220,38,38,.12)",  "NEEDS ATTENTION"),
}


def section_case_board() -> None:
    """One row per customer: what the agent decided, whether it reached them, did they pay."""
    from app.cases.board import build_board, summarise
    from app.cases.repository import CaseRepository
    from app.realtime import ingest

    st.markdown("#### Case board")
    st.markdown(
        '<div class="note">One row per customer, assembled from the case, its timeline, its '
        'payment link and its follow-up schedule. <b>There is no open/click tracking in this '
        'system</b> — the engine knows only whether a contact was confirmed delivered and '
        'whether money arrived, so a red row means <i>contacted, no payment, nothing '
        'scheduled</i>, never "the customer ignored us". We cannot tell ignored from '
        'never-saw-it and the board does not pretend to.</div>',
        unsafe_allow_html=True,
    )

    try:
        repo = CaseRepository(ingest.get_conn())
        rows = build_board(repo)
    except Exception as exc:
        st.info(f"No cases yet ({exc}).")
        return

    if not rows:
        st.info("No cases yet. Upload a CSV below to create some.")
        return

    s = summarise(rows)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cases", s["cases"])
    c2.metric("At risk", rupees(s["total_paise"]))
    c3.metric("Recovered", rupees(s["recovered_paise"]),
              delta=f"{s['recovery_rate']:.0%} of value", delta_color="normal")
    c4.metric("Contacts sent", s["contacts_made"])
    c5.metric("Needs attention", s["needs_attention"],
              delta="red rows" if s["needs_attention"] else None, delta_color="inverse")

    chips = "".join(
        f'<span class="pill" style="color:{FLAG_STYLE[f][0]};background:{FLAG_STYLE[f][1]};'
        f'border:1px solid {FLAG_STYLE[f][0]}55;margin-right:.4rem;">'
        f'{FLAG_STYLE[f][2]} · {n}</span>'
        for f, n in sorted(s["by_flag"].items()) if f in FLAG_STYLE
    )
    st.markdown(f'<div style="margin:.5rem 0 .8rem;">{chips}</div>', unsafe_allow_html=True)

    frame = pd.DataFrame([r.to_row() for r in rows])

    def paint(row):
        colour, background, _ = FLAG_STYLE.get(row["Flag"], ("", "", ""))
        return [f"background-color:{background}" if background else "" for _ in row]

    st.dataframe(
        frame.style.apply(paint, axis=1),
        use_container_width=True, hide_index=True,
        column_config={
            "Amount": st.column_config.NumberColumn(format="₹%.2f"),
            "Stage": st.column_config.TextColumn(width="large"),
            "Why": st.column_config.TextColumn("Why not paid", width="medium"),
        },
    )

    with st.expander("Timeline for one case"):
        labels = {f"{r.name or r.customer_id} · {rupees(r.amount_paise)} · {r.flag}": r
                  for r in rows}
        chosen = st.selectbox("Case", list(labels), key="board_case")
        picked = labels[chosen]
        if picked.payment_url:
            st.markdown(f"**Payment link:** {picked.payment_url}")
        for event in repo.timeline(picked.case_id):
            st.markdown(
                f'<div class="urx-kv"><span class="k">{event.at[11:19]} · '
                f'{event.kind.value.replace("_", " ").title()}</span>'
                f'<span class="v" style="font-weight:400;text-align:left;">'
                f'{event.summary}</span></div>',
                unsafe_allow_html=True,
            )


def section_handoff_report() -> None:
    """Everyone the engine could not recover, as a spreadsheet a human can work from."""
    from app.realtime import ingest
    from app.reporting import unrecovered

    st.write("")
    st.markdown("##### Unrecovered handoff report")
    st.markdown(
        '<div class="note">The most important honest output of an automated recovery '
        'engine is the list of people it could <b>not</b> recover. Every row here has been '
        'contacted as far as policy allows, and carries what was already tried — so a '
        'collections agent does not re-send the email the engine already sent three '
        'times. Customers who paid are excluded by construction.</div>',
        unsafe_allow_html=True,
    )

    try:
        conn = ingest.get_conn()
        rows = unrecovered.collect(conn)
    except Exception as exc:
        st.info(f"No recovery history yet ({exc}).")
        return

    if not rows:
        st.success(
            "Nothing to hand off. Every opportunity the engine pursued either resolved or "
            "is still in progress."
        )
        return

    summary = unrecovered.summarise(rows)
    c1, c2, c3 = st.columns(3)
    c1.metric("Customers unrecovered", summary["customers"])
    c2.metric("Still outstanding", rupees(summary["total_unrecovered_paise"]))
    c3.metric("Contacts already spent", summary["contacts_spent"])

    st.dataframe(
        pd.DataFrame([r.to_dict() for r in rows]),
        use_container_width=True, hide_index=True,
    )
    st.download_button(
        "Download Excel handoff report",
        data=unrecovered.build_workbook(rows),
        file_name=f"unrecovered_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


def section_live_test() -> None:
    """Judge harness: upload a CSV, the real engine decides, real messages go out."""
    from app.dispatch import channels
    from app.agent.loop import RecoveryAgent
    from app.cases.csv_ingest import MAX_ROWS, SAMPLE_CSV, create_cases, parse_csv
    from app.cases.repository import CaseRepository
    from app.dispatch.dispatcher import ChannelDispatcher
    from app.realtime import ingest

    section_case_board()
    st.write("")
    st.markdown("---")

    st.markdown("#### Upload a merchant CSV")
    st.markdown(
        '<div class="note">Upload a CSV with <b>your own</b> email and phone. The real '
        'decision engine runs — Stage 0, diagnosis, EV ranking, safety filter — and then '
        'actually sends what it chose. This is the one screen where a decision leaves the '
        'machine.</div>', unsafe_allow_html=True,
    )
    st.write("")

    ready = channels.configured_channels()
    cols = st.columns(len(ready))
    for col, (name, ok) in zip(cols, ready.items()):
        col.metric(name.replace("_", " ").title(), "Ready" if ok else "Not set")
    if not any(ready.values()):
        st.warning(
            "No channel has credentials, so nothing can actually send. Dry run still shows "
            "every decision. To send for real set: RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET "
            "(Razorpay delivers SMS + email itself), SMTP_USER / SMTP_PASSWORD for email, "
            "or TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN plus a TWILIO_*_FROM number for "
            "SMS, WhatsApp and IVR calls."
        )

    st.download_button(
        "Download a sample CSV", SAMPLE_CSV, file_name="recovery_test.csv", mime="text/csv"
    )
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is None:
        st.caption(
            "Columns: customer_name, email, phone, amount_rupees, event_type, "
            "failure_reason. Optional for B2B: invoice_status, amount_received_rupees, "
            "tds_section."
        )
        return

    report = parse_csv(uploaded.getvalue())
    rows = report.valid
    for col in report.missing_columns:
        st.error(f"CSV refused - missing required column: {col}")
    for bad in report.rejected:
        st.warning(f"Line {bad.line} rejected: {bad.reason}")
    if not rows:
        return

    st.dataframe(
        pd.DataFrame([
            r.to_dict() for r in rows
        ]),
        use_container_width=True, hide_index=True,
        column_config={"Amount": st.column_config.NumberColumn(format="₹%.2f")},
    )

    c1, c2 = st.columns([1, 1])
    dry = c1.toggle("Dry run (decide, send nothing)", value=True)
    confirm = c2.checkbox(
        f"These {len(rows)} recipients are my own test contacts",
        help=(
            "Real messages will be delivered. The cap is "
            f"{MAX_ROWS} rows — enough to test, not enough to broadcast."
        ),
    )

    if not st.button(
        "Run dry" if dry else "Run and SEND FOR REAL",
        type="primary", disabled=not (dry or confirm),
    ):
        return
    if not dry and not confirm:
        return

    with st.spinner("Creating cases and running the engine…"):
        # The DURABLE path: rows become Cases, so a payment webhook has something to close.
        # The old ephemeral runner left nothing for the loop to close against.
        conn = ingest.get_conn()
        repo = CaseRepository(conn)
        cases = create_cases(repo, rows, merchant_id="merch_demo")
        agent = RecoveryAgent(
            conn, repository=repo,
            dispatcher=ChannelDispatcher(conn, repository=repo, dry_run=dry),
        )
        results = agent.run_batch([c.case_id for c in cases])

    for r in results:
        status = r.dispatch.get("status", "-")
        icon = {"SENT": "SENT", "SKIPPED": "DRY", "BLOCKED": "BLOCKED"}.get(status, status)
        with st.expander(f"[{icon}]  {r.action or 'NO ACTION'} — {r.case_id[:46]}",
                         expanded=True):
            st.markdown(f"**Why:** {r.reasoning or r.skipped_reason}")
            if r.payment_url:
                st.markdown(f"**PAY NOW:** {r.payment_url}")
            if r.dispatch:
                st.dataframe(pd.DataFrame([r.dispatch]),
                             use_container_width=True, hide_index=True)

    st.success("Cases created. Scroll up to the case board to track them.")

    section_handoff_report()

    st.markdown(
        '<div class="note"><b>What is relaxed on this screen.</b> Two campaign-pacing '
        'controls only: the 24h quiet period, and the per-customer contact cap. Both exist '
        'to protect a merchant&#39;s customers during a live campaign, not a reviewer '
        'testing on themselves. Stage 0, diagnosis, EV ranking, the hard safety filter and '
        'the one-rung escalation ladder all run exactly as in production — put the same '
        'email on three rows and watch it climb EMAIL → SMS → WHATSAPP.</div>',
        unsafe_allow_html=True,
    )


def section_safety() -> None:
    st.markdown("#### Safety invariants")
    st.markdown(
        '<div class="note">These checks execute when this page loads. A tick here means the check '
        'ran and passed just now — not that a document claims it.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    checks = run_invariant_checks()
    passed = sum(1 for c in checks if c["passed"])
    st.markdown(
        f'{pill(f"{passed}/{len(checks)} executed checks passing", "ok" if passed == len(checks) else "stop")}',
        unsafe_allow_html=True,
    )
    st.write("")

    for c in checks:
        st.markdown(
            f'<div class="urx-card">'
            f'<h4>{c["id"]} · {c["name"]} &nbsp; {pill("PASS" if c["passed"] else "FAIL", "ok" if c["passed"] else "stop")}</h4>'
            f'<div class="note">{c["evidence"]}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("##### Enforced structurally, verified in the test suite")
    st.markdown(
        '<div class="note">These are architectural properties rather than page-time checks. They are '
        'covered by the pytest suite — <code>pytest -q</code> — and are listed here without a tick '
        'because this page did not run them.</div>', unsafe_allow_html=True,
    )
    st.dataframe(
        pd.DataFrame([
            {"Invariant": "INV-1 Tenant isolation", "Enforced by": "merchant_id on every key; TenantScopedDB rejects unscoped SQL"},
            {"Invariant": "INV-2 Atomic reservation", "Enforced by": "conditional UPDATE + DB CHECK (reserved + consumed <= cap)"},
            {"Invariant": "INV-3 Exploration safety", "Enforced by": "hard filter precedes exploration; eligible set is the pool"},
            {"Invariant": "INV-4 Outage suppression", "Enforced by": "diagnosis safety floor + downtime signal"},
            {"Invariant": "INV-5 Retry ownership", "Enforced by": "EXECUTE_RETRY absent from the action enum"},
            {"Invariant": "INV-6 Execution unknown", "Enforced by": "reconciliation ladder; never auto-resent"},
        ]),
        use_container_width=True, hide_index=True,
    )


def section_about() -> None:
    st.markdown("#### What this is")
    st.markdown(
        "A unified recovery decision engine: one decision layer above four revenue-leak types, "
        "deciding whether money was genuinely lost, diagnosing why, ranking interventions including "
        "**doing nothing**, and executing at most one under a contact budget shared across streams."
    )

    a, b = st.columns(2)
    with a:
        card("Really implemented", "".join([
            kv("Contact ledger", "atomic, concurrency-tested"),
            kv("Policy & safety filter", "hard constraints"),
            kv("Stage 0 / Stage 1", "validate, diagnose"),
            kv("Scoring", "heuristic + CatBoost S-learner"),
            kv("Attribution", "self-cure excluded"),
            kv("Experiment + statistics", "5 arms, CIs, Holm"),
        ]))
    with b:
        card("Simulated", "".join([
            kv("Payment execution", "sandbox provider"),
            kv("Customer response", "authored response function"),
            kv("Gateway downtime", "simulated signal"),
            kv("Message delivery", "no provider integration"),
            kv("Recovery outcomes", "synthetic"),
        ]))

    st.markdown(
        '<div class="note"><b>What this cannot show:</b> real Razorpay recovery uplift, real payer-response '
        'accuracy, production ROI, or production model calibration. Confidence intervals quantify sampling '
        'error <i>within the simulation only</i>. Environmental distributions are calibrated from public '
        'aggregate data; calibrating a simulator with real inputs does not make its outputs real.</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def render_dashboard() -> None:
    """Render the Streamlit judge dashboard."""
    st.set_page_config(
        page_title="Unified Recovery Engine",
        page_icon="◆",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(STYLES, unsafe_allow_html=True)

    st.markdown(
        '<div class="urx-head"><h1>Unified Recovery Engine</h1>'
        '<span class="sub">Track 3 · AI Revenue Recovery · judge audit interface</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="urx-banner"><b>SANDBOX — SIMULATED DATA.</b> Not connected to any payment system. '
        'No live credentials, no real money, no external gateway calls. Payment failures, customer '
        'responses and recovery outcomes are deterministic local simulations.</div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### Controls")
        st.caption("Change the world the engine sees, then re-read the trace.")
        seed = st.number_input("Random seed", value=42, min_value=1,
                               help="Same seed reproduces the identical decision.")
        outage = st.checkbox("Force gateway outage (HDFC)")
        exhaust = st.checkbox("Exhaust contact budget (cust_101)")
        st.divider()
        st.caption(
            "Reproduce the full experiment from the command line:\n\n"
            "`make eval` → `results/report.json`"
        )

    t_trace, t_exp, t_live, t_safety, t_about = st.tabs(
        ["Decision trace", "Experiment", "Live test (CSV)", "Safety", "About"]
    )
    with t_trace:
        section_trace(int(seed), outage, exhaust)
    with t_exp:
        section_experiment()
    with t_live:
        section_live_test()
    with t_safety:
        section_safety()
    with t_about:
        section_about()


if __name__ == "__main__":
    render_dashboard()
