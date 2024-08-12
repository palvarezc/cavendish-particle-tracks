import os
import time
from random import random
from typing import Callable

import numpy as np
import pytest
import tifffile as tf
from cavendish_particle_tracks import ParticleTracksWidget
from qtpy.QtCore import Qt, QTimer
from qtpy.QtWidgets import (  # QFileDialog
    QApplication,
    QDialog,
    QDialogButtonBox,
)


def get_dialog(
    dialog_trigger: Callable,
    dialog_action: Callable,
    time_out: int = 5,
    trigger_option: int = 1,
) -> QDialog:
    """
    Returns the current dialog (active modal widget). If there is no
    dialog, it waits until one is created for a maximum of 5 seconds (by
    default).

    :param dialog_trigger: Callable that triggers the dialog creation.
    :param time_out: Maximum time (seconds) to wait for the dialog creation.
    """

    dialog: QDialog = None
    start_time = time.time()

    # Helper function to catch the dialog instance and hide it
    def dialog_creation():
        # Wait for the dialog to be created or timeout
        nonlocal dialog
        while dialog is None and time.time() - start_time < time_out:
            dialog = QApplication.activeModalWidget()

        # Avoid errors when dialog is not created
        if dialog is not None:
            # Perform action dialog_action()
            # dialog.hide() and dialog.close() do not seem to work
            dialog_action(dialog)

    # Create a thread to get the dialog instance and call dialog_creation trigger
    QTimer.singleShot(1, dialog_creation)
    dialog_trigger(trigger_option)

    # Wait for the dialog to be created or timeout
    while dialog is None and time.time() - start_time < time_out:
        continue

    assert isinstance(
        dialog, QDialog
    ), f"No dialog was created after {time_out} seconds. Dialog type: {type(dialog)}"

    return dialog


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

    assert my_widget.data[0].radius_px == 1.0


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
        "ERROR: Select three points to calculate the path radius."
        in captured.out
    )


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

    # click the calculate decay length button
    my_widget._on_click_length()

    assert my_widget.table.item(
        0, my_widget._get_table_column_index("decay_length_px")
    )
    assert (
        my_widget.table.item(
            0, my_widget._get_table_column_index("decay_length_px")
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

    # click the calculate decay length button
    widget._on_click_length()
    captured = capsys.readouterr()

    assert (
        "ERROR: Select two points to calculate the decay length."
        in captured.out
    )


@pytest.mark.parametrize(
    "image_folder",
    [
        "./test_data_view1",
    ],
)
def test_load_data(make_napari_viewer, qtbot, image_folder):
    """Test loading of images in a folder as stack associated to a certain view"""

    os.mkdir(image_folder)
    data = np.random.randint(0, 255, (256, 256, 3), "uint8")
    tf.imwrite(image_folder + "/temp1.tif", data, photometric="rgb")
    data = np.random.randint(0, 255, (256, 256, 3), "uint8")
    tf.imwrite(image_folder + "/temp2.tif", data, photometric="rgb")

    viewer = make_napari_viewer()
    widget = ParticleTracksWidget(viewer)

    def set_directory_and_close(dialog):
        qtbot.addWidget(dialog)
        dialog.setDirectory(image_folder)
        buttonbox = dialog.findChild(QDialogButtonBox, "buttonBox")
        openbutton = buttonbox.children()[1]
        qtbot.mouseClick(openbutton, Qt.LeftButton, delay=1)

    # Open and retrieve file dialog
    get_dialog(
        widget.load.setCurrentIndex,
        set_directory_and_close,
        time_out=5,
        trigger_option=1,
    )

    assert viewer.layers[0].name == "View1", "View1 layer has not been created"
    assert viewer.layers[0].ndim == 3, "Layer is not a stack"

    os.remove(image_folder + "/temp1.tif")
    os.remove(image_folder + "/temp2.tif")
    os.rmdir(image_folder)
