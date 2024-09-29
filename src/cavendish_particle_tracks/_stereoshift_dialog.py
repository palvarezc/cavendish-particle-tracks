import copy
from typing import TYPE_CHECKING

import numpy as np
from napari.utils.notifications import show_error
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
)

from ._calculate import depth, length, stereoshift
from .analysis import Fiducial, StereoshiftInfo

if TYPE_CHECKING:
    from ._main_widget import ParticleTracksWidget


class StereoshiftDialog(QDialog):
    def __init__(self, parent: "ParticleTracksWidget"):
        super().__init__(parent)

        self.parent = parent

        self.setWindowTitle("Stereoshift")

        FIDUCIAL_VIEWS = [
            "Back fiducial view1",
            "Back fiducial view2",
            "Point view1",
            "Point view2",
        ]
        self._fiducial_views = [
            Fiducial(view_name) for view_name in FIDUCIAL_VIEWS
        ]

        # drop-down lists of vertex
        self.vertex_combobox = QComboBox()
        self.vertex_combobox.addItem("Origin vertex")
        self.vertex_combobox.addItem("Decay vertex")
        self.vertex_combobox.currentIndexChanged.connect(self._on_click_vertex)

        # drop-down lists of fiducials
        self.cbf1 = QComboBox()
        self.cbf1.addItem("Front / Back")
        self.cbf1.addItem("Back / Front")
        self.cbf1.currentIndexChanged.connect(self._on_click_fiducial)

        # text boxes for points
        self.textboxes = [QLabel(self) for _ in range(4)]

        # text boxes for results
        self.tshift_fiducial = QLabel(self)
        self.tshift_point = QLabel(self)
        self.tstereoshift = QLabel(self)
        self.tdepth = QLabel(self)

        self.results = [
            self.tshift_fiducial,
            self.tshift_point,
            self.tstereoshift,
            self.tdepth,
        ]
        for textbox in self.textboxes + self.results:
            textbox.setMinimumWidth(200)

        bss = QPushButton("Calculate")
        bss.clicked.connect(self._on_click_calculate)

        bap = QPushButton("Save to table")
        bap.clicked.connect(self._on_click_save_to_table)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.buttonBox.clicked.connect(self.reject)

        lviewf1 = QLabel("View 1")
        lviewf2 = QLabel("View 2")
        lviewb1 = QLabel("View 1")
        lviewb2 = QLabel("View 2")

        self.label_stereoshift = QLabel(
            "Stereo shift (shift_p/shift_f = depth_p/depth_f)"
        )

        # layout
        self.setLayout(QGridLayout())
        self.layout().addWidget(QLabel("Select Vertex"), 0, 0, 1, 2)
        self.layout().addWidget(self.vertex_combobox, 0, 2)
        self.layout().addWidget(
            QLabel("Select Reference / Fiducial"), 1, 0, 1, 2
        )
        self.layout().addWidget(self.cbf1, 1, 2)
        self.layout().addWidget(QLabel("Fiducial coordinates"), 2, 0, 1, 2)
        for i, widget in enumerate(
            [lviewf1, self.textboxes[0], lviewf2, self.textboxes[1]]
        ):
            self.layout().addWidget(widget, i // 2 + 3, i % 2 + 1)
        self.layout().addWidget(QLabel("Point coordinates"), 5, 0, 1, 2)
        for i, widget in enumerate(
            [lviewb1, self.textboxes[2], lviewb2, self.textboxes[3]]
        ):
            self.layout().addWidget(widget, i // 2 + 6, i % 2 + 1)

        self.layout().addWidget(bss, 7, 0, 1, 3)

        self.layout().addWidget(
            self.label_stereoshift,
            9,
            0,
            1,
            3,
        )
        # self.layout().addWidget(self.table, 9, 0, 1, 3)
        self.layout().addWidget(QLabel("Fiducial shift"), 10, 1)
        self.layout().addWidget(self.tshift_fiducial, 10, 2)
        self.layout().addWidget(QLabel("Point shift"), 11, 1)
        self.layout().addWidget(self.tshift_point, 11, 2)
        self.layout().addWidget(QLabel("Ratio"), 12, 1)
        self.layout().addWidget(self.tstereoshift, 12, 2)
        self.layout().addWidget(QLabel("Point depth (cm)"), 13, 1)
        self.layout().addWidget(self.tdepth, 13, 2)
        self.layout().addWidget(bap, 14, 0, 1, 3)
        self.layout().addWidget(self.buttonBox, 15, 0, 1, 3)

        # Setup points layer
        self.cal_layer = self._setup_stereoshift_layer()

        # Stereoshift related parameters
        self.stereoshift_info = StereoshiftInfo()
        self.stereoshift_info.name = "origin_vertex"

    def _setup_stereoshift_layer(self):
        # retrieve current camera position
        origin_x = self.parent.camera_center[0]
        origin_y = self.parent.camera_center[1]
        zoom_factor = self.parent.viewer.camera.zoom
        # add the points
        points = np.array(
            [
                [
                    origin_x - 100 / zoom_factor,
                    origin_y - 200 / zoom_factor,
                ],
                [
                    origin_x + 100 / zoom_factor,
                    origin_y - 200 / zoom_factor,
                ],
                [origin_x - 100 / zoom_factor, origin_y],
                [origin_x + 100 / zoom_factor, origin_y],
                [
                    origin_x - 100 / zoom_factor,
                    origin_y + 200 / zoom_factor,
                ],
                [
                    origin_x + 100 / zoom_factor,
                    origin_y + 200 / zoom_factor,
                ],
            ]
        )

        labels = ["Reference (Front) view1", "Reference (Front) view2"]
        for item in self._fiducial_views:
            labels += [item.name]

        colors = ["green", "red", "green", "red", "green", "red"]
        symbols = ["diamond", "diamond", "cross", "cross", "disc", "disc"]

        text = {
            "string": labels,
            "size": 14,
            "color": colors,
            "translation": np.array([-30, 0]),
        }

        # create a points layer where the face_color is set by the good_point feature
        # and the edge_color is set via a color map (grayscale) on the confidence
        # feature.
        points_layer = self.parent.viewer.add_points(
            points,
            name="Points_Stereoshift",
            text=text,
            size=20,
            border_width=7,
            border_width_is_relative=False,
            border_color=colors,
            face_color=colors,
            symbol=symbols,
        )

        # set the edge_color mode to colormap
        # points_layer.edge_color_mode = 'colormap'

        return points_layer

    def f(self, i) -> Fiducial:
        if i not in [1, 2]:
            raise IndexError()
        return self._fiducial_views[i - 1]

    def b(self, i) -> Fiducial:
        if i not in [1, 2]:
            raise IndexError()
        return self._fiducial_views[i + 1]

    def _on_click_fiducial(self) -> None:
        """When fiducial is selected, update the name of the fiducial and the points text"""

        if self.cbf1.currentIndex() == 0:
            self.f(1).name = "Back fiducial view1"
            self.f(2).name = "Back fiducial view2"
            self.cal_layer.text.string.array[0] = "Reference (Front) view1"
            self.cal_layer.text.string.array[1] = "Reference (Front) view2"
            self.cal_layer.text.string.array[2] = self.f(1).name
            self.cal_layer.text.string.array[3] = self.f(2).name
            self.label_stereoshift.setText(
                "Stereo shift (shift_p/shift_f = depth_p/depth_f)"
            )

        if self.cbf1.currentIndex() == 1:
            self.f(1).name = "Front fiducial view1"
            self.f(2).name = "Front fiducial view2"
            self.cal_layer.text.string.array[0] = "Reference (Back) view1"
            self.cal_layer.text.string.array[1] = "Reference (Back) view2"
            self.cal_layer.text.string.array[2] = self.f(1).name
            self.cal_layer.text.string.array[3] = self.f(2).name
            self.label_stereoshift.setText(
                "Stereo shift (shift_p/shift_f = 1 - depth_p/depth_f)"
            )

        self.cal_layer.refresh()

    def _on_click_vertex(self) -> None:
        """When vertex is selected, update the name of the vertex"""
        if self.vertex_combobox.currentIndex() == 0:
            self.stereoshift_info.name = "origin_vertex"
        if self.vertex_combobox.currentIndex() == 1:
            self.stereoshift_info.name = "decay_vertex"

    def _on_click_calculate(self) -> None:
        """When 'Calculate' button is clicked, calculate stereoshift and populate table"""

        # Add points coords to corresponding text box
        for i in range(len(self._fiducial_views)):
            (
                self._fiducial_views[i].x,
                self._fiducial_views[i].y,
            ) = (
                self.cal_layer.data[i + 2] - self.cal_layer.data[i % 2]
            )
            self.textboxes[i].setText(str(self._fiducial_views[i].xy))

        # Calculate stereoshift and depth
        self.stereoshift_info.shift_fiducial = length(
            self.f(1).xy, self.f(2).xy
        )
        self.stereoshift_info.shift_point = length(self.b(1).xy, self.b(2).xy)
        self.stereoshift_info.stereoshift = stereoshift(
            *[view.xy for view in self._fiducial_views]
        )
        self.stereoshift_info.depth_cm = depth(
            self.f(1),
            self.f(2),
            self.b(1),
            self.b(2),
            reverse=self.cbf1.currentIndex(),
        )
        self.stereoshift_info.spoints = self.cal_layer.data[2:]

        # Populate the table
        self.tshift_fiducial.setText(str(self.stereoshift_info.shift_fiducial))
        self.tshift_point.setText(str(self.stereoshift_info.shift_point))
        self.tstereoshift.setText(str(self.stereoshift_info.stereoshift))
        self.tdepth.setText(str(self.stereoshift_info.depth_cm))

    def _on_click_save_to_table(self) -> None:
        """When 'Save to table' button is clicked, propagate stereoshift and depth to main table"""
        # Propagate to particle
        try:
            selected_row = self.parent._get_selected_row()
        except IndexError:
            show_error("There are no particles in the table.")
        else:
            # Figure out what vertex to calculate stereoshift for
            what_vertex = self.vertex_combobox.currentIndex()
            # Save the stereoshift info to the particle
            if what_vertex == 0:
                self.parent.data[
                    selected_row
                ].origin_vertex_stereoshift_info = copy.deepcopy(
                    self.stereoshift_info
                )
            else:
                self.parent.data[
                    selected_row
                ].decay_vertex_stereoshift_info = copy.deepcopy(
                    self.stereoshift_info
                )
            # Update the table
            self.parent.table.setItem(
                selected_row,
                self.parent._get_table_column_index(
                    self.stereoshift_info.name + "_stereoshift_info"
                ),
                QTableWidgetItem(str(self.stereoshift_info)),
            )
            self.parent.table.setItem(
                selected_row,
                self.parent._get_table_column_index(
                    self.stereoshift_info.name + "_depth_cm"
                ),
                QTableWidgetItem(str(self.stereoshift_info.depth_cm)),
            )

    def reject(self) -> None:
        """On cancel remove the points_Stereoshift layer"""
        self.parent._deactivate_calibration_layer(self.cal_layer)
        return super().reject()
