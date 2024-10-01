from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import tifffile as tf
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialogButtonBox, QMessageBox

from cavendish_particle_tracks._main_widget import (
    IMAGE_LAYER_NAME,
    MEASUREMENTS_LAYER_NAME,
    ParticleTracksWidget,
)

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

    widget.viewer.add_image(np.random.random((100, 100)), name=IMAGE_LAYER_NAME)

    assert widget.particle_decays_menu.isEnabled() is True
    assert widget.radius_button.isEnabled() is False
    assert widget.delete_particle.isEnabled() is False
    assert widget.length_button.isEnabled() is False
    assert widget.stereoshift_button.isEnabled() is False
    assert widget.magnification_button.isEnabled() is True
    assert widget.decay_angles_button.isEnabled() is False


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
            name=MEASUREMENTS_LAYER_NAME
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
        assert cpt_widget.viewer.layers[data_layer_index].name == IMAGE_LAYER_NAME
        assert cpt_widget.viewer.layers[data_layer_index].ndim == 4
        assert cpt_widget.viewer.dims.current_step[1] == 0

        # Add a new particle and check the event_number is recorded correctly
        # Move to event 1
        cpt_widget.viewer.dims.set_current_step(1, 1)
        # Add a new particle
        cpt_widget.particle_decays_menu.setCurrentIndex(1)
        assert cpt_widget.table.rowCount() == 1
        assert cpt_widget.data[0].event_number == 1, "The event number should be 1"
        assert (
            cpt_widget.table.item(
                0, cpt_widget._get_table_column_index("event_number")
            ).text()
            == "1"
        )

        # Check that apply_magnification does not show anything in the table
        cpt_widget._apply_magnification()
        assert not cpt_widget.table.item(
            0, cpt_widget._get_table_column_index("radius_cm")
        ), "The calibrated radius should not be shown in the table"
        assert not cpt_widget.table.item(
            0, cpt_widget._get_table_column_index("decay_length_cm")
        ), "The calibrated radius should not be shown in the table"

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
    cpt_widget.viewer.add_image(np.random.random((100, 100)), name=IMAGE_LAYER_NAME)
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
