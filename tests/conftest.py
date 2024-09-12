import time
from collections.abc import Callable

import pytest

from cavendish_particle_tracks._widget import ParticleTracksWidget


@pytest.fixture
def cpt_widget(make_napari_viewer):
    """Common test setup fixture: calls the napari helper fixture
    `make_napari_viewer` then creates the ParticleTracksWidget."""
    viewer = make_napari_viewer()
    widget = ParticleTracksWidget(napari_viewer=viewer, test_mode=True)
    return widget
