"""Environment and stack compatibility smoke tests for Unified Recovery Engine.

Verifies that CatBoost, numerical stack libraries, pytest, and Hypothesis are fully
functional and deterministic in the current execution environment.
"""

import catboost
import hypothesis
from hypothesis import given
import hypothesis.strategies as st
import matplotlib
import numpy as np
import pandas as pd
import pytest
import scipy
import sklearn
import streamlit


def test_numerical_stack_imports() -> None:
    """Verify core numerical and ML stack modules import cleanly."""
    assert np.__name__ == "numpy"
    assert pd.__name__ == "pandas"
    assert scipy.__name__ == "scipy"
    assert sklearn.__name__ == "sklearn"
    assert catboost.__name__ == "catboost"
    assert matplotlib.__name__ == "matplotlib"
    assert pytest.__name__ == "pytest"
    assert hypothesis.__name__ == "hypothesis"
    assert streamlit.__name__ == "streamlit"


def test_catboost_fit_deterministic() -> None:
    """Verify CatBoost model instantiation, fitting, and prediction on a deterministic dataset."""
    X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]])
    y = np.array([0, 1, 0, 1])

    model = catboost.CatBoostClassifier(
        iterations=5,
        learning_rate=0.1,
        depth=2,
        random_seed=42,
        verbose=0,
    )
    model.fit(X, y)

    predictions = model.predict(X)
    assert len(predictions) == 4
    assert set(predictions).issubset({0, 1})


@given(st.integers(min_value=-1000, max_value=1000))
def test_hypothesis_property_smoke(val: int) -> None:
    """Verify Hypothesis property-based testing framework is operational."""
    assert val + 0 == val
    assert val - val == 0
