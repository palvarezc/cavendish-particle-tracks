from random import random

import numpy as np
import pytest
from cavendish_particle_tracks import ParticleTracksWidget


def test_calculate_radius_ui(make_napari_viewer, capsys):
    """Test the expected behavior from the expected workflow:

    - Add a particle.
    - Add and select three points.
    - Calculate a radius from this.
    - The table should have the correct radius.
    """
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100)))
    my_widget = ParticleTracksWidget(viewer)

    # need to click "new particle" to add a row to the table
    my_widget.cb.setCurrentIndex(1)
    my_widget._on_click_new_particle()

    # add three points to the points layer and select them
    viewer.add_points([(0, 1), (1, 0), (0, -1)])
    for layer in viewer.layers:
        if layer.name == "Points":
            layer.selected_data = {0, 1, 2}

    # click the calculate radius button
    my_widget._on_click_radius()

    # read captured output and check that it's as we expected
    captured = capsys.readouterr()
    expected_lines = ["Adding points to the table:", "calculating radius!"]
    for expected in expected_lines:
        assert expected in captured.out

    assert my_widget.table.item(0, 1)
    assert my_widget.table.item(0, 2)
    assert my_widget.table.item(0, 3)
    assert my_widget.table.item(0, 4)

    assert my_widget.data[0].radius == 1.0


@pytest.mark.parametrize("npoints", [1, 2, 4, 5])
def test_calculate_radius_fails_with_wrong_number_of_points(
    make_napari_viewer, capsys, npoints
):
    """Test the obvious failure modes: if I don't select 3 points, I can't
    calculate a radius so better send a nice message."""
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100)))
    widget = ParticleTracksWidget(viewer)

    # need to click "new particle" to add a row to the table
    widget.cb.setCurrentIndex(1)
    widget._on_click_new_particle()

    # add six random points to the points layer
    points = [(random(), random()) for _ in range(6)]
    viewer.add_points(points)

    # select the wrong number of points
    for layer in viewer.layers:
        if layer.name == "Points":
            layer.selected_data = set(range(npoints))

    # click the calculate radius button
    widget._on_click_radius()
    captured = capsys.readouterr()

    assert (
        "Select (only) three points to calculate the decay radius."
        in captured.out
    )
    # TODO: makes more sense to move this to the napari error window. See issue
    # #27. Then this test needs to check for warnings or whatever.


def test_add_new_particle_ui(make_napari_viewer, capsys):
    viewer = make_napari_viewer()
    widget = ParticleTracksWidget(viewer)
    assert widget.table.rowCount() == 0

    widget.cb.setCurrentIndex(1)
    widget._on_click_new_particle()

    assert widget.table.rowCount() == 1
    assert len(widget.data) == 1


def test_calculate_length_ui(make_napari_viewer, capsys):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100)))

    # create our widget, passing in the viewer
    my_widget = ParticleTracksWidget(viewer)

    # need to click "new particle" to add a row to the table
    my_widget.cb.setCurrentIndex(1)
    my_widget._on_click_new_particle()

    # add three points to the points layer and select them
    viewer.add_points([(0, 1), (0, 0)])
    for layer in viewer.layers:
        if layer.name == "Points":
            layer.selected_data = {0, 1}

    # click the calculate radius button
    my_widget._on_click_length()

    assert my_widget.table.item(
        0, my_widget._get_table_column_index("decay_length")
    )
    assert (
        my_widget.table.item(
            0, my_widget._get_table_column_index("decay_length")
        ).text()
        == "1.0"
    )


@pytest.mark.parametrize("npoints", [1, 3, 4, 5])
def test_calculate_length_fails_with_wrong_number_of_points(
    make_napari_viewer, capsys, npoints
):
    """Test the obvious failure modes: if I don't select 2 points, I can't
    calculate a length so better send a nice message."""
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100)))
    widget = ParticleTracksWidget(viewer)

    # need to click "new particle" to add a row to the table
    widget.cb.setCurrentIndex(1)
    widget._on_click_new_particle()

    # add six random points to the points layer
    points = [(random(), random()) for _ in range(6)]
    viewer.add_points(points)

    # select the wrong number of points
    for layer in viewer.layers:
        if layer.name == "Points":
            layer.selected_data = set(range(npoints))

    # click the calculate radius button
    widget._on_click_length()
    captured = capsys.readouterr()

    assert (
        "Select (only) two points to calculate the decay length."
        in captured.out
    )
    # TODO: makes more sense to move this to the napari error window. See issue
    # #27. Then this test needs to check for warnings or whatever.
