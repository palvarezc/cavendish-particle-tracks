import pytest
import numpy as np


@pytest.mark.parametrize(
    "test_points",
    [
        (
            np.array([0, 0]),
            np.array([0, 0]),
            np.array([0, 2]),
            np.array([2, 0]),
            np.array([0, 1]),
            np.array([1, 0]),
        )
    ],
)
def test_magnification_ui_expected(magnification_dialog):
    """Tests the expected behaviour from the expected workflow.
    - Add 4 points in layer
    - Select each point, select a fiducial from the dropdown and click add.
    - Magnification is calculated on click of calculate button.
    - Magnification is propgated to the table when "ok" is clicked.
    """


def test_magnification_onclick_cancel(cpt_widget):
    """Tests the expected behaviour of clicking the cancel button."""
    cpt_widget.cb.setCurrentIndex(
        1
    )  # these shared methods between tests might
    # be worth merging near the end of development because the tests take a fair bit of time to run.
    dlg_magnification = cpt_widget._on_click_magnification()

    # add 4 points to the points layer
    cpt_widget.viewer.add_points([(0, 0), (1, 0), (0, 1), (1, 1)])
    # for i in range(len)
