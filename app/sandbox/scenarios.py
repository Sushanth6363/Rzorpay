"""Golden Demo Scenarios & Data Generator for Unified Recovery Engine (M8 Judge Audit).

Provides 12 pre-configured, deterministic golden scenarios exercising all major branches of
the architecture (Stage 0, Stage 1, Hard Safety Filters, AI Decisions, Contact Ledger,
Sandbox Execution, Reconciliation, Attribution, and Multi-Tenant Isolation).
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from app.domain.enums import ActionType, PaymentOutcome, DecisionMode
from app.orchestration.recovery_orchestrator import RecoveryOrchestrator, EndToEndRecoveryResult
from app.pipeline.downtime import SimulatedDowntimeProvider


@dataclass
class DemoScenarioSpec:
    """Specification for a judge-explorable demo scenario."""

    scenario_id: str
    title: str
    description: str
    raw_event: Dict[str, Any]
    force_sandbox_outcome: Optional[PaymentOutcome] = None
    force_mode: Optional[DecisionMode] = None
    simulate_outage_gateway: Optional[str] = None
    exhaust_contact_budget_customer: Optional[str] = None
    random_seed: int = 42


# Pre-defined catalog of 12 Judge Golden Scenarios
GOLDEN_DEMO_SCENARIOS: Dict[str, DemoScenarioSpec] = {
    "SCENARIO_01_SUCCESSFUL_RETRY": DemoScenarioSpec(
        scenario_id="SCENARIO_01_SUCCESSFUL_RETRY",
        title="1. Successful Payment Retry Recovery",
        description="Payment failure due to transient network error. Stage 0/1 pass, AI recommends retry, sandbox executes successfully, 100% recovery value attributed to AI.",
        raw_event={
            "merchant_id": "merchant_alpha",
            "customer_id": "cust_101",
            "event_id": "evt_s01",
            "amount_paise": 1500000,  # ₹15,000
            "gateway": "RAZORPAY",
            "error_code": "NETWORK_ERROR",
        },
        force_sandbox_outcome=PaymentOutcome.PAYMENT_SUCCESS,
        force_mode=DecisionMode.EXPLOIT,
    ),

    "SCENARIO_02_REMINDER_RECOVERY": DemoScenarioSpec(
        scenario_id="SCENARIO_02_REMINDER_RECOVERY",
        title="2. WhatsApp Customer Outreach Recovery",
        description="Payment failure due to insufficient funds. Retry is ineligible, AI recommends WhatsApp link. Customer pays via link; attributed recovery recorded.",
        raw_event={
            "merchant_id": "merchant_alpha",
            "customer_id": "cust_102",
            "event_id": "evt_s02",
            "amount_paise": 500000,  # ₹5,000
            "gateway": "HDFC",
            "error_code": "INSUFFICIENT_FUNDS",
        },
        force_sandbox_outcome=PaymentOutcome.PAYMENT_SUCCESS,
        force_mode=DecisionMode.EXPLOIT,
    ),
    "SCENARIO_03_NATURAL_SELF_CURE": DemoScenarioSpec(
        scenario_id="SCENARIO_03_NATURAL_SELF_CURE",
        title="3. Natural Baseline Self-Cure (NO_ACTION)",
        description="Low amount failure or uncontacted baseline. AI selects NO_ACTION. Customer self-cures independently. Attribution engine records ₹0 AI Attribution (INV-8).",
        raw_event={
            "merchant_id": "merchant_alpha",
            "customer_id": "cust_103",
            "event_id": "evt_s03",
            "amount_paise": 10000,  # ₹100
            "gateway": "RAZORPAY",
            "error_code": "CUSTOMER_ABORTED",
        },
        force_sandbox_outcome=PaymentOutcome.SELF_CURED,
        force_mode=DecisionMode.SAFE_ABSTENTION,
    ),
    "SCENARIO_04_SELF_CURE_BEFORE_DELIVERY": DemoScenarioSpec(
        scenario_id="SCENARIO_04_SELF_CURE_BEFORE_DELIVERY",
        title="4. Customer Pays Before Outreach Delivery",
        description="Intervention scheduled but customer pays before delivery. Attribution classifies payment as SELF_CURED and charges ₹0 AI Attribution.",
        raw_event={
            "merchant_id": "merchant_alpha",
            "customer_id": "cust_104",
            "event_id": "evt_s04",
            "amount_paise": 800000,  # ₹8,000
            "gateway": "ICICI",
            "error_code": "AUTHENTICATION_FAILED",
        },
        force_sandbox_outcome=PaymentOutcome.SELF_CURED,
        force_mode=DecisionMode.EXPLOIT,
    ),
    "SCENARIO_05_GATEWAY_OUTAGE": DemoScenarioSpec(
        scenario_id="SCENARIO_05_GATEWAY_OUTAGE",
        title="5. Known Gateway Outage (Hard Safety Suppression)",
        description="Active outage on HDFC gateway. Hard safety filter rejects retry candidates regardless of AI expected value (INV-4). Engine safely abstains.",
        raw_event={
            "merchant_id": "merchant_alpha",
            "customer_id": "cust_105",
            "event_id": "evt_s05",
            "amount_paise": 1200000,  # ₹12,000
            "gateway": "HDFC",
            "error_code": "GATEWAY_TIMEOUT",
        },
        simulate_outage_gateway="HDFC",
    ),
    "SCENARIO_06_CONTACT_BUDGET_EXHAUSTED": DemoScenarioSpec(
        scenario_id="SCENARIO_06_CONTACT_BUDGET_EXHAUSTED",
        title="6. Exhausted Customer Contact Budget",
        description="Customer has reached maximum contact cap (e.g. 5 attempts). Atomic reservation fails (INV-2). System prevents customer spamming.",
        raw_event={
            "merchant_id": "merchant_alpha",
            "customer_id": "cust_cap_exhausted",
            "event_id": "evt_s06",
            "amount_paise": 600000,  # ₹6,000
            "gateway": "RAZORPAY",
            "error_code": "PAYMENT_FAILED",
        },
        exhaust_contact_budget_customer="cust_cap_exhausted",
    ),
    "SCENARIO_07_DUPLICATE_EVENT": DemoScenarioSpec(
        scenario_id="SCENARIO_07_DUPLICATE_EVENT",
        title="7. Duplicate Event Idempotency Check",
        description="Identical event_id submitted twice. Idempotency layer detects duplicate, returning cached opportunity without re-evaluating or re-reserving budget.",
        raw_event={
            "merchant_id": "merchant_alpha",
            "customer_id": "cust_107",
            "event_id": "evt_s07_dup",
            "amount_paise": 400000,  # ₹4,000
            "gateway": "RAZORPAY",
            "error_code": "NETWORK_ERROR",
        },
        force_sandbox_outcome=PaymentOutcome.PAYMENT_SUCCESS,
        force_mode=DecisionMode.EXPLOIT,
    ),
    "SCENARIO_08_EXECUTION_UNKNOWN_DELIVERED": DemoScenarioSpec(
        scenario_id="SCENARIO_08_EXECUTION_UNKNOWN_DELIVERED",
        title="8. Execution Unknown → Reconciled Delivered",
        description="Outreach execution status is ambiguous (EXECUTION_UNKNOWN). Reconciliation checks status and confirms delivery (INV-6). Slot retained.",
        raw_event={
            "merchant_id": "merchant_alpha",
            "customer_id": "cust_108",
            "event_id": "evt_s08",
            "amount_paise": 700000,  # ₹7,000
            "gateway": "RAZORPAY",
            "error_code": "NETWORK_ERROR",
        },
        force_sandbox_outcome=PaymentOutcome.EXECUTION_UNKNOWN,
        force_mode=DecisionMode.EXPLOIT,
    ),
    "SCENARIO_09_EXECUTION_UNKNOWN_NOT_SENT": DemoScenarioSpec(
        scenario_id="SCENARIO_09_EXECUTION_UNKNOWN_NOT_SENT",
        title="9. Execution Unknown → Reconciled Not Sent",
        description="Ambiguous execution reconciles as NOT_SENT. Reserved contact slot is safely released back to customer budget.",
        raw_event={
            "merchant_id": "merchant_alpha",
            "customer_id": "cust_109",
            "event_id": "evt_s09",
            "amount_paise": 900000,  # ₹9,000
            "gateway": "RAZORPAY",
            "error_code": "NETWORK_ERROR",
        },
        force_sandbox_outcome=PaymentOutcome.EXECUTION_UNKNOWN,
        force_mode=DecisionMode.EXPLOIT,
    ),
    "SCENARIO_10_EXECUTION_UNKNOWN_UNRESOLVED": DemoScenarioSpec(
        scenario_id="SCENARIO_10_EXECUTION_UNKNOWN_UNRESOLVED",
        title="10. Execution Unknown → Conservative Unresolved Slot Hold",
        description="Ambiguous execution cannot be resolved. System conservatively treats slot as consumed to prevent duplicate intervention spamming (ADR-0009).",
        raw_event={
            "merchant_id": "merchant_alpha",
            "customer_id": "cust_110",
            "event_id": "evt_s10",
            "amount_paise": 1100000,  # ₹11,000
            "gateway": "RAZORPAY",
            "error_code": "NETWORK_ERROR",
        },
        force_sandbox_outcome=PaymentOutcome.EXECUTION_UNKNOWN,
        force_mode=DecisionMode.EXPLOIT,
    ),
    "SCENARIO_11_CROSS_TENANT_ISOLATION": DemoScenarioSpec(
        scenario_id="SCENARIO_11_CROSS_TENANT_ISOLATION",
        title="11. Multi-Tenant Budget & Feature Isolation",
        description="Identical customer ID at Merchant Alpha and Merchant Beta receive completely isolated contact budgets and model decisions (INV-1).",
        raw_event={
            "merchant_id": "merchant_beta",
            "customer_id": "cust_101",  # Same customer ID as Scenario 1, different merchant!
            "event_id": "evt_s11",
            "amount_paise": 1500000,
            "gateway": "RAZORPAY",
            "error_code": "GATEWAY_TIMEOUT",
        },
        force_sandbox_outcome=PaymentOutcome.PAYMENT_SUCCESS,
        force_mode=DecisionMode.EXPLOIT,
    ),
    "SCENARIO_12_NEGATIVE_EV_ABSTENTION": DemoScenarioSpec(
        scenario_id="SCENARIO_12_NEGATIVE_EV_ABSTENTION",
        title="12. Negative EV Action Rejection (Safe Abstention)",
        description="Intervention cost exceeds predicted incremental recovery value. AI decision engine rejects candidate actions and safely abstains (SAFE_ABSTENTION).",
        raw_event={
            "merchant_id": "merchant_alpha",
            "customer_id": "cust_112",
            "event_id": "evt_s12",
            "amount_paise": 500,  # ₹5 micro-transaction
            "gateway": "RAZORPAY",
            "error_code": "PAYMENT_FAILED",
        },
        force_sandbox_outcome=PaymentOutcome.NO_PAYMENT,
        force_mode=DecisionMode.SAFE_ABSTENTION,
    ),
}


class ScenarioRunner:
    """Executes demo scenarios against real RecoveryOrchestrator domain services."""

    def __init__(self, orchestrator: Optional[RecoveryOrchestrator] = None) -> None:
        self._custom_orchestrator = orchestrator

    def run_scenario(self, scenario_spec: DemoScenarioSpec) -> EndToEndRecoveryResult:
        """Run a scenario spec through the closed-loop orchestrator."""
        downtime_provider = SimulatedDowntimeProvider()
        orchestrator = self._custom_orchestrator or RecoveryOrchestrator(downtime_provider=downtime_provider)

        # 1. Handle downtime simulation if specified
        if scenario_spec.simulate_outage_gateway:
            downtime_provider.set_outage(
                gateway_name=scenario_spec.simulate_outage_gateway,
                is_down=True,
            )
        else:
            downtime_provider.set_outage(
                gateway_name="HDFC",
                is_down=False,
            )

        # 2. Handle contact budget exhaustion pre-loading if specified
        if scenario_spec.exhaust_contact_budget_customer:
            raw_exhaust = {
                "merchant_id": scenario_spec.raw_event["merchant_id"],
                "customer_id": scenario_spec.exhaust_contact_budget_customer,
                "event_id": "pre_exhaust_evt",
                "amount_paise": 100000,
            }
            # Pre-consume 5 slots to exhaust budget
            for i in range(5):
                raw_exhaust["event_id"] = f"pre_exhaust_{i}"
                orchestrator.process_and_execute(
                    raw_event=raw_exhaust,
                    random_seed=scenario_spec.random_seed,
                )

        # 3. Execute main scenario event
        result = orchestrator.process_and_execute(
            raw_event=scenario_spec.raw_event,
            force_mode=scenario_spec.force_mode,
            force_sandbox_outcome=scenario_spec.force_sandbox_outcome,
            random_seed=scenario_spec.random_seed,
        )

        return result

