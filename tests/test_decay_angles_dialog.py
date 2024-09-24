import pytest
from pytestqt.qtbot import QtBot


@pytest.mark.parametrize(
    "click_twice",
    [
        True,
        False,
    ],
)
def test_decay_angles_dialog(cpt_widget, qtbot: QtBot, click_twice: bool):
    """Smoke test for the DecayAnglesDialog."""
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
