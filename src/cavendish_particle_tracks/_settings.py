from __future__ import annotations

import os


def _bool_cast(value: str) -> bool:
    return value.lower() in ("true", "yes", "1")


def _int_cast(value: str) -> int:
    return int(value)


def _get_environment_variable(name: str, fallback: int | bool) -> int | bool:
    """Get an environment variable or return a fallback value."""
    if not os.getenv(name):
        return fallback
    cast_function = _int_cast if type(fallback) is int else _bool_cast
    try:
        return cast_function(os.environ[name])
    except ValueError:
        print(f"Warning: Invalid value for {name}. Using fallback value of {fallback}.")
        return fallback


def get_shuffling_seed(fallback: int = 1) -> int:
    """Get the shuffling seed from the environment variable.

    This is useful, for example, for each lab computer being seeded differently.
    """
    return _get_environment_variable("CPT_SHUFFLING_SEED", fallback)


def get_bypass() -> bool:
    """Get the admin bypass setting from the environment variable.

    This overrides the workflow dis/enabling of buttons for testing and for development.
    It should not be set for users.
    """
    return _get_environment_variable("CPT_DEV_BYPASS", fallback=False)  # type: ignore
