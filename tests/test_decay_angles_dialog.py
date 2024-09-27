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


def test_decay_vertex_update(cpt_widget):

    cpt_widget.particle_decays_menu.setCurrentIndex(4)
    dialog = cpt_widget._on_click_decay_angles()

    data = dialog.cal_layer.data

    # Move the decay vertex
    old_value = data[0][0][0]
    data[0][0][0] = old_value + 50
    dialog.cal_layer.data = (
        data  # For some reason, this doesn't trigger the change event
    )
    dialog.cal_layer.events.data(action="changed", data_indices=(0,))

    # Check that the decay vertex has been updated
    assert dialog.cal_layer.data[0][0][0] == old_value + 50
    assert (dialog.cal_layer.data[1][0] == data[0][0]).all()
    assert (dialog.cal_layer.data[2][0] == data[0][0]).all()
