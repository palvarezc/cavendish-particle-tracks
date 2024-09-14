import pytest
from pytestqt.qtbot import QtBot


@pytest.mark.parametrize(
    "click_twice",
    [
        True,
        False,
    ],
)
def test_decay_angles_dialog(cpt_widget, qtbot: QtBot, double_click):
    """Smoke test for the DecayAnglesDialog."""
    cpt_widget.cb.setCurrentIndex(4)

    dialog = cpt_widget._on_click_decay_angles()
    if double_click:
        dialog = cpt_widget._on_click_decay_angles()

    qtbot.addWidget(dialog)

    # show dialog and check that it closes
    with qtbot.waitExposed(dialog):
        dialog.show()
    dialog.close()
    qtbot.waitSignals([dialog.rejected], timeout=5000)
