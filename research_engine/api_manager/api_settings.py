"""
API Settings

Implements APISettings, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 5.4. Owns
the tunable behavior that controls how APIManager operates -- timeout,
retry count, cool-down durations, and the env var name mapping used to
resolve each provider's key -- distinct from APIProvider's identity
and APIRegistry's Category -> Provider mapping.

Configuration Loading from .env: load_env_file() reads a plain
KEY=VALUE .env file into os.environ (standard library only -- no
external dependency), and from_env() builds an APISettings from
whatever is already in the environment. Per the "one .env file only"
rule (Section 2, Section 12), this module never reads more than one
file, and it never reads or stores an actual key value on the
APISettings object itself -- only the env var *names* live there;
resolve_key() is the one place a real key value is read, and only at
the moment it is needed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional

from .api_provider import ProviderName

DEFAULT_KEY_ENV_VARS: Dict[ProviderName, str] = {
    ProviderName.FMP: "FMP_API_KEY",
    ProviderName.FINNHUB: "FINNHUB_API_KEY",
    ProviderName.ALPHA_VANTAGE: "ALPHA_VANTAGE_API_KEY",
    ProviderName.TWELVE_DATA: "TWELVE_DATA_API_KEY",
    ProviderName.NEWSAPI: "NEWSAPI_API_KEY",
}

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_RETRY_COUNT = 1
DEFAULT_COOL_DOWN_SECONDS = 60.0
DEFAULT_INVALID_KEY_COOL_DOWN_SECONDS = 3600.0


def load_env_file(path: str = ".env", override: bool = False) -> Dict[str, str]:
    """Load a plain KEY=VALUE .env file into os.environ.

    A missing file is not an error -- returns an empty dict, since a
    developer machine or CI runner without a `.env` present is a normal
    condition, not a failure. Existing environment variables are never
    overwritten unless `override` is True, matching the usual .env
    convention of the real environment taking priority over the file.
    """
    loaded: Dict[str, str] = {}
    if not os.path.exists(path):
        return loaded

    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if not key:
                continue
            loaded[key] = value
            if override or key not in os.environ:
                os.environ[key] = value

    return loaded


@dataclass
class APISettings:
    """Tunable behavior for APIManager, per Section 5.4. Never holds a
    resolved key value -- only the env var names to look one up by."""

    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    retry_count: int = DEFAULT_RETRY_COUNT
    cool_down_seconds: float = DEFAULT_COOL_DOWN_SECONDS
    invalid_key_cool_down_seconds: float = DEFAULT_INVALID_KEY_COOL_DOWN_SECONDS
    restart_required_for_registry_changes: bool = False
    provider_key_env_vars: Dict[ProviderName, str] = field(
        default_factory=lambda: dict(DEFAULT_KEY_ENV_VARS)
    )

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "APISettings":
        """Build APISettings from the current environment (or an
        injected mapping, for tests). Only the tuning values are read
        from named API_MANAGER_* variables here -- provider key values
        themselves are read later, on demand, by resolve_key()."""
        environment = env if env is not None else os.environ
        return cls(
            timeout_seconds=float(
                environment.get("API_MANAGER_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
            ),
            retry_count=int(environment.get("API_MANAGER_RETRY_COUNT", DEFAULT_RETRY_COUNT)),
            cool_down_seconds=float(
                environment.get("API_MANAGER_COOL_DOWN_SECONDS", DEFAULT_COOL_DOWN_SECONDS)
            ),
            invalid_key_cool_down_seconds=float(
                environment.get(
                    "API_MANAGER_INVALID_KEY_COOL_DOWN_SECONDS",
                    DEFAULT_INVALID_KEY_COOL_DOWN_SECONDS,
                )
            ),
            restart_required_for_registry_changes=str(
                environment.get("API_MANAGER_RESTART_REQUIRED_FOR_REGISTRY_CHANGES", "false")
            )
            .strip()
            .lower()
            in ("1", "true", "yes"),
        )

    def resolve_key(
        self, provider_name: ProviderName, env: Optional[Mapping[str, str]] = None
    ) -> Optional[str]:
        """Read the actual key value for `provider_name` from the
        environment, using this APISettings' configured env var name.
        Returns None if no var name is configured or the variable is
        unset/blank -- never raises, since a missing key is a normal,
        expected condition in this placeholder-only phase, not an
        error."""
        environment = env if env is not None else os.environ
        var_name = self.provider_key_env_vars.get(provider_name)
        if not var_name:
            return None
        value = environment.get(var_name)
        return value if value else None
