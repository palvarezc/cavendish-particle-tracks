from random import random

import numpy as np
import pytest


def test_calculate_radius_ui(cpt_widget, capsys):
    """Test the expected behavior from the expected workflow:

    - Add a particle.
    - Add and select three points.
    - Calculate a radius from this.
    - The table should have the correct radius.
    """
    # need to click "new particle" to add a row to the table
    cpt_widget.cb.setCurrentIndex(1)
    cpt_widget._on_click_new_particle()

    # add three points to the points layer and select them
    cpt_widget.viewer.add_points([(0, 1), (1, 0), (0, -1)])
    for layer in cpt_widget.viewer.layers:
        if layer.name == "Points":
            layer.selected_data = {0, 1, 2}

    # click the calculate radius button
    cpt_widget._on_click_radius()

    # read captured output and check that it's as we expected
    captured = capsys.readouterr()
    expected_lines = ["Adding points to the table:", "calculating radius!"]
    for expected in expected_lines:
        assert expected in captured.out

    assert cpt_widget.table.item(0, 1)
    assert cpt_widget.table.item(0, 2)
    assert cpt_widget.table.item(0, 3)
    assert cpt_widget.table.item(0, 4)

    assert cpt_widget.data[0].radius_px == 1.0


@pytest.mark.parametrize("npoints", [1, 2, 4, 5])
def test_calculate_radius_fails_with_wrong_number_of_points(
    cpt_widget, capsys, npoints
):
    """Test the obvious failure modes: if I don't select 3 points, I can't
    calculate a radius so better send a nice message."""
    # need to click "new particle" to add a row to the table
    cpt_widget.cb.setCurrentIndex(1)
    cpt_widget._on_click_new_particle()

    # add six random points to the points layer
    points = [(random(), random()) for _ in range(6)]
    cpt_widget.viewer.add_points(points)

    # select the wrong number of points
    for layer in cpt_widget.viewer.layers:
        if layer.name == "Points":
            layer.selected_data = set(range(npoints))

    # click the calculate radius button
    cpt_widget._on_click_radius()
    captured = capsys.readouterr()

    assert (
        "ERROR: Select three points to calculate the path radius."
        in captured.out
    )


def test_add_new_particle_ui(cpt_widget, capsys):
    assert cpt_widget.table.rowCount() == 0

    cpt_widget.cb.setCurrentIndex(1)
    cpt_widget._on_click_new_particle()

    assert cpt_widget.table.rowCount() == 1
    assert len(cpt_widget.data) == 1


def test_delete_particle_ui(cpt_widget, capsys):
    """Tests the removal of a particle from the table"""
    cpt_widget.cb.setCurrentIndex(1)
    cpt_widget._on_click_new_particle()

    assert cpt_widget.table.rowCount() == 1
    assert len(cpt_widget.data) == 1

    cpt_widget._on_click_delete_particle()

    assert cpt_widget.table.rowCount() == 0
    assert len(cpt_widget.data) == 0


def test_calculate_length_ui(cpt_widget, capsys):
    # add a random image to the napari viewer
    cpt_widget.viewer.add_image(np.random.random((100, 100)))

    # need to click "new particle" to add a row to the table
    cpt_widget.cb.setCurrentIndex(1)
    cpt_widget._on_click_new_particle()

    # add three points to the points layer and select them
    cpt_widget.viewer.add_points([(0, 1), (0, 0)])
    for layer in cpt_widget.viewer.layers:
        if layer.name == "Points":
            layer.selected_data = {0, 1}

    # click the calculate decay length button
    cpt_widget._on_click_length()

    assert cpt_widget.table.item(
        0, cpt_widget._get_table_column_index("decay_length_px")
    )
    assert (
        cpt_widget.table.item(
            0, cpt_widget._get_table_column_index("decay_length_px")
        ).text()
        == "1.0"
    )


@pytest.mark.parametrize("npoints", [1, 3, 4, 5])
def test_calculate_length_fails_with_wrong_number_of_points(
    cpt_widget, capsys, npoints
):
    """Test the obvious failure modes: if I don't select 2 points, I can't
    calculate a length so better send a nice message."""
    # need to click "new particle" to add a row to the table
    cpt_widget.cb.setCurrentIndex(1)
    cpt_widget._on_click_new_particle()

    # add six random points to the points layer
    points = [(random(), random()) for _ in range(6)]
    cpt_widget.viewer.add_points(points)

    # select the wrong number of points
    for layer in cpt_widget.viewer.layers:
        if layer.name == "Points":
            layer.selected_data = set(range(npoints))

    # click the calculate decay length button
    cpt_widget._on_click_length()
    captured = capsys.readouterr()

    assert (
        "ERROR: Select two points to calculate the decay length."
        in captured.out
    )
