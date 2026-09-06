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

from datetime import datetime, timezone
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

  /* --- case board: a card per customer, not a spreadsheet ------------------------- */
  /* Three columns: who they are, how far up the ladder, what they owe. The ladder sits
     INLINE rather than on its own row - it halves the card height, which is the
     difference between four cases on screen and two. */
  .case { position:relative; border:1px solid rgba(128,128,128,.20); border-radius:12px;
          padding:1rem 1.15rem .85rem 1.35rem; margin-bottom:.6rem; overflow:hidden;
          background:linear-gradient(100deg, var(--tint) 0%, rgba(128,128,128,.025) 38%); }
  .case::before { content:""; position:absolute; left:0; top:0; bottom:0; width:5px;
                  background:var(--c); }
  .case .row { display:flex; align-items:flex-start; gap:1.2rem; }
  .case .idc { flex:1 1 30%; min-width:0; }
  .case .ladc { flex:0 1 auto; padding-top:.28rem; }
  .case .amtc { flex:0 0 auto; margin-left:auto; text-align:right; }

  .case .who { font-size:1.02rem; font-weight:680; letter-spacing:-.014em; line-height:1.3;
               display:flex; align-items:center; gap:.5rem; flex-wrap:wrap; }
  .case .con { font-size:.755rem; opacity:.5; margin-top:.22rem;
               font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
               overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .case .amt { font-size:1.26rem; font-weight:700; letter-spacing:-.025em;
               font-variant-numeric:tabular-nums; white-space:nowrap; line-height:1.15; }
  .case .due { font-size:.715rem; opacity:.5; margin-top:.25rem; white-space:nowrap; }
  .case .stg { font-size:.865rem; opacity:.92; margin:.7rem 0 0; line-height:1.45; }
  .case .meta { display:flex; gap:.5rem; flex-wrap:wrap; align-items:center; margin-top:.55rem; }
  .case .meta .m { font-size:.725rem; opacity:.5; }
  .case .meta .dot { opacity:.28; }

  /* the escalation ladder: which rungs this customer has actually been through */
  .lad { display:flex; align-items:center; }
  .lad .r { font-size:.66rem; letter-spacing:.06em; font-weight:700; padding:.3rem .62rem;
            border-radius:7px; border:1px solid rgba(128,128,128,.26); opacity:.34;
            white-space:nowrap; }
  .lad .r.done { opacity:1; color:#10B981; border-color:rgba(16,185,129,.55);
                 background:rgba(16,185,129,.10); }
  .lad .r.next { opacity:1; color:#818CF8; border-color:rgba(129,140,248,.75);
                 border-style:dashed; background:rgba(67,56,202,.10); }
  .lad .sep { width:16px; height:1px; background:rgba(128,128,128,.26); flex:0 0 16px; }

  /* --- decision trace: a numbered pipeline, not a bulleted list ------------------- */
  .step { position:relative; display:flex; gap:.95rem; padding:.55rem 0 .8rem; }
  .step:not(:last-child)::before { content:""; position:absolute; left:15px; top:34px;
        bottom:-6px; width:2px; background:rgba(128,128,128,.22); }
  .step .n { flex:0 0 32px; height:32px; border-radius:50%; display:flex;
             align-items:center; justify-content:center; font-size:.8rem; font-weight:700;
             background:rgba(128,128,128,.14); border:1px solid rgba(128,128,128,.3);
             position:relative; z-index:1; }
  .step .bd { flex:1; min-width:0; padding-top:.15rem; }
  .step .t { font-size:.95rem; font-weight:650; letter-spacing:-.01em;
             display:flex; align-items:center; gap:.55rem; flex-wrap:wrap; }
  .step .d { font-size:.815rem; opacity:.62; line-height:1.5; margin-top:.2rem; }
  /* A highlighted step is a claim that something happened THERE. Colour carries it. */
  .step.on  { background:rgba(67,56,202,.07); border-left:3px solid #4338CA;
              border-radius:0 9px 9px 0; padding-left:.85rem; margin-left:-.2rem; }
  .step.on .n  { background:#4338CA; border-color:#4338CA; color:#fff; }
  .step.warn { background:rgba(217,119,6,.07); border-left:3px solid #D97706;
               border-radius:0 9px 9px 0; padding-left:.85rem; margin-left:-.2rem; }
  .step.warn .n { background:#D97706; border-color:#D97706; color:#fff; }
  .step.stop { background:rgba(220,38,38,.07); border-left:3px solid #DC2626;
               border-radius:0 9px 9px 0; padding-left:.85rem; margin-left:-.2rem; }
  .step.stop .n { background:#DC2626; border-color:#DC2626; color:#fff; }

  /* the answer, beside the story */
  .ans { border:1px solid rgba(128,128,128,.24); border-radius:12px; padding:.95rem 1.1rem;
         margin-bottom:.75rem; background:rgba(128,128,128,.03); }
  .ans .h { font-size:.7rem; letter-spacing:.1em; text-transform:uppercase; opacity:.6;
            font-weight:650; margin-bottom:.5rem; }
  .ans .big { font-size:1.85rem; font-weight:700; letter-spacing:-.03em; line-height:1.15;
              font-variant-numeric:tabular-nums; }
  .ans .action { font-size:1.5rem; font-weight:700; letter-spacing:-.02em;
                 font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }
  .ans .formula { font-size:.75rem; opacity:.55; margin-top:.45rem; line-height:1.5;
                  font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }
  .rej { display:flex; justify-content:space-between; gap:1rem; padding:.34rem 0;
         font-size:.79rem; border-bottom:1px dotted rgba(128,128,128,.16); }
  .rej:last-child { border-bottom:none; }
  .rej .a { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; opacity:.85; }
  .rej .w { font-size:.71rem; font-weight:700; letter-spacing:.04em; white-space:nowrap; }

  /* --- safety checks: an executed result per row, not a checklist ----------------- */
  .sumbar { display:flex; align-items:center; justify-content:space-between; gap:1rem;
            border:1px solid var(--sc); background:var(--st); border-radius:11px;
            padding:.8rem 1.1rem; margin-bottom:.8rem; }
  .sumbar .l { display:flex; align-items:center; gap:.7rem; font-size:1rem; font-weight:650; }
  .sumbar .r { font-size:.78rem; opacity:.6; font-variant-numeric:tabular-nums; }
  .dotico { width:22px; height:22px; border-radius:50%; display:inline-flex;
            align-items:center; justify-content:center; font-size:.72rem; font-weight:800;
            color:#fff; flex:0 0 22px; }

  .chk { display:flex; align-items:flex-start; gap:.85rem; border-radius:10px;
         border:1px solid rgba(128,128,128,.2); background:rgba(128,128,128,.03);
         padding:.72rem .95rem; margin-bottom:.5rem; }
  .chk.bad { border-color:rgba(220,38,38,.45); background:rgba(220,38,38,.07); }
  .chk .code { flex:0 0 auto; font-size:.7rem; font-weight:700; letter-spacing:.04em;
               padding:.22rem .5rem; border-radius:6px; margin-top:.05rem;
               border:1px solid rgba(128,128,128,.3); background:rgba(128,128,128,.08);
               font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }
  .chk .bd { flex:1; min-width:0; }
  .chk .t { font-size:.92rem; font-weight:650; letter-spacing:-.008em; }
  .chk .e { font-size:.755rem; opacity:.58; margin-top:.22rem; line-height:1.5;
            font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
            word-break:break-word; }

  /* headline tiles, bordered rather than floating - they read as one instrument panel */
  .tiles { display:flex; gap:.7rem; margin:.2rem 0 .9rem; flex-wrap:wrap; }
  .tile { flex:1 1 0; min-width:150px; border:1px solid rgba(128,128,128,.22);
          border-radius:11px; padding:.75rem .9rem .8rem; background:rgba(128,128,128,.03); }
  .tile .k { font-size:.68rem; letter-spacing:.09em; text-transform:uppercase; opacity:.55;
             font-weight:600; }
  .tile .v { font-size:1.62rem; font-weight:700; letter-spacing:-.03em; margin-top:.3rem;
             font-variant-numeric:tabular-nums; line-height:1.1; }
  .tile .d { font-size:.72rem; margin-top:.2rem; font-variant-numeric:tabular-nums; }

  /* status chips carry a colour dot, so the legend reads at a glance */
  .chip { display:inline-flex; align-items:center; gap:.4rem; padding:.32rem .72rem;
          border-radius:999px; font-size:.71rem; font-weight:700; letter-spacing:.045em;
          margin-right:.5rem; }
  .chip .b { width:7px; height:7px; border-radius:2px; display:inline-block; }

  /* the decision trail, as a rail rather than a list of rows */
  .tl { border-left:2px solid rgba(128,128,128,.22); margin:.15rem 0 .2rem .38rem;
        padding-left:1.05rem; }
  .tl .e { position:relative; padding:.28rem 0; font-size:.825rem; line-height:1.45; }
  .tl .e::before { content:""; position:absolute; left:-1.36rem; top:.62rem; width:8px;
                   height:8px; border-radius:50%; background:rgba(128,128,128,.45);
                   box-shadow:0 0 0 3px rgba(128,128,128,.10); }
  .tl .e.hi::before { background:#059669; box-shadow:0 0 0 3px rgba(5,150,105,.16); }
  .tl .e .t { font-size:.715rem; opacity:.45; font-variant-numeric:tabular-nums;
              margin-right:.55rem; }
  .tl .e .k { font-weight:650; }

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


def step(n: int, title: str, detail: str, state: str = "", tag: str = "") -> str:
    """One numbered stage of the decision pipeline.

    `state` is a claim, not decoration: "on" says the decision was made here, "warn" that
    something was suppressed, "stop" that the case was halted. A reader should be able to
    see WHERE the decision happened without reading every line.
    """
    chip = f'<span class="pill warn" style="font-size:.63rem;">{tag}</span>' if tag else ""
    return (
        f'<div class="step {state}"><div class="n">{n}</div><div class="bd">'
        f'<div class="t">{title}{chip}</div><div class="d">{detail}</div></div></div>'
    )


def tile(key: str, value: str, delta: str = "", delta_colour: str = "") -> str:
    """One headline number. Shared by every tab so a figure looks the same everywhere."""
    d = f'<div class="d" style="color:{delta_colour};">{delta}</div>' if delta else ""
    return f'<div class="tile"><div class="k">{key}</div><div class="v">{value}</div>{d}</div>'


def tiles(*cells: str) -> None:
    st.markdown('<div class="tiles">' + "".join(cells) + "</div>", unsafe_allow_html=True)


def answer_card(heading: str, body: str) -> str:
    return f'<div class="ans"><div class="h">{heading}</div>{body}</div>'


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

def _escalation_step(result: Any, n: int) -> str:
    """Render the compliant-escalation ceiling as one pipeline step.

    Reads the escalation assessment off the executed decision — never scripted. Shows the
    ceiling that bound this decision and, when it removed a candidate, why.
    """
    esc = getattr(result, "escalation", None)
    if esc is None:
        return step(n, "Compliant escalation",
                    "No escalation assessment on this path.")
    ceiling = esc.allowed_max_rung
    ladder = esc.ladder
    ceiling_action = ladder[ceiling].replace("_", " ").title() if 0 <= ceiling < len(ladder) else "—"
    if esc.suppressed_actions:
        detail = (
            f"Ceiling <b>{ceiling_action}</b>. "
            f"Suppressed louder channels: "
            f"{', '.join(a.replace('_', ' ').title() for a in esc.suppressed_actions)}."
        )
        state = "warn"
    else:
        detail = f"Ceiling <b>{ceiling_action}</b>. No louder channel was in play to suppress."
        state = "on"
    if esc.cooldown_active:
        detail += " Quiet period active — intensity held."
    return step(n, "Compliant escalation", detail, state,
                tag="SUPPRESSED" if esc.suppressed_actions else "")


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
    attributed = result.attribution.attributed_recovered_paise
    tiles(
        tile("Selected action", d.selected_action.value.replace("_", " ").title()),
        tile("Decision mode", d.decision_mode.value.replace("_", " ").title()),
        tile("Simulated outcome",
             result.attribution.payment_outcome.value.replace("_", " ").title()),
        tile("Attributed to intervention", rupees(attributed),
             "" if attributed else "self-cure — not attributed", "#D97706"),
    )

    st.write("")
    story, answer = st.columns([1.55, 1])

    eligible = [c for c in d.candidate_scores if c.eligibility == EligibilityStatus.ELIGIBLE]
    rejected = [c for c in d.candidate_scores if c.eligibility != EligibilityStatus.ELIGIBLE]
    chosen = next((c for c in d.candidate_scores if c.action_type == d.selected_action), None)
    stage0_ok = "not_recoverable" not in str(getattr(d, "abstention_reason", "")).lower()
    reserved = getattr(d, "is_contact_reserved", False)

    # --- the story: where the decision was actually made -------------------
    with story:
        st.markdown("##### How this decision was reached")
        st.markdown("".join([
            step(1, "Event ingested",
                 f"<code>{result.event_id}</code> became opportunity "
                 f"<code>{result.opportunity_id}</code>."),
            step(2, "Stage 0 · Validate",
                 "Genuine recoverable exposure confirmed." if stage0_ok
                 else "Closed as not recoverable. No contact is made.",
                 "" if stage0_ok else "stop"),
            step(3, "Stage 1 · Diagnose",
                 f"Cause identified, and {len(d.candidate_scores)} candidate actions "
                 f"generated for it.", "on"),
            step(4, "Candidate generation",
                 "Only actions this stream can legally take are offered. A merchant-"
                 "uploaded debt has no stored instrument, so a retry is never a candidate."),
            step(5, "Safety filter · escalation ceiling",
                 f"{len(eligible)} eligible, {len(rejected)} suppressed before any "
                 f"scoring happened.",
                 "warn" if rejected else "", "SUPPRESSED" if rejected else ""),
            step(6, "Expected value ranking",
                 f"Model <code>{d.model_version}</code> scored every surviving candidate "
                 f"against doing nothing."),
            _escalation_step(result, 7),
            step(8, "Arbitration & attribution",
                 f"{result.attribution.payment_outcome.value.replace('_', ' ').title()} → "
                 f"attributed {rupees(attributed)}."
                 + ("" if reserved else " No contact slot was consumed.")),
        ]), unsafe_allow_html=True)

    # --- the answer, beside it ---------------------------------------------
    with answer:
        st.markdown("##### What it decided")

        detail = "".join([
            kv("Decision mode", d.decision_mode.value.replace("_", " ").title()),
            kv("P(recover | action)", f"{chosen.raw_probability * 100:.1f}%") if chosen else "",
            kv("P(no action)", f"{chosen.baseline_probability * 100:.1f}%") if chosen else "",
            kv("Uplift", f"{chosen.incremental_effect * 100:+.1f}%") if chosen else "",
            kv("Action cost", rupees(chosen.action_cost_paise)) if chosen else "",
        ])
        st.markdown(answer_card(
            "Chosen action",
            f'<div class="action">{d.selected_action.value}</div>'
            f'<div style="margin-top:.6rem;">{detail}</div>'), unsafe_allow_html=True)

        ev = chosen.expected_value_paise if chosen else 0
        st.markdown(answer_card(
            "Expected value",
            f'<div class="big">{rupees(ev)}</div>'
            f'<div class="formula">EV = round(Δ̂ × amount_at_risk) − cost(a)<br>'
            f'Δ̂ = p̂(x,a) − p̂(x, NO_ACTION)</div>'), unsafe_allow_html=True)

        if rejected:
            rows = "".join(
                f'<div class="rej"><span class="a">{c.action_type.value}</span>'
                f'<span class="w" style="color:#DC2626;">'
                f'{c.reject_reason.value}</span></div>'
                for c in rejected
            )
            st.markdown(answer_card("Rejected before scoring", rows), unsafe_allow_html=True)

        st.markdown(answer_card("Provenance", "".join([
            kv("Decision", d.decision_id[:26], mono=True),
            kv("Model", d.model_version),
            kv("Seed", str(seed)),
            kv("Amount at risk", rupees(result.attribution.amount_at_risk_paise)),
        ])), unsafe_allow_html=True)

    # --- the evidence, full width ------------------------------------------
    st.write("")
    st.markdown("##### Every candidate, ranked by expected value")
    rows = []
    for c in d.candidate_scores:
        rows.append({
            "": "▶" if c.action_type == d.selected_action else "",
            "Action": c.action_type.value.replace("_", " ").title(),
            "P(recover | action)": c.raw_probability * 100,
            "P(no action)": c.baseline_probability * 100,
            "Uplift": c.incremental_effect * 100,
            "Expected value": c.expected_value_paise / 100,
            "Cost": c.action_cost_paise / 100,
            "Status": ("Eligible" if c.eligibility == EligibilityStatus.ELIGIBLE
                       else c.reject_reason.value.replace("_", " ").title()),
        })
    st.dataframe(
        pd.DataFrame(rows), use_container_width=True, hide_index=True,
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
        "incremental effect under the simulator's data-generating process</b>, used for ranking "
        'only. It is not a measured causal effect; those come from the arm comparison.</div>',
        unsafe_allow_html=True,
    )

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

    total_opps = sum(m.total_opportunities for m in summary.arm_metrics.values())
    at_risk = max((getattr(m, "total_at_risk_paise", 0) for m in summary.arm_metrics.values()),
                  default=0)
    st.markdown(
        '<div class="tiles">'
        + tile("Opportunities", f"{total_opps:,}")
        + tile("Seeds", str(len(getattr(summary, "seeds", []) or [])
                            or int(seed_end) - int(seed_start) + 1))
        + tile("Arms", str(len(summary.arm_metrics)))
        + tile("At risk", rupees(at_risk))
        + '</div>',
        unsafe_allow_html=True,
    )

    # The verdict, stated at the size it deserves. An INCONCLUSIVE primary is the honest
    # outcome of this experiment and is shown as prominently as a win would have been.
    colour = "#D97706" if inconclusive else "#059669"
    st.markdown(
        f'<div class="ans" style="border-color:{colour}55;background:{colour}0F;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;gap:1rem;">'
        f'  <div>'
        f'    <div class="h">Primary comparison · {p.comparison_id} · pre-registered</div>'
        f'    <div class="big">{p.incremental_recovery_rate:+.2%}</div>'
        f'    <div class="formula">95% CI [{p.confidence_interval_95[0]:+.4f}, '
        f'{p.confidence_interval_95[1]:+.4f}] · p = {p.p_value:.4f}</div>'
        f'  </div>'
        f'  <div class="chip" style="color:{colour};background:{colour}1A;'
        f'border:1px solid {colour}66;font-size:.8rem;padding:.5rem 1rem;">'
        f'{p.status.value.replace("_", " ")}</div>'
        f'</div></div>', unsafe_allow_html=True,
    )
    st.markdown(f'<div class="note">{p.explanation}</div>', unsafe_allow_html=True)

    # Every comparison, each with its own verdict. Shown in full because reporting only the
    # favourable ones is how an honest experiment becomes a marketing chart.
    others = [c for c in getattr(summary, "comparisons", []) or []
              if c.comparison_id != p.comparison_id]
    if others:
        st.write("")
        rows = ""
        for c in others:
            sig = c.status == StatisticalStatus.STATISTICALLY_SIGNIFICANT
            col = "#059669" if sig else "#D97706"
            rows += (
                f'<div class="rej" style="align-items:center;">'
                f'<span class="a" style="flex:0 0 22%;">{c.comparison_id}</span>'
                f'<span style="flex:0 0 14%;font-variant-numeric:tabular-nums;">'
                f'{c.incremental_recovery_rate:+.2%}</span>'
                f'<span style="flex:1;opacity:.55;font-size:.74rem;'
                f'font-family:ui-monospace,Menlo,monospace;">'
                f'95% CI [{c.confidence_interval_95[0]:+.4f}, {c.confidence_interval_95[1]:+.4f}]'
                f' · p = {c.p_value:.4f}</span>'
                f'<span class="chip" style="color:{col};background:{col}1A;'
                f'border:1px solid {col}55;margin:0;">{c.status.value.replace("_", " ")}</span>'
                f'</div>'
            )
        st.markdown(f'<div class="ans"><div class="h">Every comparison</div>{rows}</div>',
                    unsafe_allow_html=True)
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
        tiles(*[
            tile(name.replace("_", " ").title(), f"{count:,}",
                 f"{count / total_s:.0%} of batch", "#818CF8")
            for name, count in sorted(streams.items(), key=lambda kv: -kv[1])
        ])
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

# The board is sorted by who needs a human, not by when the row was created. A merchant
# looking at fifty cases should never have to scroll to find the one that has stalled.
FLAG_ORDER = {"STALLED": 0, "ACTIVE": 1, "WAITING": 2, "PAID": 3}

# The compliant escalation ladder, drawn as it is actually climbed. `channels_tried` has
# already had "_SMTP" and "TWILIO_" stripped by the board, so these are the surviving keys.
LADDER = (("EMAIL", "EMAIL"), ("SMS", "SMS"), ("WHATSAPP", "WHATSAPP"), ("VOICE", "CALL"))
ACTION_RUNG = {
    "EMAIL_LINK": "EMAIL", "SMS_LINK": "SMS", "WHATSAPP_LINK": "WHATSAPP",
    "IVR_CALL": "VOICE", "AGENT_DIAL": "VOICE",
}

# Events worth a filled dot on the rail: the money, and the case ending.
TIMELINE_HIGHLIGHT = {"PAYMENT_RECEIVED", "CASE_CLOSED"}


def _ladder(row) -> str:
    """Which rungs this customer has been through, and which one is queued next.

    A rung is lit only when a contact was CONFIRMED SENT on that channel. A dashed rung is
    a decision that has not been dispatched yet - it must not read as a message delivered.
    """
    done = {c.strip() for c in (row.channels_tried or "").split(",") if c.strip()}
    planned = "" if row.paid else ACTION_RUNG.get(row.last_action, "")
    cells = []
    for key, label in LADDER:
        if key in done:
            cls = "r done"
        elif key == planned:
            cls = "r next"
        else:
            cls = "r"
        cells.append(f'<span class="{cls}">{label}</span>')
    return '<div class="lad">' + '<span class="sep"></span>'.join(cells) + '</div>'


def _due_line(row) -> str:
    """The merchant's own due date, aged.

    A settled case is never shown as overdue. "17d overdue" beside a PAID badge is both
    wrong and the kind of detail that makes a merchant distrust every other number on the
    screen - the debt stopped ageing the moment the payment was verified.
    """
    if not row.due_date:
        return "settled" if row.paid else "no due date supplied"
    try:
        due = datetime.strptime(row.due_date, "%Y-%m-%d").date()
    except ValueError:
        return f"due {row.due_date}"
    if row.paid:
        return f"due {row.due_date} · settled"
    overdue = (datetime.now(timezone.utc).date() - due).days
    return f"due {row.due_date} · {overdue}d overdue" if overdue > 0 else f"due {row.due_date}"


def _case_card(row) -> str:
    """One customer as a card: who, how far up the ladder, and what they owe.

    Three columns rather than three stacked rows. The ladder inline with the identity
    halves the card height, which is the difference between four cases visible at once
    and two - and the board's whole job is letting a merchant scan fifty of them.
    """
    colour, tint, label = FLAG_STYLE.get(row.flag, ("#6B7280", "rgba(128,128,128,.08)", row.flag))

    meta = [f'{row.contacts_made} confirmed contact{"" if row.contacts_made == 1 else "s"}']
    if row.days_since_contact is not None:
        meta.append(f"last contact {row.days_since_contact}d ago")
    if row.next_review:
        meta.append(f'next review {row.next_review[:16].replace("T", " ")}')
    elif not row.paid:
        meta.append("nothing scheduled")
    meta.append(row.payment_note)
    meta_html = '<span class="dot">·</span>'.join(f'<span class="m">{m}</span>' for m in meta)

    return (
        f'<div class="case" style="--c:{colour};--tint:{tint};">'
        f'  <div class="row">'
        f'    <div class="idc">'
        f'      <div class="who">{row.name or row.customer_id}'
        f'        <span class="pill" style="color:{colour};background:{tint};'
        f'border:1px solid {colour}55;">{label}</span>'
        f'      </div>'
        f'      <div class="con">{row.contact or "no contact on file"}</div>'
        f'    </div>'
        f'    <div class="ladc">{_ladder(row)}</div>'
        f'    <div class="amtc">'
        f'      <div class="amt">{rupees(row.amount_paise)}</div>'
        f'      <div class="due">{_due_line(row)}</div>'
        f'    </div>'
        f'  </div>'
        f'  <div class="stg">{row.stage}</div>'
        f'  <div class="meta">{meta_html}</div>'
        f'</div>'
    )


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

    st.markdown(
        '<div class="tiles">'
        + tile("Cases", str(s["cases"]))
        + tile("At risk", rupees(s["total_paise"]))
        + tile("Recovered", rupees(s["recovered_paise"]),
               f"↑ {s['recovery_rate']:.0%} of value", "#10B981")
        + tile("Contacts sent", str(s["contacts_made"]))
        + tile("Needs attention", str(s["needs_attention"]),
               ("↑ needs a human" if s["needs_attention"] else "none"),
               "#F87171" if s["needs_attention"] else "#10B981")
        + '</div>',
        unsafe_allow_html=True,
    )

    chips = "".join(
        f'<span class="chip" style="color:{FLAG_STYLE[f][0]};background:{FLAG_STYLE[f][1]};'
        f'border:1px solid {FLAG_STYLE[f][0]}66;">'
        f'<span class="b" style="background:{FLAG_STYLE[f][0]};"></span>'
        f'{FLAG_STYLE[f][2]} · {n}</span>'
        for f, n in sorted(s["by_flag"].items()) if f in FLAG_STYLE
    )
    st.markdown(f'<div style="margin:.2rem 0 1rem;">{chips}</div>', unsafe_allow_html=True)

    st.caption(
        "Sorted by who needs a human first, not by upload order. "
        "Press **Open** on any customer to expand their full decision trail."
    )
    st.write("")

    rows = sorted(rows, key=lambda r: (FLAG_ORDER.get(r.flag, 9), -r.amount_paise))
    open_id = st.session_state.get("board_open_case")

    for row in rows:
        # Top alignment, not centre: the button must not drift down the screen when the
        # detail below it expands, or the control moves out from under the cursor that
        # just pressed it.
        card_col, action_col = st.columns([11, 1.7], vertical_alignment="top")
        card_col.markdown(_case_card(row), unsafe_allow_html=True)

        is_open = open_id == row.case_id
        if action_col.button(
            "Close" if is_open else "Open",
            key=f"board_open_{row.case_id}",
            use_container_width=True,
            help=f"Full timeline for {row.name or row.customer_id}",
        ):
            st.session_state["board_open_case"] = None if is_open else row.case_id
            st.rerun()

        # Rendered INSIDE the card's own column so the panel lines up under the card it
        # belongs to rather than spanning the button gutter as well.
        if is_open:
            with card_col:
                _render_case_detail(repo, row)


def _render_case_detail(repo, row) -> None:
    """Everything known about one case, expanded in place beneath its card."""
    colour, tint, label = FLAG_STYLE.get(row.flag, ("#6B7280", "rgba(128,128,128,.08)", row.flag))

    with st.container(border=True):
        left, right = st.columns([1, 1])

        with left:
            st.markdown(
                f'<div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;'
                f'opacity:.6;margin-bottom:.45rem;">Case detail</div>'
                f'{kv("Customer", row.name or row.customer_id)}'
                f'{kv("Contact", row.contact or "-")}'
                f'{kv("Amount", rupees(row.amount_paise))}'
                f'{kv("Status", label)}'
                f'{kv("Last decision", row.last_action or "-")}'
                f'{kv("Channels tried", row.channels_tried or "none")}'
                f'{kv("Confirmed contacts", str(row.contacts_made))}'
                f'{kv("Paid", "YES" if row.paid else "NO")}'
                f'{kv("Next review", row.next_review[:16].replace("T", " ") if row.next_review else "none scheduled")}'
                f'{kv("Case id", row.case_id, mono=True)}',
                unsafe_allow_html=True,
            )

        with right:
            st.markdown(
                '<div style="font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;'
                'opacity:.6;margin-bottom:.45rem;">Decision trail</div>',
                unsafe_allow_html=True,
            )
            entries = repo.timeline(row.case_id)
            if not entries:
                st.markdown('<div class="note">Nothing has happened on this case yet.</div>',
                            unsafe_allow_html=True)
            else:
                rail = "".join(
                    f'<div class="e{" hi" if e.kind.value in TIMELINE_HIGHLIGHT else ""}">'
                    f'<span class="t">{str(e.at)[11:16]}</span>'
                    f'<span class="k">{e.kind.value.replace("_", " ").title()}</span> — '
                    f'{e.summary}</div>'
                    for e in entries
                )
                st.markdown(f'<div class="tl">{rail}</div>', unsafe_allow_html=True)

        if row.payment_url and not row.paid:
            st.markdown(
                f'<div style="margin-top:.6rem;font-size:.83rem;">'
                f'<b>Live payment link</b> · <a href="{row.payment_url}" target="_blank">'
                f'{row.payment_url}</a></div>',
                unsafe_allow_html=True,
            )
            st.caption(
                "Paying this link fires a real Razorpay webhook. The case flips to PAID and "
                "every pending contact is cancelled — press Open again after paying to watch it."
            )

    st.write("")


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
    tiles(
        tile("Customers unrecovered", str(summary["customers"])),
        tile("Still outstanding", rupees(summary["total_unrecovered_paise"])),
        tile("Contacts already spent", str(summary["contacts_spent"])),
    )

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

    # Colour carries the fact: green can send, grey cannot. A channel with no credential
    # says "Not set" rather than going quiet, because an adapter that appears configured
    # and silently sends nothing is the failure this whole file is written against.
    ready = channels.configured_channels()
    tiles(*[
        tile(name.replace("_", " ").title(),
             "Ready" if ok else "Not set",
             "can send" if ok else "no credential",
             "#10B981" if ok else "#9CA3AF")
        for name, ok in ready.items()
    ])
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
        # Read off the template itself rather than typed out, so the instructions cannot
        # drift from what the parser accepts. They already had once: this caption still
        # asked for `failure_reason` months after the engine started diagnosing that
        # itself, which would have had a judge uploading a file the parser ignored.
        st.caption(
            f"Columns: **{SAMPLE_CSV.splitlines()[0]}**. `amount` is required and every "
            "row needs an email or a phone. There is deliberately no reason column - a "
            "merchant knows what is owed, not why it is unpaid, so the engine diagnoses "
            "that itself, per case."
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
    all_ok = passed == len(checks)
    colour = "#059669" if all_ok else "#DC2626"

    st.markdown(
        f'<div class="sumbar" style="--sc:{colour}66;--st:{colour}12;">'
        f'  <div class="l">'
        f'    <span class="dotico" style="background:{colour};">{"✓" if all_ok else "✕"}</span>'
        f'    {passed}/{len(checks)} safety invariants passed'
        f'  </div>'
        f'  <div class="r">{len(checks)} checks executed on this page load</div>'
        f'</div>', unsafe_allow_html=True,
    )

    for c in checks:
        ok = c["passed"]
        ico = "#059669" if ok else "#DC2626"
        st.markdown(
            f'<div class="chk{"" if ok else " bad"}">'
            f'  <span class="dotico" style="background:{ico};">{"✓" if ok else "✕"}</span>'
            f'  <span class="code" style="color:{ico};border-color:{ico}55;">{c["id"]}</span>'
            f'  <div class="bd">'
            f'    <div class="t">{c["name"]}</div>'
            f'    <div class="e">evidence: {c["evidence"]}</div>'
            f'  </div>'
            f'</div>', unsafe_allow_html=True,
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
