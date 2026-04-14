"""Router cache keys include per-provider fingerprints."""

from unittest.mock import MagicMock

from doctranslate.translator.config import NestedTranslatorConfig
from doctranslate.translator.config import ProviderConfigModel
from doctranslate.translator.config import RouteProfileConfig
from doctranslate.translator.router import TranslatorRouter
from doctranslate.translator.types import RouterStrategy
from doctranslate.translator.types import TranslatorCapabilities


def test_router_adds_provider_cache_params():
    pcfg = ProviderConfigModel(
        provider="ollama",
        model="m1",
        base_url="http://127.0.0.1:11434",
    )
    nested = NestedTranslatorConfig()
    profile = RouteProfileConfig(providers=["p1"], strategy=RouterStrategy.FAILOVER)
    caps = {
        "p1": TranslatorCapabilities(
            supports_llm=True,
            supports_json_mode=True,
            provider_id="p1",
        ),
    }
    ex = MagicMock()
    r = TranslatorRouter(
        lang_in="en",
        lang_out="zh",
        ignore_cache=True,
        profile_name="translate",
        route_profile=profile,
        global_strategy=RouterStrategy.FAILOVER,
        executors={"p1": ex},
        capabilities_by_id=caps,
        provider_configs={"p1": pcfg},
        nested_settings=nested,
    )
    assert "provider.p1" in r.cache.params
    fp = r.cache.params["provider.p1"]
    assert fp["model"] == "m1"
    assert fp["provider"] == "ollama"
