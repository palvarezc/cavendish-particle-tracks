from __future__ import annotations

from pathlib import Path
from random import random

import numpy as np
import pytest
import tifffile as tf
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialogButtonBox, QMessageBox

from cavendish_particle_tracks._main_widget import ParticleTracksWidget

from .conftest import get_dialog


@pytest.mark.parametrize("bypass", [True, False])
@pytest.mark.parametrize("docking_area", ["left", "bottom"])
def test_open_widget(make_napari_viewer, bypass, docking_area):
    """Test the opening of the widget"""
    viewer = make_napari_viewer()
    widget = ParticleTracksWidget(
        napari_viewer=viewer,
        bypass_force_load_data=bypass,
        docking_area=docking_area,
    )
    assert widget.isVisible() is False
    widget.show()
    assert widget.isVisible() is True

    if bypass:
        return

    # Check the widget behavior before and after loading the data
    assert widget.particle_decays_menu.isEnabled() is False
    assert widget.radius_button.isEnabled() is False
    assert widget.delete_particle.isEnabled() is False
    assert widget.length_button.isEnabled() is False
    assert widget.stereoshift_button.isEnabled() is False
    assert widget.magnification_button.isEnabled() is False
    assert widget.decay_angles_button.isEnabled() is False

    widget.viewer.add_image(np.random.random((100, 100)), name="Particle Tracks")

    assert widget.particle_decays_menu.isEnabled() is True
    assert widget.radius_button.isEnabled() is False
    assert widget.delete_particle.isEnabled() is False
    assert widget.length_button.isEnabled() is False
    assert widget.stereoshift_button.isEnabled() is False
    assert widget.magnification_button.isEnabled() is True
    assert widget.decay_angles_button.isEnabled() is False


def test_calculate_radius_ui(
    cpt_widget: ParticleTracksWidget, capsys: pytest.CaptureFixture[str]
):
    """Test the expected behavior from the expected workflow:

    - Add a particle.
    - Add and select three points.
    - Calculate a radius from this.
    - The table should have the correct radius.
    """
    # need to click "new particle" to add a row to the table
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    # add three points to the points layer and select them
    cpt_widget.layer_measurements = cpt_widget.viewer.add_points(
        [(0, 1), (1, 0), (0, -1)], name="Radii and Lengths"
    )
    cpt_widget.layer_measurements.selected_data = {0, 1, 2}

    # click the calculate radius button
    cpt_widget._on_click_radius()

    # read captured output and check that it's as we expected
    captured = capsys.readouterr()
    expected_lines = ["Adding points to the table:", "calculating radius!"]
    for expected in expected_lines:
        assert expected in captured.out

    assert cpt_widget.table.item(0, cpt_widget._get_table_column_index("radius_px"))
    assert cpt_widget.table.item(0, cpt_widget._get_table_column_index("radius_cm"))
    assert cpt_widget.table.item(0, cpt_widget._get_table_column_index("rpoints"))

    assert cpt_widget.data[0].radius_px == 1.0


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

    # add six random points to the points layer
    points = [(random(), random()) for _ in range(6)]
    cpt_widget.layer_measurements = cpt_widget.viewer.add_points(
        points, name="Radii and Lengths"
    )

    # select the wrong number of points
    cpt_widget.layer_measurements.selected_data = set(range(npoints))

    # click the calculate radius button
    cpt_widget._on_click_radius()
    captured = capsys.readouterr()

    assert "ERROR: Select three points to calculate the path radius." in captured.out


def test_add_new_particle_ui(cpt_widget: ParticleTracksWidget):
    assert cpt_widget.table.rowCount() == 0

    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    assert cpt_widget.table.rowCount() == 1
    assert len(cpt_widget.data) == 1


def test_delete_particle_ui(cpt_widget: ParticleTracksWidget):
    """Tests the removal of a particle from the table"""
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    assert cpt_widget.table.rowCount() == 1
    assert len(cpt_widget.data) == 1

    def close_dialog(dialog):
        buttonbox = dialog.findChild(QDialogButtonBox)
        yesbutton = buttonbox.children()[1]
        yesbutton.click()

    # Open and retrieve file dialog
    get_dialog(
        dialog_trigger=cpt_widget._on_click_delete_particle,
        dialog_action=close_dialog,
        time_out=5,
    )

    assert cpt_widget.table.rowCount() == 0
    assert len(cpt_widget.data) == 0


def test_calculate_length_ui(
    cpt_widget: ParticleTracksWidget, capsys: pytest.CaptureFixture[str]
):
    # add a random image to the napari viewer
    cpt_widget.viewer.add_image(np.random.random((100, 100)))

    # need to click "new particle" to add a row to the table
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    # add three points to the points layer and select them
    cpt_widget.layer_measurements = cpt_widget.viewer.add_points(
        [(0, 1), (0, 0)], name="Radii and Lengths"
    )
    cpt_widget.layer_measurements.selected_data = {0, 1}

    # click the calculate decay length button
    cpt_widget._on_click_length()

    assert cpt_widget.table.item(0, cpt_widget._get_table_column_index("decay_length_px"))
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
    # need to click "new particle" to add a row to the table
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    # add six random points to the points layer
    points = [(random(), random()) for _ in range(6)]
    cpt_widget.layer_measurements = cpt_widget.viewer.add_points(
        points, name="Radii and Lengths"
    )

    # select the wrong number of points
    cpt_widget.layer_measurements.selected_data = set(range(npoints))

    # click the calculate decay length button
    cpt_widget._on_click_length()
    captured = capsys.readouterr()

    assert "ERROR: Select two points to calculate the decay length." in captured.out


@pytest.mark.parametrize(
    "data_subdirs, image_count, expect_data_loaded, reload",
    [
        (["my_view1", "my_view2", "my_view3"], [5, 5, 5], True, False),
        (["my_view1", "my_view2", "my_view3"], [2, 2, 2], True, True),
        (["my_view1", "my_view2"], [2, 2], False, False),
        (["my_view1", "my_view2", "my_view3"], [1, 2, 2], False, False),
        (["my_view1", "my_view2", "no_view"], [2, 2, 2], False, False),
    ],
)
def test_load_data(
    cpt_widget: ParticleTracksWidget,
    tmp_path: Path,
    qtbot: QtBot,
    data_subdirs: list[str],
    image_count: list[int],
    expect_data_loaded: bool,
    reload: bool,
):
    """Test loading of images in a folder as 4D image layer with width, height, event, view dimensions."""

    data_layer_index = 0
    if reload:
        cpt_widget.layer_measurements = cpt_widget.viewer.add_points(
            name="Radii and Lengths"
        )
        data_layer_index = 1

    resolution = 8400 if expect_data_loaded else 10
    for subdir, n in zip(data_subdirs, image_count):
        p = tmp_path / subdir
        p.mkdir()
        for i in range(n):
            data = np.random.randint(0, 255, (resolution, resolution, 3), "uint8")
            tf.imwrite(p / f"temp{i}.tif", data)

    def set_directory_and_close(dialog):
        qtbot.addWidget(dialog)
        dialog.setDirectory(str(tmp_path))
        buttonbox = dialog.findChild(QDialogButtonBox, "buttonBox")
        openbutton = buttonbox.children()[1]
        qtbot.mouseClick(openbutton, Qt.LeftButton, delay=1)

    # Open and retrieve file dialog
    get_dialog(
        dialog_trigger=cpt_widget._on_click_load_data,
        dialog_action=set_directory_and_close,
        time_out=5,
    )

    if expect_data_loaded:
        assert len(cpt_widget.viewer.layers) == 2
        assert cpt_widget.viewer.layers[data_layer_index].name == "Particle Tracks"
        assert cpt_widget.viewer.layers[data_layer_index].ndim == 4
        assert cpt_widget.viewer.dims.current_step[1] == 0
    else:
        # def capture_msgbox():
        #    for widget in QApplication.topLevelWidgets():
        #        # top level, all widgets didn't work, active popup didn't
        #        if isinstance(widget, QMessageBox):
        #            return widget
        #    return None

        # qtbot.waitUntil(capture_msgbox, timeout=1000)
        # msgbox = capture_msgbox()
        msgbox = cpt_widget.msg
        # msgbox = QApplication.activeWindow()
        assert isinstance(msgbox, QMessageBox)
        assert msgbox.icon() == QMessageBox.Warning
        assert msgbox.text() == (
            "The data folder must contain three subfolders, one for each view, and each subfolder must contain the same number (>1) of images."
        )


def test_show_hide_buttons(cpt_widget: ParticleTracksWidget):
    """Test the show/hide buttons"""
    cpt_widget.viewer.add_image(np.random.random((100, 100)), name="Particle Tracks")
    # ideally would like to test isVisible instead of isEnabled, but that requires showing the widget
    # need to think about how to do that, or if it's worth it
    assert cpt_widget.particle_decays_menu.isEnabled() is True
    assert cpt_widget.delete_particle.isEnabled() is False
    assert cpt_widget.radius_button.isEnabled() is False
    assert cpt_widget.length_button.isEnabled() is False
    assert cpt_widget.decay_angles_button.isEnabled() is False
    cpt_widget.particle_decays_menu.setCurrentIndex(1)
    assert cpt_widget.delete_particle.isEnabled() is True
    assert cpt_widget.radius_button.isEnabled() is True
    assert cpt_widget.length_button.isEnabled() is True
    assert cpt_widget.decay_angles_button.isEnabled() is False
    cpt_widget.particle_decays_menu.setCurrentIndex(4)
    assert cpt_widget.delete_particle.isEnabled() is True
    assert cpt_widget.radius_button.isEnabled() is False
    assert cpt_widget.length_button.isEnabled() is True
    assert cpt_widget.decay_angles_button.isEnabled() is True


def test_close_widget(cpt_widget: ParticleTracksWidget, qtbot: QtBot):
    """Test the close button"""
    cpt_widget.particle_decays_menu.setCurrentIndex(4)
    cpt_widget.show()  # the function hideEvent is not called if the widget is not shown

    def check_dialog_and_click_no(dialog):
        assert isinstance(dialog, QMessageBox)
        assert dialog.icon() == QMessageBox.Warning
        assert dialog.text() == (
            "Closing Cavendish Particle Tracks. Any unsaved data will be lost."
        )
        buttonbox = dialog.findChild(QDialogButtonBox)
        nobutton = buttonbox.children()[2]
        nobutton.click()

    get_dialog(
        dialog_trigger=cpt_widget.window().close,
        dialog_action=check_dialog_and_click_no,
        time_out=5,
    )


def test_radius_save_preserves_old_data(cpt_widget):
    """Test that previous particles' saved radii are not changed by current particle."""
    # layer_measurements = cpt_widget._setup_measurement_layer()
    measurements_layer = cpt_widget.viewer.add_points(name="Radii and Lengths", ndim=2)

    # Add first particle
    cpt_widget.particle_decays_menu.setCurrentIndex(1)  # adds new row
    # Add three points on a circle of radius 1 px
    # layer_measurements.add([[0, 0, 0, 1], [0, 0, 1, 0], [0, 0, 0, -1]]) # 1px radius
    measurements_layer.add([[0, 1], [1, 0], [0, -1]])  # 1px radius
    # Select the first three points in the layer
    measurements_layer.selected_data = {0, 1, 2}
    # User clicks the radius calculation button
    cpt_widget._on_click_radius()

    # Create a second particle, add points corresponding to a 5 px radius, and click calculate radius.
    cpt_widget.particle_decays_menu.setCurrentIndex(1)
    # layer_measurements.add([[0, 0, -6, 3], [0, 0, -3, 2], [0, 0, 0, 3]]) # 5px radius
    measurements_layer.add([[-6, 3], [-3, 2], [0, 3]])  # 5px radius
    measurements_layer.selected_data = {3, 4, 5}
    cpt_widget._on_click_radius()

    first_radius = cpt_widget.data[0].radius_px
    second_radius = cpt_widget.data[1].radius_px
    assert (
        first_radius != second_radius
    ), "The radii of different particles should be different"

    first_radius = cpt_widget.data[0].radius_cm
    second_radius = cpt_widget.data[1].radius_cm
    assert (
        first_radius != second_radius
    ), "The radii of different particles should be different"

    first_rpoints = cpt_widget.data[0].rpoints
    second_rpoints = cpt_widget.data[1].rpoints
    assert (
        first_rpoints != second_rpoints
    ), "The points for the radii calculation of different particles should be different"


def test_length_save_preserves_old_data(cpt_widget):
    """Test saving a new particle length does not mess up the previous one."""
    # setup measurement layer
    # layer_measurements = cpt_widget._setup_measurement_layer()
    measurements_layer = cpt_widget.viewer.add_points(name="Radii and Lengths", ndim=2)

    # Add first particle
    cpt_widget.particle_decays_menu.setCurrentIndex(1)
    # Add two points 1 px apart
    # layer_measurements.add([[0, 0, 0, 0], [0, 0, 1, 0]]) # 1px length
    measurements_layer.add([[0, 0], [1, 0]])  # 1px length
    # Select the first two points in the layer
    measurements_layer.selected_data = {0, 1}
    # User clicks the length calculation button
    cpt_widget._on_click_length()

    # Create a second particle, add points corresponding 2px apart, and click calculate length.
    cpt_widget.particle_decays_menu.setCurrentIndex(1)
    # layer_measurements.add([[0, 0, 1, 1], [0, 0, 1, 3], [0, 0, 0, 3]]) # 2px length
    measurements_layer.add([[1, 1], [1, 3]])  # 2px length
    measurements_layer.selected_data = {2, 3}
    cpt_widget._on_click_length()

    first_decay_length = cpt_widget.data[0].decay_length_px
    second_decay_length = cpt_widget.data[1].decay_length_px
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
