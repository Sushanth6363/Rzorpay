"""Data Access Layer (DAL) & Tenant Isolation Boundary for Unified Recovery Engine.

INVARIANTS:
1. Every query is parameterized to prevent SQL injection.
2. Every tenant-scoped query explicitly requires merchant_id. Unscoped queries raise TenantScopeViolation.
3. Contact budget reservation uses atomic SQL UPDATE enforcing reserved_count + consumed_count <= cap.
"""

import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional
from app.clock import Clock, SystemClock
from app.domain.enums import EventType, OpportunityStatus, EventSource
from app.domain.models import RecoveryOpportunity, CustomerContactBudget, EventLog
from app.domain.money import Money


class TenantScopeViolation(Exception):
    """Raised when an operation attempts unscoped or cross-tenant database access."""
    pass


class TenantScopedDB:
    """Tenant-scoped Data Access Layer enforcing strict isolation and atomic invariants."""

    def __init__(self, conn: sqlite3.Connection, merchant_id: str, clock: Optional[Clock] = None) -> None:
        if not merchant_id or not isinstance(merchant_id, str) or not merchant_id.strip():
            raise TenantScopeViolation("Merchant ID cannot be empty or null.")
        self.conn = conn
        self.merchant_id: str = merchant_id.strip()
        self.clock: Clock = clock or SystemClock()

    def _verify_tenant_match(self, target_merchant_id: str) -> None:
        """Verify that target merchant_id matches active tenant scope."""
        if target_merchant_id != self.merchant_id:
            raise TenantScopeViolation(
                f"Cross-tenant access prohibited! Active tenant: '{self.merchant_id}', requested: '{target_merchant_id}'"
            )

    # ------------------------------------------------------------------
    # 1. Recovery Opportunity Operations
    # ------------------------------------------------------------------

    def create_opportunity(self, opportunity: RecoveryOpportunity) -> None:
        """Persist a new RecoveryOpportunity within tenant scope."""
        self._verify_tenant_match(opportunity.merchant_id)
        
        sql = """
        INSERT INTO opportunities (
            opportunity_id, merchant_id, customer_id, source_event_id,
            event_type, amount_paise, currency, status, source,
            occurred_at, observed_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            opportunity.opportunity_id,
            opportunity.merchant_id,
            opportunity.customer_id,
            opportunity.source_event_id,
            opportunity.event_type.value,
            opportunity.amount.amount_paise,
            opportunity.currency,
            opportunity.status.value,
            opportunity.source.value,
            opportunity.occurred_at,
            opportunity.observed_at,
            opportunity.created_at,
            opportunity.updated_at,
        )
        self.conn.execute(sql, params)
        self.conn.commit()

    def get_opportunity(self, opportunity_id: str) -> Optional[RecoveryOpportunity]:
        """Retrieve RecoveryOpportunity by ID within active tenant scope."""
        sql = """
        SELECT opportunity_id, merchant_id, customer_id, source_event_id,
               event_type, amount_paise, currency, status, source,
               occurred_at, observed_at, created_at, updated_at
        FROM opportunities
        WHERE merchant_id = ? AND opportunity_id = ?;
        """
        cursor = self.conn.execute(sql, (self.merchant_id, opportunity_id))
        row = cursor.fetchone()
        if not row:
            return None

        return RecoveryOpportunity(
            opportunity_id=row["opportunity_id"],
            merchant_id=row["merchant_id"],
            customer_id=row["customer_id"],
            source_event_id=row["source_event_id"],
            event_type=EventType(row["event_type"]),
            amount=Money(row["amount_paise"]),
            currency=row["currency"],
            status=OpportunityStatus(row["status"]),
            source=EventSource(row["source"]),
            occurred_at=row["occurred_at"],
            observed_at=row["observed_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # ------------------------------------------------------------------
    # 2. Ingestion & Event Deduplication (Idempotency)
    # ------------------------------------------------------------------

    def save_event_if_new(self, event: EventLog) -> bool:
        """Save ingested event if not previously received.

        Returns True if newly inserted, False if duplicate idempotency key for tenant.
        """
        self._verify_tenant_match(event.merchant_id)
        
        sql = """
        INSERT OR IGNORE INTO events (
            event_id, merchant_id, source_event_id, event_type,
            source, payload_json, idempotency_key, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            event.event_id,
            event.merchant_id,
            event.source_event_id,
            event.event_type.value,
            event.source.value,
            event.payload_json,
            event.idempotency_key,
            event.created_at,
        )
        cursor = self.conn.execute(sql, params)
        self.conn.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # 3. Contact Budget & Atomic Reservation Primitive
    # ------------------------------------------------------------------

    def init_contact_budget(self, customer_id: str, cap: int = 3, max_retries: int = 5) -> CustomerContactBudget:
        """Initialize or retrieve customer contact budget with retry on transient lock contention."""
        now_iso = self.clock.now_iso()
        sql = """
        INSERT INTO contact_budgets (merchant_id, customer_id, cap, reserved_count, consumed_count, updated_at)
        VALUES (?, ?, ?, 0, 0, ?)
        ON CONFLICT(merchant_id, customer_id) DO UPDATE SET updated_at = excluded.updated_at;

        """
        for attempt in range(max_retries):
            try:
                self.conn.execute(sql, (self.merchant_id, customer_id, cap, now_iso))
                self.conn.commit()
                break
            except sqlite3.OperationalError as err:
                if "locked" in str(err).lower() or "busy" in str(err).lower():
                    if attempt == max_retries - 1:
                        raise
                    import time
                    time.sleep(0.01 * (2 ** attempt))
                else:
                    raise
        return self.get_contact_budget(customer_id)  # type: ignore

    def get_contact_budget(self, customer_id: str) -> Optional[CustomerContactBudget]:
        """Retrieve CustomerContactBudget within active tenant scope."""
        sql = """
        SELECT merchant_id, customer_id, cap, reserved_count, consumed_count, updated_at
        FROM contact_budgets
        WHERE merchant_id = ? AND customer_id = ?;
        """
        cursor = self.conn.execute(sql, (self.merchant_id, customer_id))
        row = cursor.fetchone()
        if not row:
            return None

        return CustomerContactBudget(
            merchant_id=row["merchant_id"],
            customer_id=row["customer_id"],
            cap=row["cap"],
            reserved_count=row["reserved_count"],
            consumed_count=row["consumed_count"],
            updated_at=row["updated_at"],
        )

    def reserve_contact_slot(self, customer_id: str, max_retries: int = 5) -> bool:
        """Atomically reserve a contact slot under the monthly cap.

        ATOMIC INVARIANT (ADR-0003):
        Check reserved_count + consumed_count < cap in conditional UPDATE.
        Returns True if reservation granted, False if cap exhausted.
        Handles transient SQLite lock contention with explicit bounded retries.
        """
        now_iso = self.clock.now_iso()
        
        # Ensure budget record exists
        self.init_contact_budget(customer_id)

        sql = """
        UPDATE contact_budgets
        SET reserved_count = reserved_count + 1, updated_at = ?
        WHERE merchant_id = ? AND customer_id = ? AND (reserved_count + consumed_count < cap);
        """
        for attempt in range(max_retries):
            try:
                cursor = self.conn.execute(sql, (now_iso, self.merchant_id, customer_id))
                self.conn.commit()
                return cursor.rowcount > 0
            except sqlite3.OperationalError as err:
                if "locked" in str(err).lower() or "busy" in str(err).lower():
                    if attempt == max_retries - 1:
                        raise
                    import time
                    time.sleep(0.01 * (2 ** attempt))
                else:
                    raise
        return False


    def mark_reservation_executed(self, customer_id: str) -> bool:
        """Transition 1 reserved slot to consumed status."""
        now_iso = self.clock.now_iso()
        sql = """
        UPDATE contact_budgets
        SET reserved_count = reserved_count - 1, consumed_count = consumed_count + 1, updated_at = ?
        WHERE merchant_id = ? AND customer_id = ? AND reserved_count > 0;
        """
        cursor = self.conn.execute(sql, (now_iso, self.merchant_id, customer_id))
        self.conn.commit()
        return cursor.rowcount > 0

    def release_reservation(self, customer_id: str) -> bool:
        """Release 1 reserved slot without consuming budget."""
        now_iso = self.clock.now_iso()
        sql = """
        UPDATE contact_budgets
        SET reserved_count = reserved_count - 1, updated_at = ?
        WHERE merchant_id = ? AND customer_id = ? AND reserved_count > 0;
        """
        cursor = self.conn.execute(sql, (now_iso, self.merchant_id, customer_id))
        self.conn.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # 4. Audit Logging
    # ------------------------------------------------------------------

    def log_audit(self, entity_type: str, entity_id: str, action: str, details: Dict[str, Any]) -> None:
        """Log audit event within tenant scope."""
        log_id = str(uuid.uuid4())
        now_iso = self.clock.now_iso()
        sql = """
        INSERT INTO audit_logs (log_id, merchant_id, entity_type, entity_id, action, details_json, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            log_id,
            self.merchant_id,
            entity_type,
            entity_id,
            action,
            json.dumps(details),
            now_iso,
        )
        self.conn.execute(sql, params)
        self.conn.commit()
