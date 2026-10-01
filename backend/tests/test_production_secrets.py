"""Regression tests for the production secret guard in config.py.

With DEBUG=false, the app must refuse to construct Settings while either
SECRET_KEY or CREDENTIAL_MASTER_KEY is still the value published in this file.
Both defaults are readable by anyone with the source (or its git history):

  - SECRET_KEY signs the JWTs decode_access_token accepts, so knowing it plus any
    user id is enough to mint a token the API treats as that user.
  - CREDENTIAL_MASTER_KEY unwraps every user's data key, and therefore every
    connected provider token stored under it.

Failing startup is the intended behaviour — the alternative is silently running a
production deployment on a key that's in the repository.
"""
import pytest
from pydantic import ValidationError

from app.config import _DEFAULT_CREDENTIAL_MASTER_KEY, _DEFAULT_SECRET_KEY, Settings


def _settings(**overrides):
    base = {
        "debug": False,
        "secret_key": "a-real-deployment-secret-key",
        "credential_master_key": "a-real-fernet-key",
    }
    base.update(overrides)
    return base


class TestProductionRefusesDefaultSecrets:
    def test_default_secret_key_blocks_startup(self):
        with pytest.raises(ValidationError, match="SECRET_KEY"):
            Settings(**_settings(secret_key=_DEFAULT_SECRET_KEY))

    def test_default_credential_master_key_blocks_startup(self):
        with pytest.raises(ValidationError, match="CREDENTIAL_MASTER_KEY"):
            Settings(**_settings(credential_master_key=_DEFAULT_CREDENTIAL_MASTER_KEY))

    def test_both_defaults_reported_together(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                **{
                    "debug": False,
                    "secret_key": _DEFAULT_SECRET_KEY,
                    "credential_master_key": _DEFAULT_CREDENTIAL_MASTER_KEY,
                }
            )
        message = str(exc_info.value)
        assert "SECRET_KEY" in message
        assert "CREDENTIAL_MASTER_KEY" in message

    def test_production_starts_when_both_are_supplied(self):
        settings = Settings(**_settings())
        assert settings.secret_key != _DEFAULT_SECRET_KEY
        assert settings.credential_master_key != _DEFAULT_CREDENTIAL_MASTER_KEY


class TestDevelopmentStillRunsOutOfTheBox:
    def test_debug_allows_the_published_defaults(self):
        settings = Settings(
            debug=True,
            secret_key=_DEFAULT_SECRET_KEY,
            credential_master_key=_DEFAULT_CREDENTIAL_MASTER_KEY,
        )
        assert settings.secret_key == _DEFAULT_SECRET_KEY
        assert settings.credential_master_key == _DEFAULT_CREDENTIAL_MASTER_KEY