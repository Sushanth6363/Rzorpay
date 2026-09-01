"""Experiment Arm Policy Behaviors & Execution Controls (ADR-0011, 07_EXPERIMENT_METHODOLOGY).

Defines exact treatment configurations for all 5 pre-registered arms + CONTROL baseline:
- CONTROL: NO_ACTION baseline (uncontacted counterfactual)
- A1: Independent rules (no shared ledger arbitration, no Stage 0 validation, no downtime signal)
- A2ns: Unified engine with shared ledger arbitration, but NO Stage 0 validation and no downtime signal
- A2: Unified engine with shared ledger arbitration + Stage 0 validation, but NO downtime signal
- A3: Unified engine with shared ledger arbitration + Stage 0 validation + Downtime signal (Heuristic scoring)
- A5: Unified engine with shared ledger arbitration + Stage 0 validation + Downtime signal + CatBoost S-Learner AI Scoring Engine
"""

from typing import Dict, Any, Optional
from app.domain.enums import DecisionMode, ExperimentArm, ActionType
from app.domain.models import EndToEndRecoveryResult, PaymentOutcome
from app.orchestration.recovery_orchestrator import RecoveryOrchestrator


class ExperimentPolicyController:
    """Executes closed-loop recovery orchestration under specific ExperimentArm policy constraints."""

    def __init__(self, orchestrator: Optional[RecoveryOrchestrator] = None) -> None:
        self.orchestrator = orchestrator or RecoveryOrchestrator()

    def execute_arm_policy(
        self,
        raw_event: Dict[str, Any],
        arm: ExperimentArm,
        random_seed: int = 42,
        force_sandbox_outcome: Optional[PaymentOutcome] = None,
    ) -> EndToEndRecoveryResult:
        """Execute closed-loop orchestration under the exact behavior mandated by the assigned ExperimentArm."""
        if arm == ExperimentArm.CONTROL:
            # CONTROL baseline strictly selects NO_ACTION
            return self.orchestrator.process_and_execute(
                raw_event=raw_event,
                force_mode=DecisionMode.SAFE_ABSTENTION,
                force_sandbox_outcome=force_sandbox_outcome,
                random_seed=random_seed,
                arm=arm.value,
            )

        elif arm == ExperimentArm.A1:
            # A1: Baseline Independent Rules (no Stage 0, no downtime signal, independent retry policy)
            return self.orchestrator.process_and_execute(
                raw_event=raw_event,
                force_mode=DecisionMode.EXPLOIT,
                force_sandbox_outcome=force_sandbox_outcome,
                random_seed=random_seed,
                arm=arm.value,
            )

        elif arm == ExperimentArm.A2NS:
            # A2ns: Unified Shared Ledger, but NO Stage 0 Validation
            return self.orchestrator.process_and_execute(
                raw_event=raw_event,
                force_mode=DecisionMode.EXPLOIT,
                force_sandbox_outcome=force_sandbox_outcome,
                random_seed=random_seed,
                arm=arm.value,
            )

        elif arm == ExperimentArm.A2:
            # A2: Unified Shared Ledger + Stage 0 Validation, NO Downtime Signal
            return self.orchestrator.process_and_execute(
                raw_event=raw_event,
                force_mode=DecisionMode.EXPLOIT,
                force_sandbox_outcome=force_sandbox_outcome,
                random_seed=random_seed,
                arm=arm.value,
            )

        elif arm == ExperimentArm.A3:
            # A3: Unified Shared Ledger + Stage 0 + Downtime Signal (Heuristic)
            return self.orchestrator.process_and_execute(
                raw_event=raw_event,
                force_mode=DecisionMode.EXPLOIT,
                force_sandbox_outcome=force_sandbox_outcome,
                random_seed=random_seed,
                arm=arm.value,
            )

        elif arm == ExperimentArm.A5:
            # A5: Full AI Decision Engine (CatBoost S-Learner, Epsilon Exploration)
            return self.orchestrator.process_and_execute(
                raw_event=raw_event,
                force_mode=None,  # Standard AI evaluation with exploration
                force_sandbox_outcome=force_sandbox_outcome,
                random_seed=random_seed,
                arm=arm.value,
            )

        else:
            # Fallback safe default
            return self.orchestrator.process_and_execute(
                raw_event=raw_event,
                force_mode=DecisionMode.SAFE_ABSTENTION,
                random_seed=random_seed,
                arm=arm.value,
            )

