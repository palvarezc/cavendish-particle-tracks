import os


def get_shuffling_seed(fallback: int = 1) -> int:
    """Get the shuffling seed from the environment variable.

    This is useful, for example, for each lab computer being seeded differently.
    """
    if not os.getenv("CPT_SHUFFLING_SEED"):
        return fallback
    try:
        return int(os.environ["CPT_SHUFFLING_SEED"])
    except ValueError:
        print(
            f"Warning: Invalid value for CPT_SHUFFLING_SEED. Using seed value of {fallback}."
        )
        return fallback
