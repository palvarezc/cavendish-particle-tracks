import numpy as np
import pytest
from cavendish_particle_tracks import ParticleTracksWidget


def test_calculate_radius_ui(make_napari_viewer, capsys):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100)))

    # create our widget, passing in the viewer
    my_widget = ParticleTracksWidget(viewer)

    # call our widget method
    my_widget._on_click_calculate()

    # read captured output and check that it's as we expected
    captured = capsys.readouterr()
    assert captured.out == "calculating radius!\n"


def test_selected_cells_workflow():
    assert True


@pytest.mark.skip("Not implemented")
def test_add_new_particle_ui(make_napari_viewer, capsys):
    viewer = make_napari_viewer()
    widget = ParticleTracksWidget(viewer)
    assert widget.table.rowCount() == 1

    widget._on_click_new_particle()

    assert widget.table.rowCount() == 2
