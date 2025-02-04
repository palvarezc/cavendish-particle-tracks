import numpy as np
import pytest

from cavendish_particle_tracks._calculate import CHAMBER_DEPTH as CD
from cavendish_particle_tracks._calculate import FIDUCIAL_BACK as FB
from cavendish_particle_tracks._calculate import FIDUCIAL_FRONT as FF
from cavendish_particle_tracks._magnification_dialog import MAGNIFICATION_LAYER_NAME
from cavendish_particle_tracks.analysis import Fiducial


def test_open_and_close_magnification_dialog(cpt_widget):
    """Test the expected behavior from the expected workflow:"""
    # open the dialog
    cpt_widget._on_click_magnification()
    assert cpt_widget.mag_dlg.isVisible()
    assert MAGNIFICATION_LAYER_NAME in cpt_widget.viewer.layers
    assert cpt_widget.mag_dlg.magnification_layer.visible

    # close the dialog
    cpt_widget.mag_dlg.reject()
    assert not cpt_widget.mag_dlg.isVisible()
    assert MAGNIFICATION_LAYER_NAME in cpt_widget.viewer.layers
    assert not cpt_widget.mag_dlg.magnification_layer.visible

    # Click again to test that the dialog opens again
    cpt_widget._on_click_magnification()
    assert cpt_widget.mag_dlg.isVisible()
    assert MAGNIFICATION_LAYER_NAME in cpt_widget.viewer.layers
    assert cpt_widget.mag_dlg.magnification_layer.visible


@pytest.mark.parametrize("click_twice", [True, False])
@pytest.mark.parametrize(
    "front_fiducial1, front_fiducial2, back_fiducial1, back_fiducial2, expected_magnification_params",
    [
        (
            Fiducial("C'", *FF["C'"]),
            Fiducial("F'", *FF["F'"]),
            Fiducial("C", *FB["C"]),
            Fiducial("F", *FB["F"]),
            (1.0, 0.0),
        ),
        (
            Fiducial("C'", *np.multiply(2, FF["C'"])),
            Fiducial("F'", *np.multiply(2, FF["F'"])),
            Fiducial("C", *np.multiply(2, FB["C"])),
            Fiducial("F", *np.multiply(2, FB["F"])),
            (0.5, 0.0),
        ),
        (
            Fiducial("C'", *np.multiply(2, FF["C'"])),
            Fiducial("F'", *np.multiply(2, FF["F'"])),
            Fiducial("C", *np.divide(FB["C"], 0.5 + 0.3 * CD)),
            Fiducial("F", *np.divide(FB["F"], 0.5 + 0.3 * CD)),
            (0.5, 0.3),
        ),
    ],
)
def test_magnification_ui(
    cpt_widget,
    front_fiducial1,
    front_fiducial2,
    back_fiducial1,
    back_fiducial2,
    expected_magnification_params,
    click_twice,
):
    """Tests the expected behaviour from the expected workflow.
    - Add 4 fiducials in layer
    - Select each point, select a fiducial from the dropdown and click add.
    - Magnification is calculated on click of calculate button.
    - Magnification is propagated to the table when "ok" is clicked.
    """

    # Add a particle to the table
    cpt_widget.particle_decays_menu.setCurrentIndex(1)

    # The user opens the child dialog (also test fringe case that they click the button again).
    if click_twice:
        cpt_widget._on_click_magnification()
    dlg = cpt_widget._on_click_magnification()

    # add fiducials
    fiducials = [
        front_fiducial1,
        front_fiducial2,
        back_fiducial1,
        back_fiducial2,
    ]
    combo_boxes = [
        dlg.front1_fiducial_combobox,
        dlg.front2_fiducial_combobox,
        dlg.back1_fiducial_combobox,
        dlg.back2_fiducial_combobox,
    ]
    text_boxes = [
        dlg.txt_f1coord,
        dlg.txt_f2coord,
        dlg.txt_b1coord,
        dlg.txt_b2coord,
    ]
    add_fiducial_funcs = [
        dlg._on_click_add_coords_f1,
        dlg._on_click_add_coords_f2,
        dlg._on_click_add_coords_b1,
        dlg._on_click_add_coords_b2,
    ]
    recorded_fiducials = [dlg.f1, dlg.f2, dlg.b1, dlg.b2]

    for fiducial, cb, _text_box, add_fiducial_func, recorded_fiducial in zip(
        fiducials,
        combo_boxes,
        text_boxes,
        add_fiducial_funcs,
        recorded_fiducials,
    ):
        cb.setCurrentIndex(cb.findText(fiducial.name))
        dlg.magnification_layer.add(fiducial.xy)
        dlg.magnification_layer.selected_data = {len(dlg.magnification_layer.data) - 1}
        add_fiducial_func()
        assert recorded_fiducial == fiducial
        # TODO: check text box

    dlg._on_click_magnification()
    assert dlg.a == pytest.approx(expected_magnification_params[0], rel=1e-3)
    assert dlg.b == pytest.approx(expected_magnification_params[1], rel=1e-3)

    assert dlg.table.item(0, 0).text() == str(expected_magnification_params[0])
    assert dlg.table.item(0, 1).text() == str(expected_magnification_params[1])

    dlg.accept()
    assert cpt_widget.mag_a == expected_magnification_params[0]
    assert cpt_widget.mag_b == expected_magnification_params[1]
    assert cpt_widget.data[0].magnification_a == expected_magnification_params[0]
    assert cpt_widget.data[0].magnification_b == expected_magnification_params[1]
    assert cpt_widget.mag_measured

    # Add another particle to the table and check that the magnification parameters are the same
    cpt_widget.particle_decays_menu.setCurrentIndex(1)
    assert cpt_widget.data[0].magnification_a == cpt_widget.data[-1].magnification_a
    assert cpt_widget.data[0].magnification_b == cpt_widget.data[-1].magnification_b

    # Update the magnification parameters
    dlg = cpt_widget._on_click_magnification()
    newfiducial = Fiducial("F'", *FF["F'"])
    newfiducial.x *= 1.5
    dlg.magnification_layer.add(newfiducial.xy)
    dlg.magnification_layer.selected_data = {len(dlg.magnification_layer.data) - 1}
    dlg._on_click_add_coords_f2()
    dlg._on_click_magnification()

    # Check that the magnification parameters are different
    assert dlg.a != pytest.approx(expected_magnification_params[0], rel=1e-3)
    assert dlg.b != pytest.approx(expected_magnification_params[1], rel=1e-3)
    dlg.accept()

    # Add another particle to the table and check that the magnification parameters are different
    cpt_widget.particle_decays_menu.setCurrentIndex(1)
    assert cpt_widget.data[0].magnification_a != cpt_widget.data[-1].magnification_a
    assert cpt_widget.data[0].magnification_b != cpt_widget.data[-1].magnification_b


def test_magnification_cancel(cpt_widget):
    """Tests magnification parameters are not updated when clicking the cancel button."""

    dlg = cpt_widget._on_click_magnification()

    pre_mag_a = cpt_widget.mag_a
    pre_mag_b = cpt_widget.mag_b

    dlg.a = pre_mag_a + 1
    dlg.b = pre_mag_b + 1

    dlg.reject()

    assert pre_mag_a == cpt_widget.mag_a
    assert pre_mag_b == cpt_widget.mag_b
