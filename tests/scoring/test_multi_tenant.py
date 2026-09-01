"""Tests for Multi-Tenant Isolation & Feature Vector Sanitization (M5-21..23, INV-1)."""

import pytest
from app.db.init import init_db
from app.db.dal import TenantScopedDB, TenantScopeViolation
from app.pipeline.recovery_pipeline import RecoveryPipeline
from app.scoring.engine import AIRecoveryDecisionEngine
from app.scoring.feature_builder import FeatureBuilder


def test_m5_21_merchant_id_excluded_from_model_features():
    """M5-21: Verify merchant_id is strictly excluded from model feature vector to prevent merchant bias (INV-1)."""
    feature_names = FeatureBuilder.get_feature_names()
    assert "merchant_id" not in feature_names
    assert "customer_id" not in feature_names


def test_m5_22_cross_tenant_decision_isolation():
    """M5-22: Verify identical customer_id under different merchants receive independent, merchant-scoped decisions."""
    pipeline = RecoveryPipeline()

    raw_a = {
        "merchant_id": "merch_A",
        "customer_id": "cust_shared",
        "event_id": "evt_A",
        "amount_paise": 100000,
        "occurred_at": "2026-09-01T10:00:00+00:00",
    }
    raw_b = {
        "merchant_id": "merch_B",
        "customer_id": "cust_shared",
        "event_id": "evt_B",
        "amount_paise": 200000,
        "occurred_at": "2026-09-01T10:00:00+00:00",
    }

    ctx_a = pipeline.process_raw_event(raw_a)
    ctx_b = pipeline.process_raw_event(raw_b)

    engine = AIRecoveryDecisionEngine()
    dec_a = engine.evaluate_decision(ctx_a, random_seed=42)
    dec_b = engine.evaluate_decision(ctx_b, random_seed=42)

    assert dec_a.merchant_id == "merch_A"
    assert dec_b.merchant_id == "merch_B"
    assert dec_a.decision_id != dec_b.decision_id
