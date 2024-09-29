import pytest
from pytestqt.qtbot import QtBot


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
    assert "Decay Angles Tool" in cpt_widget.viewer.layers
    assert not cpt_widget.decay_angles_dlg.cal_layer.visible

    # Click again to test that the dialog opens again
    cpt_widget._on_click_decay_angles()
    assert cpt_widget.decay_angles_dlg.isVisible()
    assert "Decay Angles Tool" in cpt_widget.viewer.layers
    assert cpt_widget.decay_angles_dlg.cal_layer.visible

    # close the dialog
    cpt_widget.decay_angles_dlg.reject()
    assert not cpt_widget.decay_angles_dlg.isVisible()
    assert "Decay Angles Tool" in cpt_widget.viewer.layers
    assert not cpt_widget.decay_angles_dlg.cal_layer.visible
