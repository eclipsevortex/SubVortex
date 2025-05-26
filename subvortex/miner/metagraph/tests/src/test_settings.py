import pytest

from subvortex.core.metagraph.settings import Settings as BaseSettings
from subvortex.miner.metagraph.src.settings import Settings


def test_create_with_env_vars(monkeypatch):
    monkeypatch.setenv("SUBVORTEX_DATABASE_HOST", "redis.internal")
    monkeypatch.setenv("SUBVORTEX_DATABASE_PORT", "6380")
    monkeypatch.setenv("SUBVORTEX_DATABASE_INDEX", "2")
    monkeypatch.setenv("SUBVORTEX_DATABASE_PASSWORD", "securepass")

    settings = Settings.create()

    assert settings.database_host == "redis.internal"
    assert settings.database_port == 6380
    assert settings.database_index == 2
    assert settings.database_password == "securepass"


def test_create_with_default_values(monkeypatch):
    monkeypatch.delenv("SUBVORTEX_DATABASE_HOST", raising=False)
    monkeypatch.delenv("SUBVORTEX_DATABASE_PORT", raising=False)
    monkeypatch.delenv("SUBVORTEX_DATABASE_INDEX", raising=False)
    monkeypatch.delenv("SUBVORTEX_DATABASE_PASSWORD", raising=False)

    settings = Settings.create()

    assert settings.database_host == "localhost"
    assert settings.database_port == 6379
    assert settings.database_index == 0
    assert settings.database_password is None


def test_partial_env_override(monkeypatch):
    monkeypatch.setenv("SUBVORTEX_DATABASE_HOST", "127.0.0.1")
    monkeypatch.delenv("SUBVORTEX_DATABASE_PORT", raising=False)
    monkeypatch.delenv("SUBVORTEX_DATABASE_INDEX", raising=False)
    monkeypatch.delenv("SUBVORTEX_DATABASE_PASSWORD", raising=False)

    settings = Settings.create()

    assert settings.database_host == "127.0.0.1"
    assert settings.database_port == 6379
    assert settings.database_index == 0
    assert settings.database_password is None


def test_invalid_port_casting(monkeypatch):
    monkeypatch.setenv("SUBVORTEX_DATABASE_PORT", "not_an_int")

    with pytest.raises(ValueError):
        Settings.create()


def test_inherits_base_settings():
    settings = Settings.create()
    assert isinstance(settings, BaseSettings)
