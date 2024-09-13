import numpy as np
import pytest

from cavendish_particle_tracks._analysis import Fiducial
from cavendish_particle_tracks._calculate import CHAMBER_DEPTH as CD
from cavendish_particle_tracks._calculate import FIDUCIAL_BACK as FB
from cavendish_particle_tracks._calculate import FIDUCIAL_FRONT as FF


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
):
    """Tests the expected behaviour from the expected workflow.
    - Add 4 fiducials in layer
    - Select each point, select a fiducial from the dropdown and click add.
    - Magnification is calculated on click of calculate button.
    - Magnification is propagated to the table when "ok" is clicked.
    """
    dlg = cpt_widget._on_click_magnification()

    # add fiducials
    fiducials = [
        front_fiducial1,
        front_fiducial2,
        back_fiducial1,
        back_fiducial2,
    ]
    combo_boxes = [dlg.cbf1, dlg.cbf2, dlg.cbb1, dlg.cbb2]
    text_boxes = [dlg.txf1, dlg.txf2, dlg.txb1, dlg.txb2]
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
        dlg.cal_layer.add(fiducial.xy)
        dlg.cal_layer.selected_data = {len(dlg.cal_layer.data) - 1}
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
