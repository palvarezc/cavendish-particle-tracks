from pytestqt.qtbot import QtBot

from cavendish_particle_tracks._decay_angles_dialog import DecayAnglesDialog


def test_decay_angles_dialog(cpt_widget, qtbot: QtBot):
    """Smoke test for the DecayAnglesDialog."""
    dialog = DecayAnglesDialog(parent=cpt_widget)
    qtbot.addWidget(dialog)

    # show dialog and check that it closes
    dialog.show()
    qtbot.waitForWindowShown(dialog)
    dialog.close()
    qtbot.waitSignals([dialog.rejected], timeout=5000)
