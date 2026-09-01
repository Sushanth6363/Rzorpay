"""Unified Recovery Pipeline & Candidate Generator package (M4)."""

from app.pipeline.downtime import DowntimeProvider, SimulatedDowntimeProvider
from app.pipeline.stage0 import Stage0Evaluator, PointInTimeLeakageError
from app.pipeline.stage1 import Stage1Diagnoser
from app.pipeline.candidate_generator import CandidateGenerator
from app.pipeline.safety_filter import HardSafetyFilter
from app.pipeline.recovery_pipeline import RecoveryPipeline
from app.pipeline.dataset_adapter import DatasetAdapter

__all__ = [
    "DowntimeProvider",
    "SimulatedDowntimeProvider",
    "Stage0Evaluator",
    "PointInTimeLeakageError",
    "Stage1Diagnoser",
    "CandidateGenerator",
    "HardSafetyFilter",
    "RecoveryPipeline",
    "DatasetAdapter",
]
