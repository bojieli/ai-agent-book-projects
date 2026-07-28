"""advise() must not TypeError-unpack when the model has zero archetypes."""
import sys
import types

import pytest

# Stub openai/config client so LegalAdvisorAgent can be constructed offline.
import config as cfg

cfg.get_client = lambda: object()

from advisor_agent import LegalAdvisorAgent  # noqa: E402
from archetypes import fit, nearest_archetype  # noqa: E402


def _small_model():
    schema = {"core_factors": [], "extensions": {"盗窃罪": [], "诈骗罪": []}}
    results = [
        {"extracted": {"charge": "盗窃罪"}, "label_months": 12},
        {"extracted": {"charge": "诈骗罪"}, "label_months": 24},
    ]
    return schema, fit(schema, results, save=False, verbose=False)


def test_nearest_returns_none_when_no_archetypes():
    _, model = _small_model()
    assert model["n_archetypes"] == 0
    assert nearest_archetype(model, {"charge": "盗窃罪"}) is None


def test_advise_raises_clear_valueerror_not_typeerror():
    schema, model = _small_model()
    agent = LegalAdvisorAgent(schema, model)
    with pytest.raises(ValueError, match="没有可用案件原型"):
        agent.advise({"charge": "盗窃罪"})
