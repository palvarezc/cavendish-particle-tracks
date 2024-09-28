from __future__ import annotations

import numpy as np
import pytest

from cavendish_particle_tracks._main_widget import ParticleTracksWidget


@pytest.mark.parametrize(
    "three_points, rad",
    [
        ([[0, 1], [1, 0], [0, -1]], 1),
        ([[-6, 3], [-3, 2], [0, 3]], 5),
        ([[1, 1], [2, 2], [3, 4]], 5.7),
    ],
)
def test_calculate_radius_ui(
    cpt_widget: ParticleTracksWidget,
    capsys: pytest.CaptureFixture[str],
    three_points,
    rad,
):
    """Test the expected behavior from the expected workflow:

    - Add a particle.
    - Add and select three points.
    - Calculate a radius from this.
    - The table should have the correct radius.
    """
    # need to click "new particle" to add a row to the table
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    layer_measurements = cpt_widget._setup_measurement_layer()

    # add three points (view, event, y, x) to the points layer and select them
    layer_measurements.add([[0, 0] + point for point in three_points])
    layer_measurements.selected_data = {0, 1, 2}

    # click the calculate radius button
    cpt_widget._on_click_radius()

    # read captured output and check that it's as we expected
    captured = capsys.readouterr()
    expected_lines = ["Adding points to the table:", "calculating radius!"]
    for expected in expected_lines:
        assert expected in captured.out

    assert cpt_widget.table.item(0, 2)
    assert cpt_widget.table.item(0, 3)
    assert cpt_widget.table.item(0, 4)
    assert cpt_widget.table.item(0, 5)

    assert cpt_widget.data[0].radius_px == pytest.approx(rad, rel=1e-3)


@pytest.mark.parametrize("npoints", [1, 2, 4, 5])
def test_calculate_radius_fails_with_wrong_number_of_points(
    cpt_widget: ParticleTracksWidget,
    capsys: pytest.CaptureFixture[str],
    npoints,
):
    """Test the obvious failure modes: if I don't select 3 points, I can't
    calculate a radius so better send a nice message."""
    # need to click "new particle" to add a row to the table
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    layer_measurements = cpt_widget._setup_measurement_layer()

    # add wrong number of points (view, event, y, x) to the points layer and select them
    points = np.random.random((npoints, 2))
    layer_measurements.add([np.append([0, 0], point) for point in points])
    layer_measurements.selected_data = set(range(npoints))

    # click the calculate radius button
    cpt_widget._on_click_radius()
    captured = capsys.readouterr()

    assert (
        "ERROR: Select three points to calculate the path radius."
        in captured.out
    )


@pytest.mark.parametrize(
    "three_points, rad",
    [
        ([[0, 1], [1, 0], [0, -1]], 1),
        ([[-6, 3], [-3, 2], [0, 3]], 5),
        ([[1, 1], [2, 2], [3, 4]], 5.7),
    ],
)
def test_calculate_radius_fails_data_out_of_sync(
    cpt_widget: ParticleTracksWidget,
    capsys: pytest.CaptureFixture[str],
    three_points,
    rad,
):
    """Test that the radius cannot be computed if the data is out of sync."""
    # Add images to the viewer
    images = np.random.randint(0, 10, (10, 10, 3, 5), "uint8")
    cpt_widget.viewer.add_image(images, name="Particle Tracks")
    cpt_widget.viewer.dims.set_current_step(2, 0)  # move to view 0
    cpt_widget.viewer.dims.set_current_step(3, 0)  # move to event 0

    # Add new particle
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    # add three points (view, event, y, x) to the points layer and select them
    layer_measurements = cpt_widget._setup_measurement_layer()
    layer_measurements.add([[0, 0] + point for point in three_points])
    layer_measurements.selected_data = {0, 1, 2}

    # change the data so that it's out of sync
    cpt_widget.viewer.dims.set_current_step(3, 1)  # move to event 1

    # click the calculate radius button
    cpt_widget._on_click_radius()

    # # read captured output and check that it's as we expected
    # captured = capsys.readouterr()
    # expected_lines = ["Measurement out of current slice"]
    # for expected in expected_lines:
    #     assert expected in captured.out

    assert (
        cpt_widget.data[0].radius_px < 0
    ), "The radius should not be calculated"

    assert not cpt_widget.table.item(
        0, 2
    ), "The radius points should not be recorded"
    assert not cpt_widget.table.item(
        0, 3
    ), "The radius points should not be recorded"
    assert not cpt_widget.table.item(
        0, 4
    ), "The radius points should not be recorded"
    assert not cpt_widget.table.item(0, 5), "The radius should not be recorded"


def test_calculate_length_ui(
    cpt_widget: ParticleTracksWidget, capsys: pytest.CaptureFixture[str]
):

    # need to click "new particle" to add a row to the table
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    # create measurements layer
    layer_measurements = cpt_widget._setup_measurement_layer()

    # add two points (view, event, y, x) to the points layer and select them
    layer_measurements.add([(0, 0, 0, 1), (0, 0, 0, 0)])
    layer_measurements.selected_data = {0, 1}

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
    cpt_widget: ParticleTracksWidget,
    capsys: pytest.CaptureFixture[str],
    npoints,
):
    """Test the obvious failure modes: if I don't select 2 points, I can't
    calculate a length so better send a nice message."""
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    layer_measurements = cpt_widget._setup_measurement_layer()

    # add wrong number of points (view, event, y, x) to the points layer and select them
    points = np.random.random((npoints, 2))
    layer_measurements.add([np.append([0, 0], point) for point in points])
    layer_measurements.selected_data = set(range(npoints))

    # click the calculate decay length button
    cpt_widget._on_click_length()
    captured = capsys.readouterr()

    assert (
        "ERROR: Select two points to calculate the decay length."
        in captured.out
    )
