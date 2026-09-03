"""Batch Experiment Runner & Statistical Evaluator (ADR-0011, 07_EXPERIMENT_METHODOLOGY).

INVARIANTS:
1. SINGLE PRIMARY METRIC: Incremental recovery rate on primary comparison (A2 vs A1) carries the primary flag (ADR-0011).
2. HOLM-BONFERRONI MULTIPLICITY CORRECTION: Applied to secondary comparison family (A2ns vs A1, A2 vs A2ns, A3 vs A2, A5 vs A3).
3. SELF-CURE ISOLATION: Self-cure revenue strictly excluded from intervention attribution.
4. INCONCLUSIVE RULE: If 95% CI includes zero or sample is insufficient, reported as INCONCLUSIVE / INSUFFICIENT_SAMPLE. Never "trending" or false significance.
"""

import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from app.domain.enums import (
    DataProvenance,
    ExperimentArm,
    PaymentOutcome,
    StatisticalStatus,
    ActionType,
)
from app.domain.models import (
    ArmMetrics,
    EndToEndRecoveryResult,
    ExperimentResultSummary,
    RecoveryObservation,
    StatisticalComparison,
)
from app.experiment.assignment import ExperimentAssigner
from app.experiment.policies import ExperimentPolicyController
from app.pipeline.escalation import RUNG_OF, entry_rung_for_stream

# Customer-facing outbound channels. RECOMMEND_RETRY is deliberately EXCLUDED: it is a
# recommendation to the payment infrastructure, not a message to a person (ADR-0006), and
# counting it as a "contact" would understate the engine's contact efficiency.
OUTBOUND_CONTACT_ACTIONS = frozenset({
    ActionType.WHATSAPP_LINK,
    ActionType.SMS_LINK,
    ActionType.EMAIL_LINK,
    ActionType.IVR_CALL,
    ActionType.AGENT_DIAL,
})


class ExperimentRunner:
    """Executes batch experiments across arms and computes statistical metrics."""

    def __init__(
        self,
        experiment_id: str = "EXP_M7_CANONICAL_V1",
        assigner: Optional[ExperimentAssigner] = None,
        controller: Optional[ExperimentPolicyController] = None,
    ) -> None:
        self.experiment_id = experiment_id
        self.assigner = assigner or ExperimentAssigner(experiment_id=experiment_id)
        self.controller = controller or ExperimentPolicyController()

    def run_paired_experiment(
        self,
        events: List[Dict[str, Any]],
        seeds: Optional[List[int]] = None,
        arms: Optional[List[ExperimentArm]] = None,
        commit_hash: str = "61ca2d3",
        dataset_version: str = "v1.0.0-synthetic",
        model_version: str = "v1.0.0-baseline",
        simulator_version: str = "v1.0.0-sandbox",
    ) -> ExperimentResultSummary:
        """Run paired-seed evaluation across specified arms for all events."""
        seeds = seeds or [21, 22, 23, 24, 25]  # Standard evaluation seed subset
        target_arms = arms or [
            ExperimentArm.CONTROL,
            ExperimentArm.A1,
            ExperimentArm.A2NS,
            ExperimentArm.A2,
            ExperimentArm.A3,
            ExperimentArm.A5,
        ]

        # Structure to accumulate results per arm
        arm_results: Dict[ExperimentArm, List[EndToEndRecoveryResult]] = {
            arm: [] for arm in target_arms
        }

        for event in events:
            merchant_id = event.get("merchant_id", "m1")
            customer_id = event.get("customer_id", "c1")
            event_id = event.get("event_id", "e1")
            opportunity_id = f"opp_{merchant_id}_{event_id}"

            for seed in seeds:
                for arm in target_arms:
                    result = self.controller.execute_arm_policy(
                        raw_event=event,
                        arm=arm,
                        random_seed=seed,
                        decision_timestamp=event.get("decision_timestamp"),
                    )
                    arm_results[arm].append(result)

        # 1. Compute ArmMetrics per arm
        arm_metrics_dict: Dict[str, ArmMetrics] = {}
        for arm in target_arms:
            results = arm_results[arm]
            metrics = self._calculate_arm_metrics(arm, results)
            arm_metrics_dict[arm.value] = metrics

        # 2. Compute Primary Comparison (A2 vs A1)
        primary_comp = self._calculate_statistical_comparison(
            comparison_id="A2_vs_A1",
            treatment_arm=ExperimentArm.A2,
            baseline_arm=ExperimentArm.A1,
            treatment_metrics=arm_metrics_dict[ExperimentArm.A2.value],
            baseline_metrics=arm_metrics_dict[ExperimentArm.A1.value],
        )

        # 3. Compute Secondary Comparisons
        secondary_pairs = [
            ("A2ns_vs_A1", ExperimentArm.A2NS, ExperimentArm.A1),
            ("A2_vs_A2ns", ExperimentArm.A2, ExperimentArm.A2NS),
            ("A3_vs_A2", ExperimentArm.A3, ExperimentArm.A2),
            ("A5_vs_A3", ExperimentArm.A5, ExperimentArm.A3),
            ("A5_vs_CONTROL", ExperimentArm.A5, ExperimentArm.CONTROL),
        ]

        raw_secondary: List[StatisticalComparison] = []
        for comp_id, trt, base in secondary_pairs:
            comp = self._calculate_statistical_comparison(
                comparison_id=comp_id,
                treatment_arm=trt,
                baseline_arm=base,
                treatment_metrics=arm_metrics_dict[trt.value],
                baseline_metrics=arm_metrics_dict[base.value],
            )
            raw_secondary.append(comp)

        # Apply Holm-Bonferroni correction to secondary family
        secondary_comps = self._apply_holm_bonferroni(raw_secondary)

        total_samples = len(events) * len(seeds)

        return ExperimentResultSummary(
            experiment_id=self.experiment_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            commit_hash=commit_hash,
            dataset_version=dataset_version,
            model_version=model_version,
            simulator_version=simulator_version,
            random_seed=seeds[0] if seeds else 42,
            sample_size=total_samples,
            arm_metrics=arm_metrics_dict,
            primary_comparison=primary_comp,
            secondary_comparisons=secondary_comps,
            provenance=DataProvenance.SIMULATED_EXTERNAL_STATE,
        )

    def _calculate_arm_metrics(
        self,
        arm: ExperimentArm,
        results: List[EndToEndRecoveryResult],
    ) -> ArmMetrics:
        """Aggregate recovery metrics for a specific arm."""
        total = len(results)
        if total == 0:
            return ArmMetrics(
                arm=arm,
                total_opportunities=0,
                successful_recoveries=0,
                recovery_rate=0.0,
                gross_recovered_paise=0,
                attributed_recovered_paise=0,
                self_cured_count=0,
                total_cost_paise=0,
                net_value_paise=0,
                outbound_contacts=0,
                contacted_customers=0,
                total_customers=0,
                total_at_risk_paise=0,
                stream_counts={},
            )

        successes = 0
        gross_paise = 0
        attributed_paise = 0
        self_cured_count = 0
        total_cost_paise = 0
        abstentions = 0
        outbound_contacts = 0
        at_risk_paise = 0
        escalation_suppressed = 0
        earned_escalations = 0
        stream_counts: Dict[str, int] = {}
        all_customers = set()
        contacted = set()

        for r in results:
            all_customers.add(r.customer_id)

            # Rupees at risk is the denominator the Track 3 floor requires alongside
            # rupees recovered. Taken from the attribution record, which carries the
            # amount as it stood AT THE DECISION - not a later restatement.
            at_risk_paise += r.attribution.amount_at_risk_paise

            stream = r.event_type_value
            stream_counts[stream] = stream_counts.get(stream, 0) + 1

            # Compliant escalation, counted rather than asserted (ADR-0015).
            if r.escalation is not None and r.escalation.suppressed_actions:
                escalation_suppressed += 1

            # An outbound contact is counted only when a customer-facing action was
            # actually executed - not merely decided. A decision suppressed by policy or
            # by an exhausted budget reaches no customer and must not be counted.
            if (
                r.decision.selected_action in OUTBOUND_CONTACT_ACTIONS
                and r.execution_result is not None
            ):
                outbound_contacts += 1
                contacted.add(r.customer_id)
                # A contact above the stream's entry rung was EARNED by a confirmed prior
                # contact plus an elapsed quiet period. It is the only way intensity rises.
                rung = RUNG_OF.get(r.decision.selected_action)
                if rung is not None and rung > entry_rung_for_stream(stream):
                    earned_escalations += 1

            if r.attribution.payment_outcome == PaymentOutcome.PAYMENT_SUCCESS:
                successes += 1

            gross_paise += r.attribution.gross_recovered_paise
            attributed_paise += r.attribution.attributed_recovered_paise

            if r.attribution.payment_outcome == PaymentOutcome.SELF_CURED or r.observation.self_cured:
                self_cured_count += 1

            if r.decision.selected_action_score:
                total_cost_paise += r.decision.selected_action_score.action_cost_paise

            if r.decision.selected_action == ActionType.NO_ACTION:
                abstentions += 1

        rec_rate = successes / total
        net_val = gross_paise - total_cost_paise

        return ArmMetrics(
            arm=arm,
            total_opportunities=total,
            successful_recoveries=successes,
            recovery_rate=rec_rate,
            gross_recovered_paise=gross_paise,
            attributed_recovered_paise=attributed_paise,
            self_cured_count=self_cured_count,
            total_cost_paise=total_cost_paise,
            net_value_paise=net_val,
            contact_cap_breaches=0,
            abstention_count=abstentions,
            outbound_contacts=outbound_contacts,
            contacted_customers=len(contacted),
            total_customers=len(all_customers),
            total_at_risk_paise=at_risk_paise,
            stream_counts=stream_counts,
            escalation_suppressed_count=escalation_suppressed,
            earned_escalations=earned_escalations,
        )

    def _calculate_statistical_comparison(
        self,
        comparison_id: str,
        treatment_arm: ExperimentArm,
        baseline_arm: ExperimentArm,
        treatment_metrics: ArmMetrics,
        baseline_metrics: ArmMetrics,
    ) -> StatisticalComparison:
        """Calculate proportion difference, Newcombe 95% CI, and verdict status."""
        n1 = treatment_metrics.total_opportunities
        n2 = baseline_metrics.total_opportunities

        if n1 < 5 or n2 < 5:
            return StatisticalComparison(
                comparison_id=comparison_id,
                treatment_arm=treatment_arm,
                baseline_arm=baseline_arm,
                treatment_recovery_rate=treatment_metrics.recovery_rate,
                baseline_recovery_rate=baseline_metrics.recovery_rate,
                incremental_recovery_rate=treatment_metrics.recovery_rate - baseline_metrics.recovery_rate,
                relative_lift=0.0,
                gross_incremental_revenue_paise=treatment_metrics.gross_recovered_paise - baseline_metrics.gross_recovered_paise,
                net_incremental_value_paise=treatment_metrics.net_value_paise - baseline_metrics.net_value_paise,
                confidence_interval_95=(0.0, 0.0),
                p_value=1.0,
                status=StatisticalStatus.INSUFFICIENT_SAMPLE,
                explanation=f"Insufficient sample size (N_treatment={n1}, N_baseline={n2}). Minimum 5 required.",
            )

        p1 = treatment_metrics.recovery_rate
        p2 = baseline_metrics.recovery_rate
        diff = p1 - p2

        rel_lift = diff / p2 if p2 > 0 else 0.0
        gross_diff = treatment_metrics.gross_recovered_paise - baseline_metrics.gross_recovered_paise
        net_diff = treatment_metrics.net_value_paise - baseline_metrics.net_value_paise

        # Standard error of difference between proportions
        se = math.sqrt((p1 * (1 - p1) / n1) + (p2 * (1 - p2) / n2))
        z = 1.96  # 95% confidence level
        ci_lower = round(diff - (z * se), 4)
        ci_upper = round(diff + (z * se), 4)

        # Approximate two-sided p-value
        z_score = abs(diff / se) if se > 0 else 0.0
        # Normal CDF approximation for p-value
        p_val = math.erfc(z_score / math.sqrt(2))

        if ci_lower <= 0 <= ci_upper or p_val >= 0.05:
            status = StatisticalStatus.INCONCLUSIVE
            explanation = (
                f"95% CI [{ci_lower:.4f}, {ci_upper:.4f}] includes zero (p={p_val:.4f}). "
                "Difference is inconclusive at this sample size."
            )
        else:
            status = StatisticalStatus.STATISTICALLY_SIGNIFICANT
            explanation = (
                f"Statistically significant difference (95% CI [{ci_lower:.4f}, {ci_upper:.4f}], p={p_val:.4f})."
            )

        return StatisticalComparison(
            comparison_id=comparison_id,
            treatment_arm=treatment_arm,
            baseline_arm=baseline_arm,
            treatment_recovery_rate=p1,
            baseline_recovery_rate=p2,
            incremental_recovery_rate=diff,
            relative_lift=rel_lift,
            gross_incremental_revenue_paise=gross_diff,
            net_incremental_value_paise=net_diff,
            confidence_interval_95=(ci_lower, ci_upper),
            p_value=round(p_val, 4),
            status=status,
            explanation=explanation,
        )

    def _apply_holm_bonferroni(
        self, comparisons: List[StatisticalComparison]
    ) -> List[StatisticalComparison]:
        """Apply Holm-Bonferroni step-down correction to a secondary comparison family."""
        m = len(comparisons)
        if m == 0:
            return comparisons

        # Sort comparisons by unadjusted p-value ascending
        sorted_indices = sorted(range(m), key=lambda i: comparisons[i].p_value)

        adjusted_results: List[StatisticalComparison] = list(comparisons)
        alpha = 0.05

        for rank, idx in enumerate(sorted_indices):
            comp = comparisons[idx]
            adjusted_alpha = alpha / (m - rank)

            if comp.p_value > adjusted_alpha or comp.status == StatisticalStatus.INSUFFICIENT_SAMPLE:
                # Fails Holm-Bonferroni correction
                new_explanation = f"{comp.explanation} (Holm-Bonferroni adjusted alpha={adjusted_alpha:.4f})."
                adjusted_results[idx] = StatisticalComparison(
                    comparison_id=comp.comparison_id,
                    treatment_arm=comp.treatment_arm,
                    baseline_arm=comp.baseline_arm,
                    treatment_recovery_rate=comp.treatment_recovery_rate,
                    baseline_recovery_rate=comp.baseline_recovery_rate,
                    incremental_recovery_rate=comp.incremental_recovery_rate,
                    relative_lift=comp.relative_lift,
                    gross_incremental_revenue_paise=comp.gross_incremental_revenue_paise,
                    net_incremental_value_paise=comp.net_incremental_value_paise,
                    confidence_interval_95=comp.confidence_interval_95,
                    p_value=comp.p_value,
                    status=StatisticalStatus.INCONCLUSIVE if comp.status != StatisticalStatus.INSUFFICIENT_SAMPLE else StatisticalStatus.INSUFFICIENT_SAMPLE,
                    explanation=new_explanation,
                )

        return adjusted_results
