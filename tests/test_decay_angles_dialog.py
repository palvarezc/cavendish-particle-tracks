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
