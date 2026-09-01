"""Deterministic Experiment Arm Assignment Engine (ADR-0011, 07_EXPERIMENT_METHODOLOGY).

INVARIANTS:
1. INV-1 Tenant Isolation: Merchant ID is included in assignment hash salt; cross-merchant customers are assigned independently.
2. DETERMINISTIC SEED REPRODUCIBILITY: Identical (experiment_id, merchant_id, customer_id, opportunity_id, seed) produces 100% reproducible ExperimentArm.
3. ZERO OUTCOME LEAKAGE: Assignment occurs prior to execution and is completely independent of customer payment outcomes.
4. HARD SAFETY FILTER RESPECTED: Arm assignment selects decision policy; hard safety filters remain downstream and non-overridable (INV-3).
"""

import hashlib
from typing import List, Optional
from app.domain.enums import ExperimentArm


class ExperimentAssigner:
    """Handles cryptographic deterministic experiment arm assignment."""

    def __init__(
        self,
        experiment_id: str = "EXP_M7_CANONICAL_V1",
        active_arms: Optional[List[ExperimentArm]] = None,
    ) -> None:
        self.experiment_id = experiment_id
        self.active_arms = active_arms or [
            ExperimentArm.CONTROL,
            ExperimentArm.A1,
            ExperimentArm.A2NS,
            ExperimentArm.A2,
            ExperimentArm.A3,
            ExperimentArm.A5,
        ]

    def assign_arm(
        self,
        merchant_id: str,
        customer_id: str,
        opportunity_id: str,
        seed: int = 42,
    ) -> ExperimentArm:
        """Deterministically map an opportunity to an ExperimentArm using SHA256 hashing."""
        raw_key = f"{self.experiment_id}|{merchant_id}|{customer_id}|{opportunity_id}|{seed}"
        hash_digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        integer_val = int(hash_digest[:8], 16)
        
        index = integer_val % len(self.active_arms)
        return self.active_arms[index]
