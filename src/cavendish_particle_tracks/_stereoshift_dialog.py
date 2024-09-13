from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._widget import ParticleTracksWidget

import numpy as np
from napari.layers import Layer, Points, Shapes
from napari.utils.notifications import show_error
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
from ._calculate import corrected_shift, depth, stereoshift


class StereoshiftDialog(QDialog):

    @property
    def camera_center(self):
        return self.parent.camera_center

    @property
    def zoom_level(self):
        return self.parent.viewer.camera.zoom

    @property
    def current_event(self):
        return self.parent.current_event

    def __init__(self, parent: "ParticleTracksWidget"):
        super().__init__(parent)
        self.shift_fiducial: float = 0.0
        self.shift_point: float = 0.0
        self.point_stereoshift: float = 0.0
        self.point_depth: float = -1.0
        self.spoints = []

        self.parent = parent
        self.setWindowTitle("Stereoshift")

        def _setup_fiducial_layer(
            origin_x, origin_y, zoom_level, current_event
        ) -> Points:
            # fmt:off
            points = [      # View 1                                                # View 2
                [origin_x, origin_y, current_event],                [origin_x + 100/zoom_level, origin_y, current_event],                # Front
                [origin_x, origin_y-100/zoom_level, current_event], [origin_x + 100/zoom_level, origin_y-100/zoom_level, current_event],  # Reference
                [origin_x, origin_y-200/zoom_level, current_event], [origin_x + 100/zoom_level, origin_y-200/zoom_level, current_event],  # Rear
            ]
            fiducial_labels = ["Front View 1",  "Front View 2",
                               "Reference View 1", "Reference View 2",
                               "Rear View 2",   "Rear View 2"]

            colors = ["green", "red",
                      "green", "red",
                      "green", "red",]
            symbols = ["x", "x",
                       "square", "square",
                       "cross", "cross"]
            # fmt:on
            text = {
                "string": fiducial_labels,
                "size": 20,
                "color": colors,
                "translation": np.array([-30, 0]),
            }
            layer_fiducials = self.parent.viewer.add_points(
                points,
                name="Stereo_Fiducials",
                text=text,
                size=20,
                border_width=7,
                border_width_is_relative=False,
                edge_color=colors,
                face_color=colors,
                symbol=symbols,
            )
            return layer_fiducials

        def _setup_points_layer(
            origin_x, origin_y, zoom_level, current_event
        ) -> Points:
            # TODO since this is mostly the same as setup fiducial layer, this code can be cleaned up as a parent and two child methods
            # TODO implment the layer attributes stuff see if i can integrate it with the existing napari stuff
            points = [
                [origin_x, origin_y - 100 / zoom_level, current_event],
                [
                    origin_x - 100 / zoom_level,
                    origin_y + 100 / zoom_level,
                    current_event,
                ],  # Rear Fiducial
            ]
            point_labels = ["Point View 1", "Point View 2"]
            # fmt:on
            colors = ["green", "red"]
            symbols = ["diamond", "diamond"]
            text = {
                "string": point_labels,
                "size": 20,
                "color": colors,
                "translation": np.array([-30, 0]),
            }
            layer_points = self.parent.viewer.add_points(
                points,
                name="Stereo_Points",
                text=text,
                size=20,
                border_width=7,
                border_width_is_relative=False,
                edge_color=colors,
                face_color=colors,
                symbol=symbols,
            )
            return layer_points

        def create_retrieve_layer(
            layer_name: str, origin_x, origin_y, zoom_level, current_event
        ) -> Layer:
            if layer_name in self.parent.viewer.layers:
                return self.parent.viewer.layers[layer_name]
            if layer_name == "Stereo_Fiducials":
                return _setup_fiducial_layer(
                    origin_x, origin_y, zoom_level, current_event
                )
            elif layer_name == "Stereo_Points":
                return _setup_points_layer(
                    origin_x, origin_y, zoom_level, current_event
                )
            # elif layer_name == "Stereo_shift_lines":
            #    return _setup_shapes_layer()
            else:
                raise Exception(
                    "Unexpected layer name encountered. Something has really went wrong."
                )

        # First, check if the layers already exist, if not, create them.
        self.layer_fiducials: Points = create_retrieve_layer(
            "Stereo_Fiducials",
            self.camera_center[0],
            self.camera_center[1],
            self.zoom_level,
            self.current_event,
        )
        self.layer_points: Points = create_retrieve_layer(
            "Stereo_Points",
            self.camera_center[0],
            self.camera_center[1],
            self.zoom_level,
            self.current_event,
        )

        # Setup the window UI
        self._setup_ui()

        # Force selection mode by default.
        self.parent.viewer.layers.selection.active = self.layer_fiducials
        self.layer_fiducials.mode = "select"
        self.layer_points.mode = "select"
        self.parent.viewer.dims.events.connect(self._on_event_changed)

    def _on_click_calculate(self) -> None:
        """Calculate the stereoshift and populate the results table."""
        f = self._retrieve_fiducial(0, 0, 1)
        # There may be a better way of doing this by assigning point attributes and accessing their labels.
        # TODO clarify whether we still want the reference offset to be displayed to the user.
        ref_plane_index = self.cmb_set_ref_plane.currentIndex()
        # index =0 if front, 1 if rear
        fiducial_plane__index = 1 - ref_plane_index
        # = 1 if front, 0 if rear
        # This could also be achieved in a more traditional/clearer way using an if/switch statement
        # Would appreciate some feedback on which style is preferred.
        # Previously, I had used Fiducial objects and passed these in to the corrected_shift function.
        # eg. self.shift_fiducial = corrected_shift(self.fiducials[fiducial_plane__index], self.fiducials[ref_plane_index])
        # this was when we had the 2D array of fiducial objects, and had to do a load of code to sync up napari's data
        # structure with ours.
        # I'm not really a fan of duplicating the data here, and would rather just use pointers to the right data
        # in napari, than have to create fiducial objects and pass them in.
        # but, feel free to suggest that I change it back.
        # I'm also not a fan of the way that these calculations get duplicated.
        # i.e depth can just use the previous results.
        # self.shift_reference
        self.shift_fiducial = corrected_shift(
            self.fiducials[fiducial_plane__index],
            self.fiducials[ref_plane_index],
        )
        self.shift_point = corrected_shift(
            self.points[0], self.fiducials[ref_plane_index]
        )
        # this is called ratio in the GUI, should I change its name here or there?
        self.point_stereoshift = stereoshift(
            self.shift_fiducial, self.shift_point
        )
        self.point_depth = depth(
            self.fiducials[fiducial_plane__index][0],
            self.fiducials[fiducial_plane__index][1],
            self.points[0][0],
            self.points[0][1],
        )
        self.spoints = self.layer_fiducials.data[2:]
        # Update the results table
        self.lbl_fiducial_shift.setText(str(self.shift_fiducial))
        self.lbl_point_shift.setText(str(self.shift_point))
        self.lbl_stereoshift_ratio.setText(str(self.point_stereoshift))
        self.lbl_point_depth.setText(str(self.point_depth))
        # endregion #############################################

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
        # TODO fix
        # combobox.currentIndexChanged.connect(self._on_click_fiducial)
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

    def _update_UI(self):
        for i in range(self.layer_fiducials.data):
            print("Test")
            # what will this look like in 4D...?

    def _set_new_event_fiducial_locations(self):
        i = 1
        # print("self.parent.viewer.cursor.events.position.connect")
        # maybe connect shapes to this instead....

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

    def _on_click_cancel(self) -> None:
        """On cancel remove the points_Stereoshift layer"""
        # TODO: this is a problem, the layer still exists... not sure how to remove it
        # TODO: Rework this with the new layer handling.
        self.parent.viewer.layers.select_previous()
        self.parent.viewer.layers.remove(self.layer_fiducials)
        self.parent.viewer.layers.remove(self.layer_points)
        return super().accept()

    def _on_event_changed(self, event) -> None:
        # this is temporary and will be refactored.
        # TODO add check for whether there are already points in the layer.
        # this might seem a very weird way of doing this, since i could just run a for loop above, but this means it's easy to setup
        # the ability for fiducials to copy from one layer to the next.
        self.layer_fiducials: Points
        layer_created = False
        for point in self.layer_fiducials.data:
            if point[3] == self.current_event:
                layer_created = True
                break
        if layer_created:
            return
        origin_x = self.camera_center[0]
        origin_y = self.camera_center[1]
        current_event = self.current_event
        zoom_level = self.zoom_level
        # fmt:off
        points = [      # View 1                                                # View 2
            [origin_x, origin_y, current_event],                [origin_x + 100/zoom_level, origin_y, current_event],                # Front Fiducial
            [origin_x, origin_y+100/zoom_level, current_event], [origin_x + 100/zoom_level, origin_y+100/zoom_level, current_event]  # Rear Fiducial
        ]
        fiducial_labels = ["Front1", "Front2", "Rear1", "Rear2"]
        # fmt:on
        colors = ["green", "red", "green", "red"]
        symbols = ["x", "x", "cross", "cross"]
        text = {
            "string": fiducial_labels,
            "size": 20,
            "color": colors,
            "translation": np.array([-30, 0]),
        }
        self.layer_fiducials.add(
            points,
            text=text,
            size=20,
            edge_width=7,
            edge_width_is_relative=False,
            edge_color=colors,
            face_color=colors,
            symbol=symbols,
        )

    def _retrieve_fiducial(self, event, depth_index, view):
        """Access a fiducial by:
        [ (event=),  (front=0,ref=1,back=2), (view=1,2)]"""
        # this is written on the assumption the layers are deleted after every use.
        # this will be updated to work for many layers in the next PR
        # filter down a subset of the points using the above criteria.
        # in this temp mode, we already know the order of the data in the layer so can access directly
        # will need to filter view by the text, as viewpoints persist across multiple view layers.
        # remember that the layer is set up such that:
        #            points = [      # View 1                                                # View 2
        #      0  [origin_x, origin_y, current_event],                 1  [origin_x + 100/zoom_level, origin_y, current_event],                # Front
        #      2  [origin_x, origin_y-100/zoom_level, current_event],  3  [origin_x + 100/zoom_level, origin_y-100/zoom_level, current_event],  # Reference
        #      4  [origin_x, origin_y-200/zoom_level, current_event],  5  [origin_x + 100/zoom_level, origin_y-200/zoom_level, current_event],  # Rear
        data = self.layer_fiducials.data[depth_index * 2 + (view - 1)]
        return Fiducial("", data[0], data[1])  # double check these are correct
        # depth,view
        # case (0,1) -> front, view 1 -> 0
        # case (0,2) -> front, view 2 -> 1
        # case (1,1) -> ref, view 1 -> 2
        # case (1,2) -> ref, view 2 -> 3
        # case (2,1) -> back, view 1 -> 4
        # case (2,2) -> back, view 2 -> 5

    # def _on_change_cmb_fiducial etc etc
    # add the label to the point in the view
    # replaces the old on_click_add button

    # there may be another way of doing this that is less computationally intensive, but I've found that this works.
    # the shapes layer is used to connect together points between views
    # a vector layer could also be used, but it uses n-dim projections to assign the vectors
    # whereas shapes just uses start,end point, which is a lot easier to code as i can just pull the coords
    # from the points layer on updates


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
