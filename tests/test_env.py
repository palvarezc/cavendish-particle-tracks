import os

import pytest


@pytest.fixture
def mocked_shuffle_seed_env(mocker):
    mocker.patch.dict(os.environ, {"CPT_SHUFFLING_SEED": "12345"})
    yield


@pytest.mark.usefixtures("mocked_shuffle_seed_env")
def test_shuffle_seed(cpt_widget):
    assert cpt_widget.shuffling_seed == 12345, "Setting shuffling seed from env failed"


@pytest.fixture(params=["Rutherford", "True", "False", ""])
def mocked_invalid_shuffle_seed_env(mocker, request):
    mocker.patch.dict(os.environ, {"CPT_SHUFFLING_SEED": request.param})
    yield


@pytest.mark.usefixtures("mocked_invalid_shuffle_seed_env")
def test_invalid_shuffle_seed(cpt_widget):
    assert (
        cpt_widget.shuffling_seed == 1
    ), "Setting seed from invalid env should default to 1"


def test_sanity_teardown_env_patching(cpt_widget):
    assert (
        "CPT_SHUFFLING_SEED" not in os.environ
    ), "CPT_SHUFFLING_SEED should not be set after fixture teardown"
    assert cpt_widget.shuffling_seed == 1, "No env variable should default to 1"
