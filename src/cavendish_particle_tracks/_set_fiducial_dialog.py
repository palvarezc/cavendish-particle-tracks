import numpy as np
from napari.layers import Points, Shapes
from napari import Viewer
from qtpy.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ._analysis import FIDUCIAL_BACK, FIDUCIAL_FRONT, Fiducial
from ._calculate import (
    corrected_shift,
    depth,
    magnification,
)


class Set_Fiducial_Dialog(QDialog):
    def __init__(self, parent: Viewer):
        # Call parent constructor
        super().__init__(parent)
        self.parent = parent

        # ignoring ruff style here to make the array clearer
        # fmt:off
        self.points = [
            [Fiducial("Point View 1"), Fiducial("Point View 2")],
        ]
        self.fiducials = [
            [Fiducial("Front Fiducial 1 View 1"), Fiducial("Front Fiducial 1 View 2")],
            [Fiducial("Front Fiducial 2 View 1")],
            [Fiducial("Back Fiducial 1 View 1"),Fiducial("Back Fiducial 1 View 2")],
            [Fiducial("Back Fiducial 2 View 1")]
        ]
        # fmt:on
        self.shift_fiducial = 0.0
        self.shift_point = 0.0
        self.point_stereoshift = 0.0
        self.point_depth = -1.0
        self.spoints = []
        # endregion
        self.layer_fiducials: Points = self._setup_fiducial_layer()
        self.layer_points: Points = self._setup_points_layer()
        self._setup_ui()
        self.sync_layer_with_data()
        self.layer_shapes = self._setup_shapes_layer()
        self.parent.layers.selection.active = self.layer_fiducials

        @self.layer_points.events.data.connect
        def _on_change_layer_points(event):
            self.points[0][0].x, self.points[0][0].y = self.layer_points.data[
                0
            ]
            self.layer_shapes.data[0][0][0] = self.points[0][0].x
            self.layer_shapes.data[0][0][1] = self.points[0][0].y
            self.layer_shapes.refresh()
            # update for more points as needed

        @self.layer_fiducials.events.data.connect
        def _on_change_layer_points(event):
            for i in range(len(self.fiducials)):
                for j in range(len(self.fiducials[i])):
                    (self.fiducials[i][j].x, self.fiducials[i][j].y) = (
                        self.layer_fiducials.data[i * 2 + j]
                    )
            self.layer_shapes.data[0][0][0] = self.fiducials[0][0].x
            self.layer_shapes.data[0][0][1] = self.fiducials[0][0].y
            self.layer_shapes.refresh()

    def _setup_ui(self) -> None:
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
        lbl_front1 = QLabel("Front Fiducial 1")
        lbl_front1_view1 = QLabel("View 1")
        lbl_front1_view2 = QLabel("View 2")
        lbl_front2 = QLabel("Front Fiducial 2")
        lbl_front2_view1 = QLabel("View 1")
        lbl_back1 = QLabel("Rear Fiducial 1")
        lbl_back1_view1 = QLabel("View 1")
        lbl_back1_view2 = QLabel("View 2")
        lbl_back2 = QLabel("Rear Fiducial 2")
        lbl_back2_view1 = QLabel("View 1")
        lbl_point_coords = QLabel("Point coordinates")
        lbl_point_view1 = QLabel("View 1")
        lbl_point_view2 = QLabel("View 2")
        # Textboxes for the output of point coordinates
        self.fiducial_textboxes = [QLabel(self) for _ in range(6)]
        self.point_textboxes = [QLabel(self) for _ in range(2)]
        # Comboboxes for selecting which fiducial the point corresponds to
        self.cmb_front1 = self._setup_dropdown_fiducials_combobox()
        self.cmb_front2 = self._setup_dropdown_fiducials_combobox()
        self.cmb_back1 = self._setup_dropdown_fiducials_combobox(back=True)
        self.cmb_back2 = self._setup_dropdown_fiducials_combobox(back=True)
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
            self.fiducial_textboxes + self.results + self.point_textboxes
        ):  # possibly another way of implementing this without creaing an unnecessary list that isn't referenced again
            textbox.setMinimumWidth(50)
        # Add magnification results table
        # TODO again I'd like to change this once functionality complete
        self.table = QTableWidget(1, 2)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(["a", "b"])
        # Control Buttons
        btn_calculate = QPushButton("Calculate")
        btn_calculate.clicked.connect(self._on_click_calculate)
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.buttonBox.clicked.connect(self.cancel)
        self.buttonBox.accepted.connect(self._on_click_save_to_table)
        # Layout
        # surely there's a nicer way of doing this grid layout stuff.
        # there is: nested layouts are possible https://doc.qt.io/qtforpython-6/overviews/qtwidgets-tutorials-widgets-nestedlayouts-example.html
        # That said, is it really that much of an improvement?
        # actually yes it is
        # when you need to insert into grid style layouts
        # the problem is you now need to update all the points after it
        layout_outer = QVBoxLayout()

        layout_refplane = QHBoxLayout()
        layout_refplane.addWidget(lbl_ref_plane)
        layout_refplane.addWidget(self.cmb_set_ref_plane)
        layout_outer.addLayout(layout_refplane)

        layout_fiducials = QGridLayout(margin=10)
        layout_fiducials.addWidget(lbl_front1, 0, 0)
        layout_fiducials.addWidget(self.cmb_front1, 0, 1)
        layout_fiducials.addWidget(lbl_front1_view1, 0, 2)
        layout_fiducials.addWidget(self.fiducial_textboxes[0], 0, 3)
        layout_fiducials.addWidget(lbl_front1_view2, 0, 4)
        layout_fiducials.addWidget(self.fiducial_textboxes[1], 0, 5)

        layout_fiducials.addWidget(lbl_front2, 1, 0)
        layout_fiducials.addWidget(self.cmb_front2, 1, 1)
        layout_fiducials.addWidget(lbl_front2_view1, 1, 2)
        layout_fiducials.addWidget(self.fiducial_textboxes[2], 1, 3)

        layout_fiducials.addWidget(lbl_back1, 2, 0)
        layout_fiducials.addWidget(self.cmb_back1, 2, 1)
        layout_fiducials.addWidget(lbl_back1_view1, 2, 2)
        layout_fiducials.addWidget(self.fiducial_textboxes[3], 2, 3)
        layout_fiducials.addWidget(lbl_back1_view2, 2, 4)
        layout_fiducials.addWidget(self.fiducial_textboxes[4], 2, 5)

        layout_fiducials.addWidget(lbl_back2, 3, 0)
        layout_fiducials.addWidget(self.cmb_back2, 3, 1)
        layout_fiducials.addWidget(lbl_back2_view1, 3, 2)
        layout_fiducials.addWidget(self.fiducial_textboxes[5], 3, 3)

        layout_fiducials.addWidget(lbl_point_coords, 4, 0)
        layout_fiducials.addWidget(lbl_point_view1, 4, 2)
        layout_fiducials.addWidget(self.point_textboxes[0], 4, 3)
        layout_fiducials.addWidget(lbl_point_view2, 4, 4)
        layout_fiducials.addWidget(self.point_textboxes[1], 4, 5)
        layout_outer.addLayout(layout_fiducials)

        layout_stereoshift = QHBoxLayout()
        layout_stereoshift.addWidget(self.label_stereoshift)
        layout_stereoshift.addWidget(btn_calculate)
        layout_outer.addLayout(layout_stereoshift)

        layout_results = QGridLayout(margin=10)
        layout_results.addWidget(QLabel("Fiducial shift"), 0, 0)
        layout_results.addWidget(self.lbl_fiducial_shift, 0, 1)
        layout_results.addWidget(QLabel("Point shift"), 1, 0)
        layout_results.addWidget(self.lbl_point_shift, 1, 1)
        layout_results.addWidget(QLabel("Ratio"), 2, 0)
        layout_results.addWidget(self.lbl_stereoshift_ratio, 2, 1)
        layout_results.addWidget(QLabel("Point depth (cm)"), 3, 0)
        layout_results.addWidget(self.lbl_point_depth, 3, 1)
        layout_outer.addLayout(layout_results)

        layout_outer.addWidget(self.table)
        layout_outer.addWidget(self.buttonBox)

        self.setLayout(layout_outer)

    def _setup_dropdown_fiducials_combobox(self, back=False):
        """Sets up a drop-down list of fiducials for the `back` or front (`back=False`)."""
        combobox = QComboBox()
        if back:
            combobox.addItems(FIDUCIAL_BACK.keys())
        else:
            combobox.addItems(FIDUCIAL_FRONT.keys())
        combobox.currentIndexChanged.connect(self._on_click_fiducial)
        return combobox

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

        self.layer_fiducials.refresh()
        self.layer_points.refresh()

    # def _on_change_cmb_fiducial etc etc
    # add the label to the point in the view
    # replaces the old on_click_add button

    def _setup_fiducial_layer(self) -> Points:
        points = np.array(  # TODO points is a duplicate of the fiducial array, why bother keeping both? can definitely be cleaned up
            [
                [100, 100],  # Front Fiducial 1 View 1
                [101, 400],  # Front Fiducial 1 View 2
                [200, 100],  # Front Fiducial 2 View 1
                [200, 102],  # Front Fiducial 2 View 2
                [299, 401],  # Back Fiducial 1 View 1
                [400, 402],  # Back Fiducial 1 View 2
                [500, 400],  # Back Fiducial 2 View 1
                [500, 402],  # BackFiducial 2 View 2
                # then expand this to include the magnification points and redo the array
            ]
        )
        # TODO fix all this here and check how it's actually working
        # TODO implment the layer attributes stuff see if i can integrate it with the existing napari stuff
        fiducial_labels = []
        for i in self.fiducials:
            # What I've done here is a big no-no, as the list of fiducials here
            # carries the same name as the points used to instantiate the layer.
            # (ie. self.points = fiducials, points = the array above as the scope is limited to this function)
            # This is kinda why I want to change this, but leaving it as functional but odd till
            # we figure out how to get the points to instantiate in the middle of the viewport or
            # decide otherwise.
            for j in i:
                fiducial_labels += [
                    j.name
                ]  # TODO check this is actually working, now that i see it again it probably doesn't work
                # how i intended it to.

        colors = [
            "green",
            "red",
            "green",
            "red",
            "green",
            "red",
            "green",
            "red",
        ]

        symbols = ["x", "x", "cross", "cross", "disc", "disc"]  # TODO fix

        text = {
            "string": fiducial_labels,
            "size": 20,
            "color": colors,
            "translation": np.array([-30, 0]),
        }

        layer_fiducials = self.parent.viewer.add_points(
            points,
            name="Fiducials",
            text=text,
            size=20,
            edge_width=7,
            edge_width_is_relative=False,
            edge_color=colors,
            face_color=colors,
            # symbol=symbols,
        )
        return layer_fiducials

    # TODO since this is mostly the same as setup fiducial layer, this code can be cleaned up as a parent and two child methods
    def _setup_points_layer(self) -> Points:
        points = np.array(  # TODO points is a duplicate of the fiducial array, why bother keeping both?
            [[600, 600], [600, 700]]  # Point 1 View 1  # point 1 view 2
        )

        # TODO fix all this here and check how it's actually working
        # TODO implment the layer attributes stuff see if i can integrate it with the existing napari stuff
        point_labels = []
        for i in self.points:
            # What I've done here is a big no-no, as the list of fiducials here
            # carries the same name as the points used to instantiate the layer.
            # (ie. self.points = fiducials, points = the array above as the scope is limited to this function)
            # This is kinda why I want to change this, but leaving it as functional but odd till
            # we figure out how to get the points to instantiate in the middle of the viewport or
            # decide otherwise.
            for j in i:
                point_labels += [j.name]
        colors = [
            "yellow",
            "yellow",
        ]
        text = {
            "string": point_labels,
            "size": 20,
            "color": colors,
            "translation": np.array([-30, 0]),
        }
        layer_fiducials = self.parent.viewer.add_points(
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
        return layer_fiducials

    # there may be another way of doing this that is less computationally intensive, but I've found that this works.
    # the shapes layer is used to connect together points between views
    # a vector layer could also be used, but it uses n-dim projections to assign the vectors
    # whereas shapes just uses start,end point, which is a lot easier to code as i can just pull the coords
    # from the points layer on updates
    def _setup_shapes_layer(self) -> Shapes:
        self.shapes = []
        for fiducial in self.fiducials[::2]:
            # is there a better way to write this to combine the two arrays?
            # this one needs to skip every 2nd element since those don't have an item in the 2nd view
            self.shapes.append(
                np.array(
                    [
                        [fiducial[0].x, fiducial[0].y],
                        [fiducial[1].x, fiducial[1].y],
                    ]
                )
            )  # on update should copy data to point then update, ideally we should merge the two but hey...
            # that's for the next patch...
        for point in self.points:
            self.shapes.append(
                np.array([[point[0].x, point[0].y], [point[1].x, point[1].y]])
            )
        layer_shapes = self.parent.viewer.add_shapes(
            self.shapes,
            shape_type="line",
            edge_color="yellow",
            edge_width=5,
        )
        layer_shapes.editable = False
        return layer_shapes

    def _on_click_calculate(self) -> None:
        """Calculate the stereoshift and populate the results table."""
        # TODO need to add checks that the user hasn't deleted points or otherwise
        # Add points in the coords to corresponding text box
        self.sync_layer_with_data()
        # There may be a better way of doing this by assigning point attributes.
        # I can see this approach going wrong.
        # Take a look at the napari example nD points with features
        # TODO clarify whether we still want the reference offset to be displayed to the user.
        ref_plane_index = self.cmb_set_ref_plane.currentIndex() * 2
        # index =0 if front, 2 if rear
        fiducial_plane__index = 2 - ref_plane_index
        # = 2 if front, 0 if rear
        # This could also be achieved in a more traditional/clearer way
        # (ie one that doesn't need a comment to be obvious) using an if/switch statement
        # But this keeps it a little more concise and is similar to the original code's use
        # of + and % to get the correct data index.
        # Would appreciate feedback on which style is preferred.
        self.shift_fiducial = corrected_shift(
            self.fiducials[fiducial_plane__index],
            self.fiducials[ref_plane_index],
        )
        self.shift_point = corrected_shift(
            self.points[0], self.fiducials[ref_plane_index]
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
            self.fiducials[fiducial_plane__index][0],
            self.fiducials[fiducial_plane__index][1],
            self.points[0][0],
            self.points[0][1],
        )
        self.spoints = self.layer_fiducials.data[2:]
        # TODO this will need to be updated once magnification etc is added.
        # also needs a better name and for the function to be more clear
        # also worth noting that this is used when saving to table.
        # why not use the existing points list for this to avoid duplicating it?
        # sure, the access is a little more complicated but it keeps the number
        # of variables down.

        # Update the results table
        self.lbl_fiducial_shift.setText(str(self.shift_fiducial))
        self.lbl_point_shift.setText(str(self.shift_point))
        self.lbl_stereoshift_ratio.setText(str(self.point_stereoshift))
        self.lbl_point_depth.setText(str(self.point_depth))

        # region Magnification ##################################
        self.fiducials[0][0].name = self.cmb_front1.currentText()
        self.fiducials[1][0].name = self.cmb_front2.currentText()
        self.fiducials[2][0].name = self.cmb_back1.currentText()
        self.fiducials[3][0].name = self.cmb_back2.currentText()
        self.a, self.b = magnification(
            self.fiducials[0][0],  # F1 View 1
            self.fiducials[1][0],  # F2 View 1
            self.fiducials[2][0],  # B1 View 1
            self.fiducials[3][0],  # B2 View 1
        )
        # Update the magnification table
        self.table.setItem(0, 0, QTableWidgetItem(str(self.a)))
        self.table.setItem(0, 1, QTableWidgetItem(str(self.b)))

    def sync_layer_with_data(self):
        for i in range(len(self.fiducials)):
            for j in range(len(self.fiducials[i])):
                (self.fiducials[i][j].x, self.fiducials[i][j].y) = (
                    self.layer_fiducials.data[i * 2 + j]
                )
                self.fiducial_textboxes[i].setText(
                    str(self.fiducials[i][j].xy)
                )
        for i in range(len(self.points)):
            for j in range(len(self.points[i])):
                (self.points[i][j].x, self.points[i][j].y) = (
                    self.layer_points.data[i * 2 + j]
                )
                self.point_textboxes[i].setText(str(self.points[i][j].xy))

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
        self.parent.viewer.layers.remove(self.layer_fiducials)
        self.parent.viewer.layers.remove(self.layer_points)
        return super().accept()

    def _on_click_fiducial(self) -> None:
        print("This is a skeleton function")


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
point_stereoshift = ratio between point shifts
point_depth = depth of the point
spoints? oh it's the points for the stereoshift.
#TODO get rid of spoints or find some other way of exporting to the table once the data structure has been finalised.
for now, spoints doesn't work.

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
- Calculation structure was redundant.z

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

TODO Writeup changes made to magnification for PR

Comment copied from on_click_fiducial
# This was intended to be linked to the combobox
        # Would be cool if we could wait for a click here and add that as the selected fiducial, but no clue how to do that yet
        # layers  = [
        #     layer for layer in self.parent.viewer.layers if layer.name == "Points_Calibration"
        # ]
        # layer = layers[0]
        # @layer.mouse_drag_callbacks.append
        # def callback(layer, event):  # (0,0) is the center of the upper left pixel
        #     print(self.parent.viewer.cursor.position)

_______________________
Magnification previous implementation pseudocode:

When "add" is clicked for a fiducial -> add coords(fiducial index) is called
Add_cords:
-> retrieves point from layer
-> enforces only one point selected
-> updates UI
-> returns coords

When calculate clicked
-> checks fiducials have been added, if not alerts the user
-> calls magnification to calculate
    -> Magnification(4 fiducials)
    -> calcs mag from known point locations
    -> returns a,b
-> Updates UI

When accept clicked
-> call widget "propogate magnification"
-> remove layer using select previous and remove by ref. # why do we need both?
-> cal.setEnabled = true (sets up magnification to actually work)
-> update button text on parent widget
-> return super.accept() # what does this do?

When cancel clicked
-> remove layer
-> call parent "reject" # what does this do?
________________________
New approach pseudo
INIT:
- Create fiducial array
- initialise stereoshift calculation variables.
- call setup points layer
- call UI setup

SETUP POINTS LAYER:
- Initiliase arbitrary set of points


"""
