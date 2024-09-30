from math import sqrt

import numpy as np
import pytest

from cavendish_particle_tracks.analysis import CHAMBER_DEPTH


def test_open_and_close_stereoshift_dialog(cpt_widget):
    """Test the expected behavior from the expected workflow:

    - Open stereoshift dialog when clicked
    - Close the dialog
    """
    # open the dialog
    cpt_widget._on_click_stereoshift()
    assert cpt_widget.stereoshift_dlg.isVisible()
    assert "Points_Stereoshift" in cpt_widget.viewer.layers
    assert cpt_widget.stereoshift_dlg.cal_layer.visible

    # close the dialog
    cpt_widget.stereoshift_dlg.reject()
    assert not cpt_widget.stereoshift_dlg.isVisible()
    assert "Points_Stereoshift" in cpt_widget.viewer.layers
    assert not cpt_widget.stereoshift_dlg.cal_layer.visible

    # Click again to test that the dialog opens again
    cpt_widget._on_click_stereoshift()
    assert cpt_widget.stereoshift_dlg.isVisible()
    assert "Points_Stereoshift" in cpt_widget.viewer.layers
    assert cpt_widget.stereoshift_dlg.cal_layer.visible


@pytest.mark.parametrize("vertex", ["origin", "decay"])
@pytest.mark.parametrize(
    "test_points, expected_fiducial_shift, expected_point_shift, expected_stereoshift, expected_depth, double_click",
    [
        (
            [
                np.array([0.0, 0.0]),
                np.array([0.0, 0.0]),
                np.array([0.0, 2.0]),
                np.array([2.0, 0.0]),
                np.array([0.0, 1.0]),
                np.array([1.0, 0.0]),
            ],
            sqrt(8),
            sqrt(2),
            0.5,
            0.5 * CHAMBER_DEPTH,
            True,
        ),
        (
            [
                np.array([0.0, 0.0]),
                np.array([0.0, 0.0]),
                np.array([0.0, 2.0]),
                np.array([2.0, 0.0]),
                np.array([0.0, 0.0]),
                np.array([1.0, 0.0]),
            ],
            sqrt(8),
            1.0,
            1 / sqrt(8),
            1 / sqrt(8) * CHAMBER_DEPTH,
            False,
        ),
        (
            [
                np.array([0.0, 1.0]),
                np.array([1.0, 0.0]),
                np.array([0.0, 0.0]),
                np.array([2.0, 2.0]),
                np.array([-1.0, 0.0]),
                np.array([0.0, -1.0]),
            ],
            sqrt(10),
            sqrt(0),
            0.0,
            0.0 * CHAMBER_DEPTH,
            False,
        ),
    ],
)
def test_calculate_stereoshift_ui(
    cpt_widget,
    vertex,
    test_points,
    expected_fiducial_shift,
    expected_point_shift,
    expected_stereoshift,
    expected_depth,
    double_click,
):
    """Test the expected behavior from the expected workflow:

    - Open stereoshift dialog when clicked
    - Record points positions in text boxes.
    - Calculate shift_fiducial, shift_point, stereoshift and depth.
    - The textboxes should be updated.
    """
    # need to click "new particle" to add a row to the table
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    stereoshift_dialog = cpt_widget._on_click_stereoshift()
    if double_click:
        stereoshift_dialog = cpt_widget._on_click_stereoshift()

    stereoshift_dialog.vertex_combobox.setCurrentIndex(0 if vertex == "origin" else 1)

    # move points to parameterised positions
    for i in range(len(test_points)):
        stereoshift_dialog.cal_layer.data[i] = test_points[i]

    # record points and calculate
    stereoshift_dialog._on_click_calculate()

    # Check recorded points
    for i in range(4):
        assert stereoshift_dialog.textboxes[i].text() == str(
            test_points[i + 2] - test_points[i % 2]
        )

    # Check calculated values
    assert stereoshift_dialog.tshift_fiducial.text() == str(expected_fiducial_shift)
    assert stereoshift_dialog.tshift_point.text() == str(expected_point_shift)
    assert stereoshift_dialog.tstereoshift.text() == str(expected_stereoshift)
    assert stereoshift_dialog.tdepth.text() == str(expected_depth)

    # check save to table
    stereoshift_dialog._on_click_save_to_table()

    # select the stereoshift info corresponding to the correct vertex
    if vertex == "origin":
        data = cpt_widget.data[0].origin_vertex_stereoshift_info
    else:
        data = cpt_widget.data[0].decay_vertex_stereoshift_info

    assert data.spoints == stereoshift_dialog.stereoshift_info.spoints
    assert data.shift_fiducial == stereoshift_dialog.stereoshift_info.shift_fiducial
    assert data.shift_point == stereoshift_dialog.stereoshift_info.shift_point
    assert data.stereoshift == stereoshift_dialog.stereoshift_info.stereoshift
    # TODO: these names should be more consistent between different parts of the program
    assert data.depth_cm == stereoshift_dialog.stereoshift_info.depth_cm


def test_stereoshift_save_to_table_fails_with_empty_table(cpt_widget, capsys):
    """Test the expected failure modes: if I don't have any data in the table."""
    # open the dialog
    stereoshift_dialog = cpt_widget._on_click_stereoshift()

    # click the save to table button
    stereoshift_dialog._on_click_save_to_table()
    captured = capsys.readouterr()

    assert "ERROR: There are no particles in the table." in captured.out


def test_stereoshift_save_preserves_old_data(cpt_widget):
    """Test saving a new particle stereoshift does not mess up the previous one."""
    # open the dialog
    stereoshift_dialog = cpt_widget._on_click_stereoshift()

    # create a new particle and calculate stereoshift
    cpt_widget.particle_decays_menu.setCurrentIndex(1)
    # move reference point to avoid the default nan
    stereoshift_dialog.cal_layer.data[0][1] += -50
    stereoshift_dialog._on_click_calculate()
    stereoshift_dialog._on_click_save_to_table()
    first_particle_depth = cpt_widget.data[0].origin_vertex_stereoshift_info.depth_cm

    # create a second particle and calculate stereoshift
    cpt_widget.particle_decays_menu.setCurrentIndex(1)
    # move point to change depth
    stereoshift_dialog.cal_layer.data[-1][1] += -20
    stereoshift_dialog._on_click_calculate()
    assert (
        stereoshift_dialog.stereoshift_info.depth_cm != first_particle_depth
    ), "The depths should be different."
    stereoshift_dialog._on_click_save_to_table()

    first_particle_depth = cpt_widget.data[0].origin_vertex_stereoshift_info.depth_cm
    second_particle_depth = cpt_widget.data[1].origin_vertex_stereoshift_info.depth_cm
    assert (
        first_particle_depth != second_particle_depth
    ), "The depths should be different."

    first_spoints = cpt_widget.data[0].origin_vertex_stereoshift_info.spoints
    second_spoints = cpt_widget.data[1].origin_vertex_stereoshift_info.spoints
    assert (
        first_spoints != second_spoints
    ), "The points for the stereoshift calculation of different particles should be different"
