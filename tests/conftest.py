import time
from collections.abc import Callable

import pytest
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QApplication, QDialog

from cavendish_particle_tracks._widget import ParticleTracksWidget


@pytest.fixture
def cpt_widget(make_napari_viewer):
    """Common test setup fixture: calls the napari helper fixture
    `make_napari_viewer` then creates the ParticleTracksWidget."""
    viewer = make_napari_viewer()
    widget = ParticleTracksWidget(napari_viewer=viewer)
    return widget


def get_dialog(
    dialog_trigger: Callable,
    dialog_action: Callable,
    time_out: int = 5,
) -> QDialog:
    """
    Returns the current dialog (active modal widget). If there is no
    dialog, it waits until one is created for a maximum of 5 seconds (by
    default).

    :param dialog_trigger: Callable that triggers the dialog creation.
    :param dialog_action: Callable that manipulates and closes/hides the dialog.
    :param time_out: Maximum time (seconds) to wait for the dialog creation.
    """

    dialog: QDialog = None
    start_time = time.time()

    def dialog_capture():
        """Nested function to catch the dialog instance and hide it"""
        # Wait for the dialog to be created or timeout
        nonlocal dialog
        while dialog is None and time.time() - start_time < time_out:
            dialog = QApplication.activeModalWidget()

        # Avoid errors when dialog is not created
        if dialog is not None:
            dialog_action(dialog)

    # Create a thread to get the dialog instance and call dialog_creation trigger
    QTimer.singleShot(1, dialog_capture)
    dialog_trigger()

    # Wait for the dialog to be created or timeout
    while dialog is None and time.time() - start_time < time_out:
        continue

    assert isinstance(
        dialog, QDialog
    ), f"No dialog was created after {time_out} seconds. Dialog type: {type(dialog)}"

    return dialog
