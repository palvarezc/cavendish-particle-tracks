import napari
import numpy as np
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
)

from ._analysis import FIDUCIAL_BACK, FIDUCIAL_FRONT, Fiducial
from ._calculate import depth, length, magnification, stereoshift


class Set_Fiducial_Dialog(QDialog):
    def __init__(self, parent=None):
        # Call parent constructor
        super().__init__(parent)
        self.parent = parent
        # ignoring ruff style here to make the array clearer
        # fmt:off
        self.points = [
            [Fiducial("Front Fiducial View 1"), Fiducial("Front Fiducial View 2")],
            [Fiducial("Point View 1"), Fiducial("Point View 2")],
            [Fiducial("Back Fiducial View 1"),Fiducial("Back Fiducial View 2")]
        ]
        # fmt:on
        self.point_layer = self._setup_points_layer()

        # region UI Setup
        self.setWindowTitle("Measure Stereoshift and Magnification")
        """ This section is used to select whether the shift of the front
        or rear fiducial plane is subtracted from the shift of the other points.
        It actually makes zero difference to the calculation, but is left in as an
        exercise for students to think about and understand how stereoshift works. """
        lbl_ref_plane = QLabel("Measure shift relative to the: ")
        cmb_set_ref_plane = QComboBox()
        cmb_set_ref_plane.addItems(["front plane", "rear plane"])
        cmb_set_ref_plane.currentIndexChanged.connect(
            self._on_change_cmb_set_ref_plane
        )
        # Labels for the points' coordinates
        lbl_fiducial_coords = QLabel("Fiducial coordinates")
        lbl_front_view1 = QLabel("View 1")
        lbl_front_view2 = QLabel("View 2")
        lbl_point_view1 = QLabel("View 1")
        lbl_point_view2 = QLabel("View 2")
        lbl_back_view1 = QLabel("View 1")
        lbl_back_view2 = QLabel("View 2")
        # Textboxes for the output of point coordinates
        self.textboxes = [QLabel(self) for _ in range(6)]
        # Texbox with calculation formula
        self.label_stereoshift = QLabel(
            "Stereo shift (shift_p/shift_f = depth_p/depth_f)"
        )
        # TODO: work out what these do
        # Textboxes for calculation results
        self.lbl_fiducial_shift = QLabel(self)
        self.lbl_point_shift = QLabel(self)
        self.lbl_stereoshift_ratio = QLabel(self)
        self.lbl_point_depth = QLabel(self)
        self.results = [
            self.lbl_fiducial_shift,
            self.lbl_point_shift,
            self.lbl_stereoshift_ratio,
            self.lbl_point_depth,
        ]
        # Set minimum width for textboxes
        for textbox in (
            self.textboxes + self.results
        ):  # possibly another way of implementing this without creaing an unnecessary list that isn't referenced again
            textbox.setMinimumWidth(200)
        # Control Buttons
        btn_calculate = QPushButton("Calculate")
        # btn_calculate.clicked.connect(self._on_click_calculate) # TODO add this back in
        btn_save = QPushButton("Save to table")
        # btn_save.clicked.connect(self._on_click_save_to_table) # TODO add this back in
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel)
        # self.buttonBox.clicked.connect(self.cancel) # TODO add this back in
        # Layout
        # surely there's a nicer way of doing this grid layout stuff.
        self.setLayout(QGridLayout())
        self.layout().addWidget(lbl_ref_plane, 0, 0, 1, 2)
        self.layout().addWidget(lbl_fiducial_coords, 1, 0, 1, 2)
        self.layout().addWidget(cmb_set_ref_plane, 0, 2)
        for i, widget in enumerate(
            [
                lbl_front_view1,
                self.textboxes[0],
                lbl_front_view2,
                self.textboxes[1],
            ]
        ):
            self.layout().addWidget(widget, i // 2 + 2, i % 2 + 1)
        for i, widget in enumerate(
            [
                lbl_back_view1,
                self.textboxes[2],
                lbl_back_view2,
                self.textboxes[3],
            ]
        ):
            self.layout().addWidget(widget, i // 2 + 5, i % 2 + 1)

        self.layout().addWidget(btn_calculate, 7, 0, 1, 3)
        self.layout().addWidget(
            self.label_stereoshift,
            8,
            0,
            1,
            3,
        )
        # update this once standard decided upon
        self.layout().addWidget(QLabel("Fiducial shift"), 9, 1)
        self.layout().addWidget(self.lbl_fiducial_shift, 9, 2)
        self.layout().addWidget(QLabel("Point shift"), 10, 1)
        self.layout().addWidget(self.lbl_point_shift, 10, 2)
        self.layout().addWidget(QLabel("Ratio"), 11, 1)
        self.layout().addWidget(self.lbl_stereoshift_ratio, 11, 2)
        self.layout().addWidget(QLabel("Point depth (cm)"), 12, 1)
        self.layout().addWidget(self.lbl_point_depth, 12, 2)
        self.layout().addWidget(btn_save, 13, 0, 1, 3)
        self.layout().addWidget(self.buttonBox, 14, 0, 1, 3)
        # endregion

    def _on_change_cmb_set_ref_plane(self) -> None:
        # TODO check if this index is correct, maybe just call the option by name.
        # check how original code works and make sure I've copied the correct functionality.
        if self.cmb_ref_plane() == 0:
            self.label_stereoshift.setText(
                "Stereo shift (shift_p/shift_f = depth_p/depth_f)"
            )
        elif self.cmb_ref_plane() == 1:
            self.label_stereoshift.setText(
                "Stereo shift (shift_p/shift_f = 1 - depth_p/depth_f)"
            )

        self.cal_layer.refresh()

    def _setup_points_layer(self) -> napari.layers.Points:
        # TODO: Is there a better way of typehinting without importing the entirety of Napari>
        # I mean, I assume this import doesn't actually use any extra memory since Napari is imported anyway
        # whilst this plugin is running. But I don't know enough about how Python handles imports / memory usage to be sure.
        # add the points
        points = np.array(
            [
                [100, 100],  # Front Fiducial View 1
                [100, 400],  # Front Fiducial View 2
                [200, 100],  # Point View 1
                [200, 400],  # Point View 2
                [300, 100],  # Back Fiducial View 1
                [300, 400],  # Back Fiducial View 2
                # then expand this to include the magnification points and redo the array
            ]
        )
        # TODO fix all this here and check how it's actually working
        # TODO implment the layer attributes stuff see if i can integrate it with the existing napari stuff
        labels = ["Reference (Front) view1", "Reference (Front) view2"]
        for i in self.points:
            for j in i:
                labels += [j.name]

        colors = ["green", "green", "blue", "blue", "red", "red"]

        text = {
            "string": labels,
            "size": 20,
            "color": colors,
            "translation": np.array([-30, 0]),
        }

        layer_points = self.parent.viewer.add_points(
            points,
            name="Points_Stereoshift",
            text=text,
            size=20,
            edge_width=7,
            edge_width_is_relative=False,
            edge_color=colors,
            face_color=colors,
        )

        return layer_points


""" 
In the original class  FIDUCIAL_VIEWS = [
            "Back fiducial view1",
            "Back fiducial view2",
            "Point view1",
            "Point view2",
        ]

Then Fiducial is a class(FIDUCIAL VIEW PASSED IN as view_name)

Fiducial has name, x, y
xy accesses those properties.

fiducial views is then a list of Fiducial objects, where 1, 2
are the 2 views of the same fiducial used for stereoshift calcualtion.

stift_fiducial is the distance the fiducial has shifted between views.
shift_point is the distance the point has shifted between views.
point_stereoshift?
point_depth?
spoints?

This gets really confusing, really quickly.
We need better names for things.

Proposed overhaul
- got rid of FIDUCIAL_VIEWS, as the const is never referenced again, making it a redundant declaration
  instead, it's declared in the list of objects used by the rest of the program 
  small, pedantic change, but it makes the intent more obvious and reducing the number of lines of code
- declarations were all done in the same place to make the layout code more obvious
- think i changed a load of other things and lost track whoops
- put all the declarations and layout code together instead of interwoven. Otherwise, it can become difficult to imagine what the GUI looks like (and its function)
  without having seen an image of it. Alternatively, can put everything to do with a given UI element together as per -> https://www.pythonguis.com/tutorials/pyqt-layouts/
  would be useful to agree on a std for this.
  Arguably, the latter might be better since items such as lbl_ref_plane never need to be referenced again, so the declaration outside of the layout code is unnecessary.

Stereoshift function:
l is the distance to the camera lens
c is the distance to the first glass plane
t is the thickness of the glass
z is the distance inside the chamber (=0 at front glass pane)

The reference fiducial will shift an amount a
a is subtracted from all the other shifts

Zc is the fiducial z
Zp is the point z
Sp is the point shift
Sc is the fiducial shift
zc=31.6
zp/zc = sp/zc

reverse case test sp=0 => zp=1 true


the spread in values of zp obtained from different pairs is a guide to refractive and other errors incurred.
nb how does this affect the dropdown where they select whatever markers used for the fiducials?


testing results:
- reference shift magnitude affects accuracy of stereoshift calculation, but which is better?
- should we enforce front shift > rear shift > point shift?
"""
