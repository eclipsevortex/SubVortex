from subvortex.core.core_bittensor.subtensor.subtensor_settings import Settings


def test_create_with_env_vars(monkeypatch):
    monkeypatch.setenv("SUBVORTEX_NETWORK", "custom-network")
    monkeypatch.setenv("SUBVORTEX_CHAIN_ENDPOINT", "custom-chain-endpoint")

    settings = Settings.create()

    assert settings.network == "custom-network"
    assert settings.chain_endpoint == "custom-chain-endpoint"


def test_create_with_default_values(monkeypatch):
    monkeypatch.delenv("SUBVORTEX_NETWORK", raising=False)
    monkeypatch.delenv("SUBVORTEX_CHAIN_ENDPOINT", raising=False)

    settings = Settings.create()

    assert settings.network == "finney"
    assert settings.chain_endpoint is None


def test_partial_env_override(monkeypatch):
    monkeypatch.setenv("SUBVORTEX_NETWORK", "custom-network")
    monkeypatch.delenv("SUBVORTEX_CHAIN_ENDPOINT", raising=False)

    settings = Settings.create()

    assert settings.network == "custom-network"
    assert settings.chain_endpoint is None
