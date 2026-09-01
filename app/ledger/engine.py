"""Atomic Contact Ledger & Reconciliation Engine for Unified Recovery Engine.

Exposes high-level intervention lifecycle control, deterministic idempotency, atomic reservation,
and bounded reconciliation semantics as specified in ADR-0003 and ADR-0006.
"""

import sqlite3
from typing import Any, Dict, List, Optional
from app.clock import Clock, SystemClock
from app.db.dal import TenantScopedDB, TenantScopeViolation
from app.domain.enums import ActionType, LedgerStatus
from app.domain.models import ContactLedgerEntry, CustomerContactBudget


class ContactLedgerEngine:
    """High-level API for managing intervention capacity, ledger lifecycles, and reconciliation."""

    def __init__(self, conn: sqlite3.Connection, merchant_id: str, clock: Optional[Clock] = None) -> None:
        self.dal = TenantScopedDB(conn=conn, merchant_id=merchant_id, clock=clock)
        self.merchant_id = merchant_id

    def reserve_contact(
        self,
        customer_id: str,
        opportunity_id: str,
        action_type: ActionType,
        intervention_idempotency_key: str,
        cap: int = 3,
    ) -> Optional[ContactLedgerEntry]:
        """Atomically reserve intervention capacity under customer cap and persist ledger entry.

        IDEMPOTENCY: Repeated calls with identical intervention_idempotency_key return existing
        ledger entry without consuming additional capacity.
        """
        return self.dal.reserve_contact_ledger(
            customer_id=customer_id,
            opportunity_id=opportunity_id,
            action_type=action_type,
            intervention_idempotency_key=intervention_idempotency_key,
            cap=cap,
        )

    def get_ledger_entry(self, ledger_id: str) -> Optional[ContactLedgerEntry]:
        """Retrieve ledger entry by ledger ID within active merchant tenant scope."""
        return self.dal.get_ledger_entry(ledger_id)

    def get_ledger_entry_by_key(self, intervention_idempotency_key: str) -> Optional[ContactLedgerEntry]:
        """Retrieve ledger entry by deterministic intervention key."""
        return self.dal.get_ledger_entry_by_idempotency_key(intervention_idempotency_key)

    def get_customer_history(self, customer_id: str) -> List[ContactLedgerEntry]:
        """Retrieve complete contact history for a customer."""
        return self.dal.get_customer_ledger_history(customer_id)

    def get_customer_budget(self, customer_id: str) -> Optional[CustomerContactBudget]:
        """Retrieve customer contact budget counters."""
        return self.dal.get_contact_budget(customer_id)

    def record_execution_attempt(self, ledger_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Mark intervention execution dispatch attempt."""
        return self.dal.transition_ledger_status(
            ledger_id=ledger_id,
            target_status=LedgerStatus.EXECUTION_ATTEMPTED,
            metadata=metadata,
        )

    def record_execution_result(
        self,
        ledger_id: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Record deterministic execution outcome (EXECUTED or FAILED_CLOSED)."""
        target = LedgerStatus.EXECUTED if success else LedgerStatus.FAILED_CLOSED
        return self.dal.transition_ledger_status(
            ledger_id=ledger_id,
            target_status=target,
            metadata=metadata,
        )

    def mark_execution_unknown(self, ledger_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Mark execution outcome as ambiguous/unknown (EXECUTION_UNKNOWN).

        INVARIANT (INV-6): Slot stays held in reserved_count. Counter state is unchanged.
        EXECUTION_UNKNOWN cannot automatically trigger re-execution.
        """
        return self.dal.transition_ledger_status(
            ledger_id=ledger_id,
            target_status=LedgerStatus.EXECUTION_UNKNOWN,
            metadata=metadata,
        )

    def reconcile(
        self,
        ledger_id: str,
        outcome: LedgerStatus,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Reconcile entry from EXECUTION_UNKNOWN to terminal state.

        Terminal options:
        - RECONCILED_DELIVERED: confirmed delivered (reserved -> consumed)
        - RECONCILED_NOT_SENT: confirmed not sent (reserved -> released, capacity returned)
        - RECONCILED_UNRESOLVED: fail-closed after timeout (reserved -> consumed, queued for human review)

        IDEMPOTENCE: Re-invoking reconcile on an already reconciled entry returns True without side-effects.
        """
        if outcome not in (
            LedgerStatus.RECONCILED_DELIVERED,
            LedgerStatus.RECONCILED_NOT_SENT,
            LedgerStatus.RECONCILED_UNRESOLVED,
        ):
            return False

        return self.dal.transition_ledger_status(
            ledger_id=ledger_id,
            target_status=outcome,
            expected_status=LedgerStatus.EXECUTION_UNKNOWN,
            metadata=metadata,
        )

    def release_reservation(self, ledger_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Release reserved slot without consuming capacity (capacity returned)."""
        return self.dal.transition_ledger_status(
            ledger_id=ledger_id,
            target_status=LedgerStatus.RELEASED,
            metadata=metadata,
        )
