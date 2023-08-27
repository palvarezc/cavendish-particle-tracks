from math import sqrt

import numpy as np
import pytest
from cavendish_particle_tracks import ParticleTracksWidget
from cavendish_particle_tracks._analysis import CHAMBER_DEPTH as CD


@pytest.mark.parametrize(
    "points, FS, PS, S, D",
    [
        (
            [
                np.array([0, 2]),
                np.array([2, 0]),
                np.array([0, 1]),
                np.array([1, 0]),
            ],
            sqrt(8),
            sqrt(2),
            0.5,
            0.5 * CD,
        ),
        (
            [
                np.array([0, 0]),
                np.array([2, 2]),
                np.array([-1, 0]),
                np.array([0, -1]),
            ],
            sqrt(8),
            sqrt(2),
            0.5,
            0.5 * CD,
        ),
    ],
)
def test_calculate_stereoshift_ui(make_napari_viewer, points, FS, PS, S, D):
    """Test the expected behavior from the expected workflow:

    - Open stereoshift dialog when clicked
    - Record points positions in text boxes.
    - Calculate shift_fiducial, shift_point, stereoshift and depth.
    - The textboxes should be updated.
    """
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100)))
    my_widget = ParticleTracksWidget(viewer)

    # need to click "new particle" to add a row to the table
    my_widget.cb.setCurrentIndex(1)
    my_widget._on_click_new_particle()

    dlg = my_widget._on_click_stereoshift()

    # move points to parameterised positions
    for i in range(4):
        dlg.cal_layer.data[1 + i] = points[i]

    # record points and calculate
    dlg._on_click_calculate()

    # Check recorded points
    for i in range(4):
        assert dlg.textboxes[i].text() == str(points[i])

    # Check calculated values
    assert dlg.tshift_fiducial.text() == str(FS)
    assert dlg.tshift_point.text() == str(PS)
    assert dlg.tstereoshift.text() == str(S)
    assert dlg.tdepth.text() == str(D)
