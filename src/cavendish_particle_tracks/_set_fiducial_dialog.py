import napari
import numpy as np
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
)

from ._analysis import FIDUCIAL_BACK, FIDUCIAL_FRONT, Fiducial
from ._calculate import (
    corrected_length,
    depth,
    magnification,
    stereoshift,
)


class Set_Fiducial_Dialog(QDialog):
    def __init__(self, parent):
        # Call parent constructor
        super().__init__(parent)
        self.parent = parent

        # region Stereoshift
        # ignoring ruff style here to make the array clearer
        # fmt:off
        self.points = [
            [Fiducial("Front Fiducial View 1"), Fiducial("Front Fiducial View 2")],
            [Fiducial("Point View 1"), Fiducial("Point View 2")],
            [Fiducial("Back Fiducial View 1"),Fiducial("Back Fiducial View 2")]
        ]
        # fmt:on
        self.shift_fiducial = 0.0
        self.shift_point = 0.0
        self.point_stereoshift = 0.0
        self.point_depth = -1.0
        self.spoints = []
        # endregion
        self.layer_points = self._setup_points_layer()

        # region UI Setup
        self.setWindowTitle("Measure Stereoshift and Magnification")
        """ This section is used to select whether the shift of the front
        or rear fiducial plane is subtracted from the shift of the other points.
        It actually makes zero difference to the calculation, but is left in as an
        exercise for students to think about and understand how stereoshift works. """
        lbl_ref_plane = QLabel("Measure shift relative to the: ")
        self.cmb_set_ref_plane = QComboBox()
        self.cmb_set_ref_plane.addItems(["front plane", "rear plane"])
        self.cmb_set_ref_plane.currentIndexChanged.connect(
            self._on_change_cmb_set_ref_plane
        )
        # Labels for the points' coordinates
        lbl_fiducial_coords = QLabel("Fiducial coordinates")
        lbl_front_view1 = QLabel("View 1")
        lbl_front_view2 = QLabel("View 2")
        lbl_point_view1 = QLabel("View 1")
        lbl_point_view2 = QLabel("View 2")  # TODO Implement these
        lbl_back_view1 = QLabel("View 1")
        lbl_back_view2 = QLabel("View 2")
        # Textboxes for the output of point coordinates
        self.textboxes = [QLabel(self) for _ in range(6)]
        # Texbox with calculation formula
        self.label_stereoshift = QLabel(
            "Stereo shift (shift_p/shift_f = depth_p/depth_f)"
        )
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
        btn_calculate.clicked.connect(self._on_click_calculate)
        btn_save = QPushButton("Save to table")
        btn_save.clicked.connect(
            self._on_click_save_to_table
        )  # TODO add this back in
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.buttonBox.clicked.connect(self.cancel)  # TODO add this back in
        # Layout
        # surely there's a nicer way of doing this grid layout stuff.
        self.setLayout(QGridLayout())
        self.layout().addWidget(lbl_ref_plane, 0, 0, 1, 2)
        self.layout().addWidget(lbl_fiducial_coords, 1, 0, 1, 2)
        self.layout().addWidget(self.cmb_set_ref_plane, 0, 2)
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
        # check how original code works and make sure I've copied the correct functionality.
        if self.cmb_set_ref_plane.currentIndex == 0:
            self.label_stereoshift.setText(
                "Stereo shift (shift_p/shift_f = depth_p/depth_f)"
            )
        elif self.cmb_set_ref_plane.currentIndex == 1:
            self.label_stereoshift.setText(
                "Stereo shift (shift_p/shift_f = 1 - depth_p/depth_f)"
            )

        self.layer_points.refresh()

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
            symbol="x",
        )

        return layer_points

    def _on_click_calculate(self) -> None:
        """Caculate the stereoshift and populate the results table."""

        # Add points in the coords to corresponding text box
        for i in range(len(self.points)):
            self.points[i].xy = self.layer_points.data[i]
            # There may be a better way of doing this by assigning point attributes.
            # I can see this approach going wrong.
            # Take a look at the napari example nD points with features
            self.textboxes[i].setText(str(self._fiducial_views[i].xy))
        self.textboxes[i].setText(str(self._fiducial_views[i].xy))
        # TODO clarify whether we still want the reference offset to be displayed to the user.
        ref_plane_index = self.cmb_set_ref_plane.currentIndex * 2
        # index =0 if front, 2 if rear
        fiducial_plane__index = 2 - ref_plane_index
        # whatever plane is not the reference plane, use the opposite plane.
        # The index of the points plane is always 1.
        # This could also be achieved in a more traditional/clearer way
        # (ie one that doesn't need a comment to be obvious) using an if/switch statement
        # But this keeps it a little more concise and is similar to the original code's use
        # of + and % to get the correct data index.
        # Would appreciate feedback on which style is preferred.
        self.shift_fiducial = corrected_length(
            self.points[fiducial_plane__index], self.points[ref_plane_index]
        )
        self.shift_point = corrected_length(
            self.points[1], self.points[ref_plane_index]
        )
        # See comments in pull request.
        self.point_stereoshift = self.shift_fiducial / self.shift_point
        # This is called ratio in the GUI, should the front or backend be changed here?
        # This next line is another example where the calculation is being done in
        # calculate.py but results in duplicated function calls.
        # I'll leave it as is for now, but it's another small thing to consider.
        # TODO: Regardless of how we decide to refactor, could do
        # with rewriting that function to take the list of points instead.
        self.point_depth = depth(
            self.points[fiducial_plane__index][0],
            self.points[fiducial_plane__index][1],
            self.points[1][0],
            self.points[1][1],
        )
        self.spoints = self.cal_layer.data[1:]
        # TODO this will need to be updated once magnification etc is added.

        # Update the results table
        self.lbl_fiducial_shift.setText(str(self.shift_fiducial))
        self.lbl_point_shift.setText(str(self.shift_point))
        self.lbl_stereoshift_ratio.setText(str(self.point_stereoshift))
        self.lbl_point_depth.setText(str(self.point_depth))

    def _on_click_save_to_table(self) -> None:
        """When 'Save to table' button is clicked, propagate stereoshift and depth to main table"""
        # Propagate to particle
        selected_row = self.parent._get_selected_row()
        self.parent.data[selected_row].spoints = self.spoints
        self.parent.data[selected_row].shift_fiducial = self.shift_fiducial
        self.parent.data[selected_row].shift_point = self.shift_point
        self.parent.data[selected_row].stereoshift = self.point_stereoshift
        self.parent.data[selected_row].depth_cm = self.point_depth

        # Propagate to parent table
        for i in range(2):
            self.parent.table.setItem(
                selected_row,
                self.parent._get_table_column_index("sf" + str(i + 1)),
                QTableWidgetItem(str(self.spoints[i])),
            )
            self.parent.table.setItem(
                selected_row,
                self.parent._get_table_column_index("sp" + str(i + 1)),
                QTableWidgetItem(str(self.spoints[i + 2])),
            )
        self.parent.table.setItem(
            selected_row,
            self.parent._get_table_column_index("shift_fiducial"),
            QTableWidgetItem(str(self.shift_fiducial)),
        )
        self.parent.table.setItem(
            selected_row,
            self.parent._get_table_column_index("shift_point"),
            QTableWidgetItem(str(self.shift_point)),
        )
        self.parent.table.setItem(
            selected_row,
            self.parent._get_table_column_index("stereoshift"),
            QTableWidgetItem(str(self.point_stereoshift)),
        )
        self.parent.table.setItem(
            selected_row,
            self.parent._get_table_column_index("depth_cm"),
            QTableWidgetItem(str(self.point_depth)),
        )

    def cancel(self) -> None:
        """On cancel remove the points_Stereoshift layer"""
        # TODO: this is a problem, the layer still exists... not sure how to remove it
        # TODO: Rework this with the new layer handling.
        self.parent.viewer.layers.select_previous()
        self.parent.viewer.layers.remove(self.cal_layer)
        return super().accept()


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

fiducial views is then a list of Fiducial and point objects, where 1, 2 -> CHANGE: Now just called points to avoid confusion since it contains both.
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
- For now, implement selecting first two points for stereoshift calculation, then implement the rest of the points.
- Tbh the coordinate readouts can be got rid of as well since they're arbitrary anyways
- Maybe replace this with a table once i get it working...

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


NAMES:
cal_layer -> points_layer
fiducial_views -> points

"""
