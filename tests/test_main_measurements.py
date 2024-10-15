from __future__ import annotations

import numpy as np
import pytest

from cavendish_particle_tracks._main_widget import (
    IMAGE_LAYER_NAME,
    ParticleTracksWidget,
)


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
    three_points: list[list[int]],
    rad: float,
) -> None:
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

    assert cpt_widget.table.item(0, cpt_widget._get_table_column_index("radius"))
    assert cpt_widget.table.item(0, cpt_widget._get_table_column_index("radius_cm"))
    assert cpt_widget.table.item(0, cpt_widget._get_table_column_index("rpoints"))

    assert cpt_widget.data[0].radius == pytest.approx(rad, rel=1e-3)


@pytest.mark.parametrize("npoints", [1, 2, 4, 5])
def test_calculate_radius_fails_with_wrong_number_of_points(
    cpt_widget: ParticleTracksWidget,
    capsys: pytest.CaptureFixture[str],
    npoints: int,
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

    assert "ERROR: Select three points to calculate the path radius." in captured.out


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
    three_points: list[list[int]],
    rad: float,
) -> None:
    """Test that the radius cannot be computed if the data is out of sync."""
    # Add images to the viewer (view, event, y, x)
    images = np.random.randint(0, 10, (3, 5, 10, 10), "uint8")
    cpt_widget.viewer.add_image(images, name=IMAGE_LAYER_NAME)
    cpt_widget.viewer.dims.set_current_step(0, 0)  # move to view 0
    cpt_widget.viewer.dims.set_current_step(1, 0)  # move to event 0

    # Add new particle
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    # add three points (view, event, y, x) to the points layer and select them
    layer_measurements = cpt_widget._setup_measurement_layer()
    layer_measurements.add([[0, 0] + point for point in three_points])
    layer_measurements.selected_data = {0, 1, 2}

    # change the data event so that it's out of sync
    cpt_widget.viewer.dims.set_current_step(1, 1)  # move to event 1

    # click the calculate radius button and check that it fails
    cpt_widget._on_click_radius()
    captured = capsys.readouterr()
    assert (
        "Measurement points not in current Event. Measurement not completed."
        in captured.out
    )

    # change the data view so that it's out of sync
    cpt_widget.viewer.dims.set_current_step(1, 0)  # move to event 0
    cpt_widget.viewer.dims.set_current_step(0, 1)  # move to view 1

    # click the calculate radius button and check that it fails
    cpt_widget._on_click_radius()
    captured = capsys.readouterr()
    assert (
        "Measurement points not in current View. Measurement not completed."
        in captured.out
    )

    assert cpt_widget.data[0].radius != pytest.approx(
        rad, rel=1e-3
    ), "The radius should not be calculated"

    assert not cpt_widget.table.item(
        0, cpt_widget._get_table_column_index("rpoints")
    ), "The radius points should not be recorded"

    # change the data view so that it's in sync
    cpt_widget.viewer.dims.set_current_step(0, 0)  # move to view 0
    cpt_widget._on_click_radius()

    assert cpt_widget.data[0].radius == pytest.approx(
        rad, rel=1e-3
    ), "The radius should have been calculated"

    assert cpt_widget.table.item(
        0, cpt_widget._get_table_column_index("radius")
    ), "The radius should have been recorded"
    assert cpt_widget.table.item(
        0, cpt_widget._get_table_column_index("rpoints")
    ), "The radius points should have been recorded"


def test_radius_save_preserves_old_data(cpt_widget: ParticleTracksWidget):
    """Test that previous particles' saved radii are not changed by current particle."""
    measurements_layer = cpt_widget._setup_measurement_layer()

    # Add first particle
    cpt_widget.particle_decays_menu.setCurrentIndex(1)  # adds new row
    # Add three points on a circle of radius 1 px
    measurements_layer.add([[0, 0, 0, 1], [0, 0, 1, 0], [0, 0, 0, -1]])  # 1px radius
    # Select the first three points in the layer
    measurements_layer.selected_data = {0, 1, 2}
    # User clicks the radius calculation button
    cpt_widget._on_click_radius()

    # Create a second particle, add points corresponding to a 5 px radius, and click calculate radius.
    cpt_widget.particle_decays_menu.setCurrentIndex(1)
    measurements_layer.add([[0, 0, -6, 3], [0, 0, -3, 2], [0, 0, 0, 3]])  # 5px radius
    measurements_layer.selected_data = {3, 4, 5}
    cpt_widget._on_click_radius()

    first_radius = cpt_widget.data[0].radius
    second_radius = cpt_widget.data[1].radius
    assert (
        first_radius != second_radius
    ), "The radii of different particles should be different"

    first_rpoints = cpt_widget.data[0].rpoints
    second_rpoints = cpt_widget.data[1].rpoints
    assert (
        first_rpoints != second_rpoints
    ), "The points for the radii calculation of different particles should be different"

    first_radius = cpt_widget.data[0].radius_cm
    second_radius = cpt_widget.data[1].radius_cm
    assert (
        first_radius != second_radius
    ), "The radii of different particles should be different"


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

    assert cpt_widget.table.item(0, cpt_widget._get_table_column_index("decay_length"))
    assert cpt_widget.data[0].decay_length == pytest.approx(1, rel=1e-3)


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

    assert "ERROR: Select two points to calculate the decay length." in captured.out


def test_calculate_length_fails_data_out_of_sync(
    cpt_widget: ParticleTracksWidget, capsys: pytest.CaptureFixture[str]
):
    # Add images to the viewer
    images = np.random.randint(0, 10, (3, 5, 10, 10), "uint8")
    cpt_widget.viewer.add_image(images, name=IMAGE_LAYER_NAME)
    cpt_widget.viewer.dims.set_current_step(0, 0)  # move to view 0
    cpt_widget.viewer.dims.set_current_step(1, 0)  # move to event 0

    # Add new particle
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    # add three points (view, event, y, x) to the points layer and select them
    layer_measurements = cpt_widget._setup_measurement_layer()
    layer_measurements.add([(0, 0, 0, 1), (0, 0, 0, 0)])
    layer_measurements.selected_data = {0, 1}

    # change the data event so that it's out of sync
    cpt_widget.viewer.dims.set_current_step(1, 1)  # move to event 1

    # click the calculate radius button and check that it fails
    cpt_widget._on_click_length()
    captured = capsys.readouterr()
    assert (
        "Measurement points not in current Event. Measurement not completed."
        in captured.out
    )

    # change the data view so that it's out of sync
    cpt_widget.viewer.dims.set_current_step(1, 0)  # move to event 0
    cpt_widget.viewer.dims.set_current_step(0, 1)  # move to view 1

    # click the calculate radius button and check that it fails
    cpt_widget._on_click_length()
    captured = capsys.readouterr()
    assert (
        "Measurement points not in current View. Measurement not completed."
        in captured.out
    )

    assert not cpt_widget.table.item(
        0, cpt_widget._get_table_column_index("decay_length")
    ), "The decay length should not be recorded"
    assert cpt_widget.data[0].decay_length != pytest.approx(
        1, rel=1e-3
    ), "The decay length should not be calculated"

    # change the data view so that it's in sync
    cpt_widget.viewer.dims.set_current_step(0, 0)  # move to view 0
    cpt_widget._on_click_length()

    assert cpt_widget.table.item(
        0, cpt_widget._get_table_column_index("decay_length")
    ), "The decay length should be recorded"
    assert cpt_widget.data[0].decay_length == pytest.approx(
        1, rel=1e-3
    ), "The decay length should be calculated"


def test_length_save_preserves_old_data(cpt_widget: ParticleTracksWidget):
    """Test saving a new particle length does not mess up the previous one."""
    measurements_layer = cpt_widget._setup_measurement_layer()

    # Add first particle
    cpt_widget.particle_decays_menu.setCurrentIndex(1)
    # Add two points 1 px apart
    measurements_layer.add([[0, 0, 0, 0], [0, 0, 1, 0]])  # 1px length
    # Select the first two points in the layer
    measurements_layer.selected_data = {0, 1}
    # User clicks the length calculation button
    cpt_widget._on_click_length()

    # Create a second particle, add points corresponding 2px apart, and click calculate length.
    cpt_widget.particle_decays_menu.setCurrentIndex(1)
    measurements_layer.add([[0, 0, 1, 1], [0, 0, 1, 3], [0, 0, 0, 3]])  # 2px length
    measurements_layer.selected_data = {2, 3}
    cpt_widget._on_click_length()

    first_decay_length = cpt_widget.data[0].decay_length
    second_decay_length = cpt_widget.data[1].decay_length
    assert (
        first_decay_length != second_decay_length
    ), "The decay length of different particles should be different"

    first_decay_length = cpt_widget.data[0].decay_length_cm
    second_decay_length = cpt_widget.data[1].decay_length_cm
    assert (
        first_decay_length != second_decay_length
    ), "The decay length of different particles should be different"

    first_dpoints = cpt_widget.data[0].dpoints
    second_dpoints = cpt_widget.data[1].dpoints
    assert (
        first_dpoints != second_dpoints
    ), "The points for the decay length calculation of different particles should be different"
