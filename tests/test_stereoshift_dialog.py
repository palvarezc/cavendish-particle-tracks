from math import sqrt

import numpy as np
import pytest

from cavendish_particle_tracks._analysis import CHAMBER_DEPTH

# from cavendish_particle_tracks._stereoshift_dialog import StereoshiftDialog

# from cavendish_particle_tracks._widget import ParticleTracksWidget


@pytest.mark.parametrize(
    "test_points, expected_fiducial_shift, expected_point_shift, expected_stereoshift, expected_depth",
    [
        (
            [
                np.array([0, 0]),
                np.array([0, 0]),
                np.array([0, 2]),
                np.array([2, 0]),
                np.array([0, 1]),
                np.array([1, 0]),
            ],
            sqrt(8),
            sqrt(2),
            0.5,
            0.5 * CHAMBER_DEPTH,
        ),
        (
            [
                np.array([0, 0]),
                np.array([0, 0]),
                np.array([0, 2]),
                np.array([2, 0]),
                np.array([0, 0]),
                np.array([1, 0]),
            ],
            sqrt(8),
            1.0,
            1 / sqrt(8),
            1 / sqrt(8) * CHAMBER_DEPTH,
        ),
        (
            [
                np.array([0, 1]),
                np.array([1, 0]),
                np.array([0, 0]),
                np.array([2, 2]),
                np.array([-1, 0]),
                np.array([0, -1]),
            ],
            sqrt(10),
            sqrt(0),
            0.0,
            0.0 * CHAMBER_DEPTH,
        ),
    ],
)
def test_calculate_stereoshift_ui(
    cpt_widget,
    test_points,
    expected_fiducial_shift,
    expected_point_shift,
    expected_stereoshift,
    expected_depth,
):
    """Test the expected behavior from the expected workflow:

    - Open stereoshift dialog when clicked
    - Record points positions in text boxes.
    - Calculate shift_fiducial, shift_point, stereoshift and depth.
    - The textboxes should be updated.
    """
    # need to click "new particle" to add a row to the table
    cpt_widget.cb.setCurrentIndex(1)

    dlg = cpt_widget._on_click_stereoshift()

    # move points to parameterised positions
    for i in range(len(test_points)):
        dlg.cal_layer.data[i] = test_points[i]

    # record points and calculate
    dlg._on_click_calculate()

    # Check recorded points
    for i in range(4):
        assert dlg.textboxes[i].text() == str(
            test_points[i + 2] - test_points[i % 2]
        )

    assert dlg.cbf1.currentIndex() == 0

    # Check calculated values
    assert dlg.tshift_fiducial.text() == str(expected_fiducial_shift)
    assert dlg.tshift_point.text() == str(expected_point_shift)
    assert dlg.tstereoshift.text() == str(expected_stereoshift)
    assert dlg.tdepth.text() == str(expected_depth)

    # check save to table
    dlg._on_click_save_to_table()
    assert cpt_widget.data[0].spoints.all() == dlg.spoints.all()
    assert cpt_widget.data[0].shift_fiducial == dlg.shift_fiducial
    assert cpt_widget.data[0].shift_point == dlg.shift_point
    assert cpt_widget.data[0].stereoshift == dlg.point_stereoshift
    # these names should be more consistent between different parts of the program
    assert cpt_widget.data[0].depth_cm == dlg.point_depth
