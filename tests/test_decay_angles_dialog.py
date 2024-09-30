import numpy as np
import pytest
from pytestqt.qtbot import QtBot

from cavendish_particle_tracks._decay_angles_dialog import ANGLES_LAYER_NAME


@pytest.mark.parametrize(
    "click_twice",
    [
        True,
        False,
    ],
)
def test_open_and_close_decay_angles_dialog(cpt_widget, qtbot: QtBot, click_twice: bool):
    """Test the expected behavior from the expected workflow:"""
    cpt_widget.particle_decays_menu.setCurrentIndex(4)

    # The user clicks the button (also test fringe case that they click the button again).
    if click_twice:
        cpt_widget._on_click_decay_angles()
    dialog = cpt_widget._on_click_decay_angles()

    qtbot.addWidget(dialog)

    # show dialog and check that it closes
    with qtbot.waitExposed(dialog):
        dialog.show()
    dialog.close()
    qtbot.waitSignals([dialog.rejected], timeout=5000)

    assert not cpt_widget.decay_angles_dlg.isVisible()
    assert ANGLES_LAYER_NAME in cpt_widget.viewer.layers
    assert not cpt_widget.decay_angles_dlg.cal_layer.visible

    # Click again to test that the dialog opens again
    cpt_widget._on_click_decay_angles()
    assert cpt_widget.decay_angles_dlg.isVisible()
    assert ANGLES_LAYER_NAME in cpt_widget.viewer.layers
    assert cpt_widget.decay_angles_dlg.cal_layer.visible

    # close the dialog
    cpt_widget.decay_angles_dlg.reject()
    assert not cpt_widget.decay_angles_dlg.isVisible()
    assert ANGLES_LAYER_NAME in cpt_widget.viewer.layers
    assert not cpt_widget.decay_angles_dlg.cal_layer.visible


def test_decay_vertex_update(cpt_widget):

    cpt_widget.particle_decays_menu.setCurrentIndex(4)
    dialog = cpt_widget._on_click_decay_angles()

    # Move the decay vertex of the Lambda
    old_value = dialog.cal_layer.data[0][0][0]
    dialog.cal_layer.data[0][0][0] = old_value + 50
    # For some reason, this doesn't trigger the change event
    dialog.cal_layer.events.data(action="changed", data_indices=(0,))

    # Check that the decay vertex has been updated
    assert dialog.cal_layer.data[0][0][0] == old_value + 50
    assert (dialog.cal_layer.data[1][0] == data[0][0]).all()
    assert (dialog.cal_layer.data[2][0] == data[0][0]).all()

    # Move two tracks simultaneously
    data = dialog.cal_layer.data
    old_value = data[0][0][0]
    data[1][0][0] = old_value + 50
    data[2][0][0] = old_value + 50
    dialog.cal_layer.data = data  # For some reason, this doesn't trigger the change event
    dialog.cal_layer.events.data(action="changed", data_indices=(1, 2))

    # Check that the decay vertex has been updated
    assert dialog.cal_layer.data[0][0][0] == old_value + 50


@pytest.mark.parametrize(
    "Lambda_track, p_track, pi_track, phi_proton, phi_pion",
    [
        (
            [[0, 0], [-1, 0]],
            [[0, 0], [1, 1]],
            [[0, 0], [1, -1]],
            np.pi / 4,
            -1 * np.pi / 4,
        ),
    ],
)
def test_calculate_decay_angles_ui(
    cpt_widget, Lambda_track, p_track, pi_track, phi_proton, phi_pion
):
    cpt_widget.particle_decays_menu.setCurrentIndex(4)
    dialog = cpt_widget._on_click_decay_angles()

    dialog.cal_layer.data = np.array([Lambda_track, p_track, pi_track])

    # Calculate the decay angles
    dialog._on_click_calculate()

    # Check that the decay angles have been calculated
    assert dialog.phi_proton == pytest.approx(phi_proton, rel=1e-6)
    assert dialog.phi_pion == pytest.approx(phi_pion, rel=1e-6)

    dialog.show()

    # Check the values are saved correctly
    dialog._on_click_save_to_table()

    assert cpt_widget.data[-1].phi_proton == pytest.approx(phi_proton, rel=1e-6)
    assert cpt_widget.data[-1].phi_pion == pytest.approx(phi_pion, rel=1e-6)


def test_decay_angles_save_preserves_old_data(cpt_widget):
    """Test saving a new particle decay angles does not mess up the previous one."""
    # open the dialog
    dlg = cpt_widget._on_click_decay_angles()

    # create a new particle and calculate stereoshift
    cpt_widget.particle_decays_menu.setCurrentIndex(4)
    dlg._on_click_calculate()
    dlg._on_click_save_to_table()
    first_particle_phi_proton = cpt_widget.data[0].phi_proton
    first_particle_phi_pion = cpt_widget.data[0].phi_pion

    # create a second particle and calculate stereoshift
    cpt_widget.particle_decays_menu.setCurrentIndex(4)
    # move Lambda shape to change decay angles
    dlg.cal_layer.data[0][1] += -20
    dlg._on_click_calculate()
    assert (
        dlg.phi_proton != first_particle_phi_proton
    ), "The proton angle should be different."
    assert dlg.phi_pion != first_particle_phi_pion, "The pion angle should be different."
    dlg._on_click_save_to_table()

    first_particle_phi_proton = cpt_widget.data[0].phi_proton
    first_particle_phi_pion = cpt_widget.data[0].phi_pion
    second_particle_phi_proton = cpt_widget.data[1].phi_proton
    second_particle_phi_pion = cpt_widget.data[1].phi_pion

    assert (
        first_particle_phi_proton != second_particle_phi_proton
    ), "The depths should be different."
    assert (
        first_particle_phi_pion != second_particle_phi_pion
    ), "The depths should be different."
