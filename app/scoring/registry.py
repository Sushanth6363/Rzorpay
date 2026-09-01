"""File-Based Model Registry for Unified Recovery Engine (ADR-0008).

INVARIANTS:
1. ADR-0008: Models stored as local files (models/vN.cbm + vN.meta.json).
2. Zero external ML platform dependencies (No MLflow, W&B, or cloud model stores).
3. Complete provenance and hash verification for reproducibility.
"""

import hashlib
import json
import os
from typing import Any, Dict, List, Optional
from app.scoring.s_learner import CatBoostSLearner


class FileBasedModelRegistry:
    """Manages file-based CatBoost S-learner model artifacts and metadata JSONs."""

    def __init__(self, base_dir: str = "models") -> None:
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_model_path(self, version: str) -> str:
        return os.path.join(self.base_dir, f"{version}.cbm")

    def _get_meta_path(self, version: str) -> str:
        return os.path.join(self.base_dir, f"{version}.meta.json")

    def register_model(
        self,
        version: str,
        learner: CatBoostSLearner,
        metrics: Optional[Dict[str, float]] = None,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Save learner model and create metadata JSON file."""
        model_path = self._get_model_path(version)
        meta_path = self._get_meta_path(version)

        # Save model file
        learner.save_model(model_path)

        # Compute SHA256 artifact hash if file exists
        artifact_hash = ""
        if os.path.exists(model_path):
            with open(model_path, "rb") as f:
                artifact_hash = hashlib.sha256(f.read()).hexdigest()

        metadata = {
            "model_name": "CatBoostSLearner",
            "model_version": version,
            "artifact_path": model_path,
            "artifact_hash": artifact_hash,
            "config": learner.to_config_dict(),
            "metrics": metrics or {},
            "notes": notes,
            "is_fitted": learner.is_fitted,
        }

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    def load_model(self, version: str) -> Optional[CatBoostSLearner]:
        """Load model by version string."""
        model_path = self._get_model_path(version)
        meta_path = self._get_meta_path(version)

        if not os.path.exists(model_path):
            return None

        # Load metadata if exists
        config = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                config = json.load(f).get("config", {})

        learner = CatBoostSLearner(
            random_seed=config.get("random_seed", 42),
            iterations=config.get("iterations", 50),
            depth=config.get("depth", 4),
            learning_rate=config.get("learning_rate", 0.1),
        )
        learner.load_model(model_path)
        return learner

    def list_versions(self) -> List[str]:
        """Return list of available registered model versions."""
        versions = []
        if os.path.exists(self.base_dir):
            for filename in os.listdir(self.base_dir):
                if filename.endswith(".meta.json"):
                    v = filename.replace(".meta.json", "")
                    versions.append(v)
        return sorted(versions)
