"""Experiment Arm Policy Behaviors & Execution Controls (ADR-0011, 07_EXPERIMENT_METHODOLOGY).

Defines exact treatment configurations for all 5 pre-registered arms + CONTROL baseline:
- CONTROL: NO_ACTION baseline (uncontacted counterfactual)
- A1:   Independent rules  — no Stage 0 gate, no downtime signal, heuristic scorer
- A2ns: Unified engine     — shared ledger arbitration, NO Stage 0 gate, no downtime signal
- A2:   Unified engine     — shared ledger + Stage 0 gate, NO downtime signal
- A3:   Unified engine     — shared ledger + Stage 0 + downtime signal, heuristic scorer
- A5:   Unified engine     — shared ledger + Stage 0 + downtime signal, CatBoost S-Learner

CRITICAL INVARIANT (ADR-0011):
    Arms MUST differ by real capability, never by label alone. Each arm below is built
    with a genuinely different orchestrator configuration. If two arms produce byte-identical
    metrics across a batch, the ablation is not measuring anything and the comparison is void.

    Each comparison isolates EXACTLY one capability:
        A2ns vs A1   -> shared ledger + arbitration       (D1)
        A2   vs A2ns -> Stage 0 validation gate           (D3)
        A3   vs A2   -> downtime-signal consumption       (D2)
        A5   vs A3   -> scoring function (model vs rules)
"""

from typing import Any, Dict, Optional

from app.domain.enums import DecisionMode, ExperimentArm, ActionType
from app.domain.models import EndToEndRecoveryResult, PaymentOutcome
from app.orchestration.recovery_orchestrator import RecoveryOrchestrator
from app.pipeline.downtime import NullDowntimeProvider, SimulatedDowntimeProvider
from app.scoring.engine import AIRecoveryDecisionEngine
from app.scoring.heuristic import HeuristicScorer
from app.scoring.dataset_generator import SyntheticDatasetGenerator  # noqa: F401  (legacy; see ADR-0017)
from app.scoring.logged_dataset import generate_logged_training_data
from app.scoring.s_learner import CatBoostSLearner

# Declarative arm configuration. This table IS the experiment design — a reviewer can
# read exactly what differs between any two arms without tracing code paths.
#
#   stage0_enabled  : Stage 0 may reject candidates (validation gate active)
#   downtime_signal : recovery layer consumes the gateway outage signal
#   scorer          : "heuristic" (rule-based) or "catboost" (S-Learner)
#   shared_ledger   : cross-stream arbitration under a shared contact budget
# Gateways that are in a simulated outage window during evaluation. Arms WITH the
# downtime signal see these as down; arms without it are blind to the same outage.
OUTAGE_GATEWAYS = ("razorpay_outage_sim",)

ARM_CONFIG: Dict[ExperimentArm, Dict[str, Any]] = {
    ExperimentArm.CONTROL: {
        "stage0_enabled": False, "downtime_signal": False,
        "scorer": "heuristic", "shared_ledger": False,
    },
    ExperimentArm.A1: {
        "stage0_enabled": False, "downtime_signal": False,
        "scorer": "heuristic", "shared_ledger": False,
    },
    ExperimentArm.A2NS: {
        "stage0_enabled": False, "downtime_signal": False,
        "scorer": "heuristic", "shared_ledger": True,
    },
    ExperimentArm.A2: {
        "stage0_enabled": True, "downtime_signal": False,
        "scorer": "heuristic", "shared_ledger": True,
    },
    ExperimentArm.A3: {
        "stage0_enabled": True, "downtime_signal": True,
        "scorer": "heuristic", "shared_ledger": True,
    },
    ExperimentArm.A5: {
        "stage0_enabled": True, "downtime_signal": True,
        "scorer": "catboost", "shared_ledger": True,
    },
}



# Module-level cache: the model is trained once and PINNED for the whole run, so the
# artifact is constant across every arm and every seed (07_EXPERIMENT_METHODOLOGY).
_CATBOOST_SINGLETON: Optional[CatBoostSLearner] = None
CATBOOST_TRAIN_SEED = 42
CATBOOST_TRAIN_SAMPLES = 400


def _fitted_catboost() -> CatBoostSLearner:
    """Return the single fitted S-Learner, training it on first use.

    TRAINED ON THE ENGINE'S OWN LOGGED OUTCOMES (ADR-0017).

    It previously trained on SyntheticDatasetGenerator, whose hand-authored probability
    table disagrees with the sandbox the model is graded in — RECOMMEND_RETRY sits near the
    bottom of that table (~0.27) and is the second-best action in the simulator (0.65). The
    model learned that world faithfully and was then scored in a different one, while the
    heuristic's baselines happened to match the grading world's ordering. "The AI loses" was
    a train/serve mismatch, not a fact about the model.

    Labels now come from replaying training opportunities through the real pipeline and
    sandbox, on a batch seed and outcome seeds DISJOINT from evaluation's (ADR-0005). The
    simulator's probabilities are untouched: this changes where the labels come from, never
    what they are.
    """
    global _CATBOOST_SINGLETON
    if _CATBOOST_SINGLETON is None:
        learner = CatBoostSLearner()
        training_data = generate_logged_training_data()
        learner.fit(training_data)
        _CATBOOST_SINGLETON = learner
    return _CATBOOST_SINGLETON


def build_orchestrator_for_arm(arm: ExperimentArm) -> RecoveryOrchestrator:
    """Construct an orchestrator whose capabilities match the arm's declared configuration."""
    cfg = ARM_CONFIG[arm]

    if cfg["downtime_signal"]:
        # Arms consuming the downtime signal are told which gateways are in an outage
        # window. Arms without the signal get NullDowntimeProvider and are blind to it —
        # the outage still occurs, they simply cannot see it. That asymmetry IS the
        # A3 vs A2 measurement.
        sim_downtime = SimulatedDowntimeProvider()
        for gw in OUTAGE_GATEWAYS:
            sim_downtime.set_outage(gw, is_down=True)
        downtime_provider: Any = sim_downtime
    else:
        downtime_provider = NullDowntimeProvider()

    if cfg["scorer"] == "catboost":
        # A5 uses a FITTED model. An unfitted CatBoost falls back to the same hand-written
        # baselines the heuristic uses, which would make A5 vs A3 measure nothing (the two
        # scorers would return identical probabilities). Training is what makes the
        # comparison a real test of the model rather than of its cold-start table.
        # Trained on outcomes logged from the engine's own sandbox (ADR-0017), using
        # batch seed 7 and outcome seeds 1-10 — disjoint from evaluation's batch seed 42
        # and seeds 21-40. See ADR-0005 for the seed-disjointness rule.
        learner: Any = _fitted_catboost()
        model_version = "v1.0.0-catboost"
    else:
        learner = HeuristicScorer()
        model_version = "v1.0.0-heuristic"

    ai_engine = AIRecoveryDecisionEngine(learner=learner, model_version=model_version)

    return RecoveryOrchestrator(
        downtime_provider=downtime_provider,
        ai_engine=ai_engine,
        stage0_enabled=cfg["stage0_enabled"],
        shared_ledger_enabled=cfg["shared_ledger"],
    )


class ExperimentPolicyController:
    """Executes closed-loop recovery orchestration under specific ExperimentArm constraints."""

    def __init__(self, orchestrator: Optional[RecoveryOrchestrator] = None) -> None:
        # An explicitly injected orchestrator is honoured (tests, sandbox). Otherwise a
        # per-arm orchestrator is built and cached on first use.
        self._injected = orchestrator
        self.orchestrator = orchestrator or build_orchestrator_for_arm(ExperimentArm.A5)
        self._arm_cache: Dict[ExperimentArm, RecoveryOrchestrator] = {}

    def _orchestrator_for(self, arm: ExperimentArm) -> RecoveryOrchestrator:
        if self._injected is not None:
            return self._injected
        if arm not in self._arm_cache:
            self._arm_cache[arm] = build_orchestrator_for_arm(arm)
        return self._arm_cache[arm]

    def execute_arm_policy(
        self,
        raw_event: Dict[str, Any],
        arm: ExperimentArm,
        random_seed: int = 42,
        force_sandbox_outcome: Optional[PaymentOutcome] = None,
        decision_timestamp: Optional[str] = None,
    ) -> EndToEndRecoveryResult:
        """Execute closed-loop orchestration under the exact capabilities mandated by the arm.

        `decision_timestamp` gives the batch a TIME AXIS. Without one, every decision in a
        run happens at wall-clock now, microseconds apart, and any quiet-period rule is
        permanently active - which would make compliant escalation untestable and would
        silently freeze the intensity ladder. Callers that model elapsed time pass it; the
        default remains the clock, matching production.
        """
        orch = self._orchestrator_for(arm)

        if arm == ExperimentArm.CONTROL:
            # CONTROL is the uncontacted counterfactual: it always abstains.
            force_mode: Optional[DecisionMode] = DecisionMode.SAFE_ABSTENTION
        elif arm == ExperimentArm.A5:
            # A5 alone runs the standard AI path including epsilon-exploration.
            force_mode = None
        else:
            # All other arms exploit their own scorer deterministically (no exploration),
            # so the A5 vs A3 comparison isolates the scorer plus its exploration policy.
            force_mode = DecisionMode.EXPLOIT

        return orch.process_and_execute(
            raw_event=raw_event,
            force_mode=force_mode,
            force_sandbox_outcome=force_sandbox_outcome,
            random_seed=random_seed,
            arm=arm.value,
            decision_timestamp=decision_timestamp or raw_event.get("decision_timestamp"),
        )
