from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._main_widget import ParticleTracksWidget

import numpy as np
from napari.layers import Layer, Points
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
)

from ._analysis import Fiducial
from ._calculate import corrected_shift, depth, stereoshift

FRONT = 0
BACK = 1


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

    @property
    def reference_plane(self):
        return self.cmb_set_ref_plane.currentIndex

    def __init__(self, parent: "ParticleTracksWidget"):
        super().__init__(parent)
        self.shift_fiducial: float = 0.0
        self.shift_point: float = 0.0
        self.point_stereoshift: float = 0.0
        self.point_depth: float = -1.0
        self.spoints = []

        self.parent: "ParticleTracksWidget" = parent  # noqa: UP037
        self.parent.stereoshift_isopen = True
        self.setWindowTitle("Stereoshift")

        # First, check if the layers already exist, if not, create them.
        self.layer_fiducials: Points = self._create_retrieve_layer(
            "Stereo_Fiducials",
            self.camera_center[0],
            self.camera_center[1],
            self.zoom_level,
            self.current_event,
        )
        self.layer_points: Points = self._create_retrieve_layer(
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
        # self.parent.viewer.dims.events.connect(self._on_event_changed)

    def _setup_fiducial_layer(
        self, origin_x, origin_y, zoom_level, current_event
    ) -> Points:
        # fmt:off
        points = [      # View 1                                                # View 2
            [origin_x, origin_y, current_event],                [origin_x + 100/zoom_level, origin_y, current_event],                # Front
            [origin_x, origin_y-100/zoom_level, current_event], [origin_x + 100/zoom_level, origin_y-100/zoom_level, current_event],  # Rear
        ]
        fiducial_labels = ["Front View 1",  "Front View 2",
                           "Rear View 2",   "Rear View 2"]
        colors = ["green", "red",
                  "green", "red",]
        symbols = ["x", "x",
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
        self, origin_x, origin_y, zoom_level, current_event
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

        # Control Buttons
        btn_calculate = QPushButton("Calculate")
        btn_calculate.clicked.connect(self._on_click_calculate)
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.accepted.connect(self.accept)
        # Layout
        layout_outer = QVBoxLayout()
        layout_refplane = QHBoxLayout()
        layout_refplane.addWidget(lbl_ref_plane)
        layout_refplane.addWidget(self.cmb_set_ref_plane)
        layout_outer.addLayout(layout_refplane)
        layout_fiducials = QGridLayout(margin=10)
        layout_fiducials.addWidget(lbl_front1, 0, 0)
        layout_fiducials.addWidget(lbl_front1_view1, 0, 2)
        layout_fiducials.addWidget(self.fiducial_textboxes[0], 0, 3)
        layout_fiducials.addWidget(lbl_front1_view2, 0, 4)
        layout_fiducials.addWidget(self.fiducial_textboxes[1], 0, 5)
        layout_fiducials.addWidget(lbl_front2, 1, 0)
        layout_fiducials.addWidget(lbl_front2_view1, 1, 2)
        layout_fiducials.addWidget(self.fiducial_textboxes[2], 1, 3)
        layout_fiducials.addWidget(lbl_back1, 2, 0)
        layout_fiducials.addWidget(lbl_back1_view1, 2, 2)
        layout_fiducials.addWidget(self.fiducial_textboxes[3], 2, 3)
        layout_fiducials.addWidget(lbl_back1_view2, 2, 4)
        layout_fiducials.addWidget(self.fiducial_textboxes[4], 2, 5)
        layout_fiducials.addWidget(lbl_back2, 3, 0)
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
        layout_outer.addWidget(self.buttonBox)
        self.setLayout(layout_outer)

    def _create_retrieve_layer(
        self, layer_name: str, origin_x, origin_y, zoom_level, current_event
    ) -> Layer:
        if layer_name in self.parent.viewer.layers:
            return self.parent.viewer.layers[layer_name]
        if layer_name == "Stereo_Fiducials":
            return self._setup_fiducial_layer(
                origin_x, origin_y, zoom_level, current_event
            )
        elif layer_name == "Stereo_Points":
            return self._setup_points_layer(
                origin_x, origin_y, zoom_level, current_event
            )
        # elif layer_name == "Stereo_shift_lines":
        #    return self._setup_shapes_layer()
        else:
            raise Exception(
                "Unexpected layer name encountered. Something has really went wrong."
            )

    def _on_click_calculate(self) -> None:
        """Calculate the stereoshift and populate the results table."""
        # I could do a list (front fiducials = [front 1, front 2]) here if desired.
        # I don't see the point, as it seems clear enough to me.
        # The way I've laid this out, there are cleverer ways to do this.
        # But after trying a load of different ways, this is the most readable and maintainable.
        front_fiducials = [
            self._retrieve_fiducial(0, FRONT, 1),
            self._retrieve_fiducial(0, FRONT, 2),
        ]
        rear_fiducials = [
            self._retrieve_fiducial(0, BACK, 1),
            self._retrieve_fiducial(0, BACK, 2),
        ]
        points = [self._retrieve_points(0, 1), self._retrieve_points(0, 2)]

        # We wish to swap whether the front or back points are used for the calculation
        # depending on the user's choice.
        if self.reference_plane == FRONT:
            shifting_fiducials = front_fiducials
            static_reference_fiducials = rear_fiducials
        else:
            shifting_fiducials = rear_fiducials
            static_reference_fiducials = front_fiducials

        self.shift_fiducial = corrected_shift(
            shifting_fiducials, static_reference_fiducials
        )
        self.shift_point = corrected_shift(points, static_reference_fiducials)
        # TODO this is called ratio in the GUI, should I change its name here or there?
        self.point_stereoshift = stereoshift(
            self.shift_fiducial, self.shift_point
        )
        self.point_depth = depth(
            self.point_stereoshift, bool(self.reference_plane)
        )
        # TODO what what spoints doing again? check this is correct
        self.spoints = self.layer_fiducials.data[2:]
        # Update the results table
        self.lbl_fiducial_shift.setText(str(self.shift_fiducial))
        self.lbl_point_shift.setText(str(self.shift_point))
        self.lbl_stereoshift_ratio.setText(str(self.point_stereoshift))
        self.lbl_point_depth.setText(str(self.point_depth))
        # endregion #############################################

    def _on_change_cmb_set_ref_plane(self) -> None:
        if self.cmb_set_ref_plane.currentIndex == 0:
            self.label_stereoshift.setText(
                "Stereo shift (shift_p/shift_f = depth_p/depth_f)"
            )
        else:
            self.label_stereoshift.setText(
                "Stereo shift (shift_p/shift_f = 1 - depth_p/depth_f)"
            )

    def _retrieve_fiducial(self, event, depth_index, view) -> Fiducial:
        """Access a fiducial by:
        [ (event=),  (front=0,back=1), (view=1,2)]"""
        # this is written on the assumption the layers are deleted after every use.
        # this will be updated to work for many layers in the next PR
        # filter down a subset of the points using the above criteria.
        # in this temp mode, we already know the order of the data in the layer so can access directly
        # will need to filter view by the text, as viewpoints persist across multiple view layers.
        # remember that the layer is set up such that:
        #            points = [      # View 1                                                # View 2
        #      0  [origin_x, origin_y, current_event],                 1  [origin_x + 100/zoom_level, origin_y, current_event],                # Front
        #      2  [origin_x, origin_y-200/zoom_level, current_event],  3  [origin_x + 100/zoom_level, origin_y-200/zoom_level, current_event],  # Rear
        data = self.layer_fiducials.data[depth_index * 2 + (view - 1)]
        # Layer data has a different coordinate order than world data.
        # so even though the axis_labels are event, view, y, x
        # these remain as they were intialised.
        # so [x,y,event] is the correct order, as above.
        return Fiducial("", data[0], data[1])
        # depth,view
        # case (0,1) -> front, view 1 -> 0
        # case (0,2) -> front, view 2 -> 1
        # case (1,1) -> ref, view 1 -> 2
        # case (1,2) -> ref, view 2 -> 3

    def _retrieve_points(self, event, view) -> Fiducial:
        """Access a point by: [ (event=), (view=1,2)]"""
        name = f"Point View {view}"
        return Fiducial(
            name,
            self.layer_points.data[view][0],
            self.layer_points.data[view][1],
        )

    def _activate_stereoshift_layers(self):
        """Show the stereoshift layers and move it to the top."""
        self.layer_fiducials.visible = True
        self.layer_points.visible = True
        # move layers to the top
        self.parent.viewer.layers.move(
            self.parent.viewer.layers.index(self.layer_points),
            len(self.parent.viewer.layers),
        )
        self.parent.viewer.layers.move(
            self.parent.viewer.layers.index(self.layer_fiducials),
            len(self.parent.viewer.layers),
        )
        self.parent.viewer.layers.selection.active = self.layer_fiducials

    def _deactivate_stereoshift_layers(self):
        """Hide the stereoshift layers and move it to the bottom"""
        self.parent.viewer.layers.remove[self.layer_fiducials.name]
        self.parent.viewer.layers.remove[self.layer_points.name]
        # TODO update this once ability to handle multiple measurements is added.
        # self.layer_fiducials.visible = False
        # self.layer_points.visible = False
        # self.parent.viewer.layers.move(
        #    self.parent.viewer.layers.index(self.layer_points), 0
        # )
        # self.parent.viewer.layers.move(
        #    self.parent.viewer.layers.index(self.layer_fiducials), 0
        # )

    def accept(self) -> None:
        """When 'Save to table' button is clicked, save the data and close the stereoshift widget."""
        self._save_to_table()
        self._deactivate_stereoshift_layers()
        self.parent.stereoshift_isopen = False
        return super().accept()

    def _save_to_table(self) -> None:
        """Saves data to the plugin table."""
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

    def reject(self) -> None:
        """On cancel remove the points_Stereoshift layer"""
        # TODO: this is a problem, the layer still exists... not sure how to remove it
        # TODO: Rework this with the new layer handling.
        self._deactivate_stereoshift_layers()
        self.parent.stereoshift_isopen = False
        return super().reject()

    # def _on_change_cmb_fiducial etc etc
    # add the label to the point in the view
    # replaces the old on_click_add button

    # there may be another way of doing this that is less computationally intensive, but I've found that this works.
    # the shapes layer is used to connect together points between views
    # a vector layer could also be used, but it uses n-dim projections to assign the vectors
    # whereas shapes just uses start,end point, which is a lot easier to code as i can just pull the coords
    # from the points layer on updates

    # region temp
    #    def _on_event_changed(self, event) -> None:
    #        # this is temporary and will be refactored.
    #        # TODO add check for whether there are already points in the layer.
    #        # this might seem a very weird way of doing this, since i could just run a for loop above, but this means it's easy to setup
    #        # the ability for fiducials to copy from one layer to the next.
    #        self.layer_fiducials: Points
    #        layer_created = False
    #        for point in self.layer_fiducials.data:
    #            if point[3] == self.current_event:
    #                layer_created = True
    #                break
    #        if layer_created:
    #            return
    #        origin_x = self.camera_center[0]
    #        origin_y = self.camera_center[1]
    #        current_event = self.current_event
    #        zoom_level = self.zoom_level
    #        # fmt:off
    #        points = [      # View 1                                                # View 2
    #            [origin_x, origin_y, current_event],                [origin_x + 100/zoom_level, origin_y, current_event],                # Front Fiducial
    #            [origin_x, origin_y+100/zoom_level, current_event], [origin_x + 100/zoom_level, origin_y+100/zoom_level, current_event]  # Rear Fiducial
    #        ]
    #        fiducial_labels = ["Front1", "Front2", "Rear1", "Rear2"]
    #        # fmt:on
    #        colors = ["green", "red", "green", "red"]
    #        symbols = ["x", "x", "cross", "cross"]
    #        text = {
    #            "string": fiducial_labels,
    #            "size": 20,
    #            "color": colors,
    #            "translation": np.array([-30, 0]),
    #        }
    #        self.layer_fiducials.add(
    #            points,
    #            text=text,
    #            size=20,
    #            border_width=7,
    #            border_width_is_relative=False,
    #            border_color=colors,
    #            face_color=colors,
    #            symbol=symbols,
    #        )
    # endregion
