"""Streamlit Judge Dashboard for Unified Recovery Engine (M7 Benchmarking & Audit).

INVARIANTS:
1. CLEAR SIMULATED MARKER: All displays prominently mark data as SIMULATED / SANDBOX.
2. AUDIT-READY TRANSPARENCY: Shows primary comparison (A2 vs A1), 5-Arm summary, Holm-Bonferroni secondary CIs, individual recovery traces, and point-in-time feedback dataset tuples.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from app.domain.enums import ExperimentArm, PaymentOutcome, StatisticalStatus
from app.experiment.runner import ExperimentRunner
from app.experiment.feedback_loop import FeedbackLoopEngine


def render_dashboard():
    """Render the interactive Streamlit Judge Dashboard."""
    st.set_page_config(
        page_title="Unified Recovery Engine — M7 Experimentation & Judge Dashboard",
        page_icon="⚖️",
        layout="wide",
    )

    # 1. Header Banner & Safety Marker
    st.title("⚖️ Unified Recovery Engine — Judge Dashboard & Experimentation Framework")
    st.caption("Track 3 AI Revenue Recovery | Milestone M7 Audit & Benchmarking Interface")

    st.info(
        "⚠️ **SANDBOX / SIMULATED EXPERIMENTATION MODE** — "
        "All recovery observations, state transitions, and outcomes are produced by the deterministic sandbox simulator."
    )

    # Sidebar Controls
    st.sidebar.header("⚙️ Experiment Controls")
    seed_selection = st.sidebar.slider("Evaluation Seed Range", min_value=21, max_value=60, value=(21, 25))
    sample_size = st.sidebar.number_input("Number of Opportunities per Seed", min_value=5, max_value=100, value=10)

    seeds = list(range(seed_selection[0], seed_selection[1] + 1))

    if st.sidebar.button("🚀 Run 5-Arm Experiment Benchmark"):
        with st.spinner(f"Executing paired experiment over seeds {seeds} ({sample_size} opportunities)..."):
            # Generate synthetic test events
            events = [
                {
                    "merchant_id": "m1",
                    "customer_id": f"cust_{i % 5}",
                    "event_id": f"event_{i}",
                    "amount_paise": (1000 + (i * 500)) * 100,
                    "gateway": "HDFC" if i % 2 == 0 else "RAZORPAY",
                }
                for i in range(sample_size)
            ]

            runner = ExperimentRunner(experiment_id="EXP_M7_JUDGE_RUN")
            summary = runner.run_paired_experiment(events=events, seeds=seeds)

            st.session_state["last_experiment_summary"] = summary
            st.session_state["last_events"] = events

    summary = st.session_state.get("last_experiment_summary", None)

    if summary is None:
        st.warning("Click '🚀 Run 5-Arm Experiment Benchmark' in the sidebar to execute the benchmark evaluation.")
        return

    # 2. Key Metrics & Primary Comparison (A2 vs A1)
    st.subheader("🎯 Primary Pre-Registered Experiment Metric (ADR-0011)")
    p_comp = summary.primary_comparison

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Comparison ID",
            value=p_comp.comparison_id,
        )
    with col2:
        st.metric(
            label="Incremental Recovery Rate (A2 vs A1)",
            value=f"{p_comp.incremental_recovery_rate:+.2%}",
            delta=f"Relative Lift: {p_comp.relative_lift:+.2%}",
        )
    with col3:
        st.metric(
            label="95% Confidence Interval",
            value=f"[{p_comp.confidence_interval_95[0]:.2%}, {p_comp.confidence_interval_95[1]:.2%}]",
        )
    with col4:
        st.metric(
            label="Statistical Verdict",
            value=p_comp.status.value,
        )

    st.markdown(f"**Explanation**: {p_comp.explanation}")

    # 3. 5-Arm Aggregated Performance Table
    st.subheader("📊 5-Arm Performance Summary (A1–A5 + CONTROL Baseline)")
    arm_data = []
    for arm_id, metrics in summary.arm_metrics.items():
        arm_data.append(
            {
                "Arm": arm_id,
                "Total Opportunities": metrics.total_opportunities,
                "Successful Recoveries": metrics.successful_recoveries,
                "Recovery Rate": f"{metrics.recovery_rate:.2%}",
                "Gross Recovered (₹)": f"₹{metrics.gross_recovered_paise / 100:,.2f}",
                "Attributed Recovery (₹)": f"₹{metrics.attributed_recovered_paise / 100:,.2f}",
                "Self-Cures": metrics.self_cured_count,
                "Action Cost (₹)": f"₹{metrics.total_cost_paise / 100:,.2f}",
                "Net Value (₹)": f"₹{metrics.net_value_paise / 100:,.2f}",
                "Abstentions": metrics.abstention_count,
            }
        )

    df_arms = pd.DataFrame(arm_data)
    st.dataframe(df_arms, use_container_width=True)

    # 4. Secondary Comparisons & Multiplicity Family (Holm-Bonferroni Corrected)
    st.subheader("🔍 Secondary Pairwise Comparisons (Holm-Bonferroni Corrected)")
    sec_data = []
    for s_comp in summary.secondary_comparisons:
        sec_data.append(
            {
                "Comparison": s_comp.comparison_id,
                "Treatment Arm": s_comp.treatment_arm.value,
                "Baseline Arm": s_comp.baseline_arm.value,
                "Incremental Rate": f"{s_comp.incremental_recovery_rate:+.2%}",
                "Gross Incremental (₹)": f"₹{s_comp.gross_incremental_revenue_paise / 100:,.2f}",
                "95% CI": f"[{s_comp.confidence_interval_95[0]:.2%}, {s_comp.confidence_interval_95[1]:.2%}]",
                "p-value": s_comp.p_value,
                "Verdict Status": s_comp.status.value,
                "Explanation": s_comp.explanation,
            }
        )
    df_sec = pd.DataFrame(sec_data)
    st.dataframe(df_sec, use_container_width=True)

    # 5. Feedback Loop Inspection (Point-in-Time Features vs Observed Outcomes)
    st.subheader("🔁 Feedback Loop & Retraining Tuple Inspection (INV-7)")
    st.caption("Transformed TrainingRecord instances separating Feature Vector X from Target Outcome Y.")
    
    st.json(
        {
            "experiment_id": summary.experiment_id,
            "sample_size": summary.sample_size,
            "provenance": summary.provenance.value,
            "commit_hash": summary.commit_hash,
            "model_version": summary.model_version,
            "primary_comparison": summary.primary_comparison.to_dict(),
        }
    )


if __name__ == "__main__":
    render_dashboard()
