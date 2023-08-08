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

from cavendish_particle_tracks._analysis import (
    Fiducial,
)
from cavendish_particle_tracks._calculate import depth, length, stereoshift


class StereoshiftDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent

        self.setWindowTitle("Stereoshift")

        self.f1 = Fiducial("Back fiducial view1")
        self.f2 = Fiducial("Back fiducial view2")
        self.b1 = Fiducial("Point view1")
        self.b2 = Fiducial("Point view2")

        # drop-down lists of fiducials
        self.cbf1 = QComboBox()
        self.cbf1.addItem("Front / Back")
        self.cbf1.addItem("Back / Front")
        self.cbf1.currentIndexChanged.connect(self._on_click_fiducial)

        # text boxes points
        self.txf1 = QLabel(self)
        self.txf2 = QLabel(self)
        self.txb1 = QLabel(self)
        self.txb2 = QLabel(self)

        self.txboxes = [self.txf1, self.txf2, self.txb1, self.txb2]
        for txt in self.txboxes:
            txt.setMinimumWidth(200)

        # text boxes results
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
        for txt in self.txboxes:
            txt.setMinimumWidth(200)

        bss = QPushButton("Calculate")
        bss.clicked.connect(self._on_click_calculate)

        bap = QPushButton("Save to table")
        bap.clicked.connect(self._on_click_save_to_table)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.buttonBox.clicked.connect(self.cancel)

        lviewf1 = QLabel("View 1")
        lviewf2 = QLabel("View 2")
        lviewb1 = QLabel("View 1")
        lviewb2 = QLabel("View 2")

        self.label_stereoshift = QLabel(
            "Stereo shift (shift_p/shift_f = depth_p/depth_f)"
        )

        # layout
        self.setLayout(QGridLayout())
        self.layout().addWidget(
            QLabel("Select Reference / Fiducial"), 0, 0, 1, 2
        )
        self.layout().addWidget(QLabel("Fiducial coordinates"), 1, 0, 1, 2)
        self.layout().addWidget(self.cbf1, 0, 2)
        for i, widget in enumerate([lviewf1, self.txf1, lviewf2, self.txf2]):
            self.layout().addWidget(widget, i // 2 + 2, i % 2 + 1)
        self.layout().addWidget(QLabel("Point coordinates"), 4, 0, 1, 2)
        for i, widget in enumerate([lviewb1, self.txb1, lviewb2, self.txb2]):
            self.layout().addWidget(widget, i // 2 + 5, i % 2 + 1)

        self.layout().addWidget(bss, 7, 0, 1, 3)

        self.layout().addWidget(
            self.label_stereoshift,
            8,
            0,
            1,
            3,
        )
        # self.layout().addWidget(self.table, 9, 0, 1, 3)
        self.layout().addWidget(QLabel("Fiducial shift"), 9, 1)
        self.layout().addWidget(self.tshift_fiducial, 9, 2)
        self.layout().addWidget(QLabel("Point shift"), 10, 1)
        self.layout().addWidget(self.tshift_point, 10, 2)
        self.layout().addWidget(QLabel("Ratio"), 11, 1)
        self.layout().addWidget(self.tstereoshift, 11, 2)
        self.layout().addWidget(QLabel("Point depth (cm)"), 12, 1)
        self.layout().addWidget(self.tdepth, 12, 2)
        self.layout().addWidget(bap, 13, 0, 1, 3)
        self.layout().addWidget(self.buttonBox, 14, 0, 1, 3)

        # Setup points layer
        self.cal_layer = self._setup_stereoshift_layer()

        # Stereoshift related parameters
        self.shift_fiducial = 0.0
        self.shift_point = 0.0
        self.point_stereoshift = 0.0
        self.point_depth = -1.0
        self.spoints = []

    def _setup_stereoshift_layer(self):
        # add the points
        points = np.array(
            [[100, 100], [200, 300], [333, 111], [400, 350], [500, 150]]
        )

        labels = [
            "Reference (Front)",
            self.f1.name,
            self.f2.name,
            self.b1.name,
            self.b2.name,
        ]
        colors = ["green", "blue", "blue", "red", "red"]

        text = {
            "string": labels,
            "size": 20,
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
            edge_width=7,
            edge_width_is_relative=False,
            edge_color=colors,
            face_color=colors,
        )

        # set the edge_color mode to colormap
        # points_layer.edge_color_mode = 'colormap'

        return points_layer

    def _on_click_fiducial(self) -> None:
        """When fiducial is selected, update the name of the fiducial and the points text"""

        if self.cbf1.currentIndex() == 0:
            self.f1.name = "Back fiducial view1"
            self.f2.name = "Back fiducial view2"
            self.cal_layer.text.string.array[0] = "Reference (Front)"
            self.cal_layer.text.string.array[1] = self.f1.name
            self.cal_layer.text.string.array[2] = self.f2.name
            self.label_stereoshift.setText(
                "Stereo shift (shift_p/shift_f = depth_p/depth_f)"
            )

        if self.cbf1.currentIndex() == 1:
            self.f1.name = "Front fiducial view1"
            self.f2.name = "Front fiducial view2"
            self.cal_layer.text.string.array[0] = "Reference (Back)"
            self.cal_layer.text.string.array[1] = self.f1.name
            self.cal_layer.text.string.array[2] = self.f2.name
            self.label_stereoshift.setText(
                "Stereo shift (shift_p/shift_f = 1 - depth_p/depth_f)"
            )

        self.cal_layer.refresh()

    def _on_click_calculate(self) -> None:
        """When 'Calculate' button is clicked, calculate stereoshift and populate table"""

        # Add points coords to corresponding text box
        points = [self.f1, self.f2, self.b1, self.b2]
        for i in range(len(points)):
            points[i].x, points[i].y = self.cal_layer.data[i + 1]
            self.txboxes[i].setText(str(points[i].xy))

        # Calculate stereoshift and depth
        self.shift_fiducial = length(self.f1.xy, self.f2.xy)
        self.shift_point = length(self.b1.xy, self.b2.xy)
        self.point_stereoshift = stereoshift(
            self.f1.xy, self.f2.xy, self.b1.xy, self.b2.xy
        )
        self.point_depth = depth(
            self.f1, self.f2, self.b1, self.b2, reverse=self.cbf1.currentIndex
        )
        self.spoints = self.cal_layer.data[1:]

        # Populate the table
        self.tshift_fiducial.setText(str(self.shift_fiducial))
        self.tshift_point.setText(str(self.shift_point))
        self.tstereoshift.setText(str(self.point_stereoshift))
        self.tdepth.setText(str(self.point_depth))

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
        self.parent.viewer.layers.select_previous()
        self.parent.viewer.layers.remove(self.cal_layer)
        return super().accept()
