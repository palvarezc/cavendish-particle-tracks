from typing import List

import numpy as np
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from cavendish_particle_tracks._analysis import (
    FIDUCIAL_BACK,
    Fiducial,
)
from cavendish_particle_tracks._calculate import depth, length, stereoshift


class StereoshiftDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent

        self.setWindowTitle("Stereoshift")

        self.f1 = Fiducial()
        self.f2 = Fiducial()
        self.b1 = Fiducial()
        self.b2 = Fiducial()

        # drop-down lists of fiducials
        self.cbf1 = QComboBox()
        self.cbf1.addItems(FIDUCIAL_BACK)
        self.cbf1.setCurrentIndex(-1)
        self.cbf1.currentIndexChanged.connect(self._on_click_fiducial)

        # text boxes
        self.txf1 = QLabel(self)
        self.txf2 = QLabel(self)
        self.txb1 = QLabel(self)
        self.txb2 = QLabel(self)

        self.txboxes = [self.txf1, self.txf2, self.txb1, self.txb2]
        for txt in self.txboxes:
            txt.setMinimumWidth(200)

        # add coords buttons
        self.cof1 = QPushButton("Add")
        self.cof2 = QPushButton("Add")
        self.cob1 = QPushButton("Add")
        self.cob2 = QPushButton("Add")
        self.cof1.clicked.connect(self._on_click_add_coords_f1)
        self.cof2.clicked.connect(self._on_click_add_coords_f2)
        self.cob1.clicked.connect(self._on_click_add_coords_b1)
        self.cob2.clicked.connect(self._on_click_add_coords_b2)

        bss = QPushButton("Calculate stereo shift")
        bss.clicked.connect(self._on_click_stereoshift)

        self.table = QTableWidget(1, 4)
        self.table.setHorizontalHeaderLabels(
            ["Fiducial shift", "Point shift", "ratio", "Point depth [cm]"]
        )

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        lviewf1 = QLabel("View 1")
        lviewf2 = QLabel("View 2")
        lviewb1 = QLabel("View 1")
        lviewb2 = QLabel("View 2")

        # layout
        self.setLayout(QGridLayout())
        self.layout().addWidget(QLabel("Select fiducial mark"), 0, 0, 1, 2)
        self.layout().addWidget(self.cbf1, 0, 2)
        for i, widget in enumerate(
            [lviewf1, self.txf1, self.cof1, lviewf2, self.txf2, self.cof2]
        ):
            self.layout().addWidget(widget, i // 3 + 1, i % 3)
        self.layout().addWidget(QLabel("Select point"), 3, 0, 1, 2)
        for i, widget in enumerate(
            [lviewb1, self.txb1, self.cob1, lviewb2, self.txb2, self.cob2]
        ):
            self.layout().addWidget(widget, i // 3 + 4, i % 3)

        self.layout().addWidget(bss, 6, 0, 1, 3)

        self.layout().addWidget(
            QLabel("Stereo shift (shift_p/shift_f = depth_p/depth_f)"),
            7,
            0,
            1,
            3,
        )
        self.layout().addWidget(self.table, 8, 0, 1, 3)

        self.layout().addWidget(self.buttonBox, 9, 0, 1, 3)

        self.cal_layer = self._setup_stereoshift_layer()

    def _on_click_fiducial(self) -> None:
        """When fiducial is selected, update the name of the fiducial in the points text"""

        self.cal_layer.text.string.array[1] = (
            self.cbf1.currentText() + " view1"
        )
        self.cal_layer.text.string.array[2] = (
            self.cbf1.currentText() + " view2"
        )
        self.cal_layer.refresh()

    def _on_click_add_coords_f1(self) -> None:
        """Add fiducial view1"""
        self.f1.name = self.cbf1.currentText()
        self.f1.x, self.f1.y = self._add_coords(0)

    def _on_click_add_coords_f2(self) -> None:
        """Add fiducial view2"""
        self.f2.name = self.cbf1.currentText()
        self.f2.x, self.f2.y = self._add_coords(1)

    def _on_click_add_coords_b1(self) -> None:
        """Add point view1"""
        self.b1.name = "Point"
        self.b1.x, self.b1.y = self._add_coords(2)

    def _on_click_add_coords_b2(self) -> None:
        """Add point view2"""
        self.b2.name = "Point"
        self.b2.x, self.b2.y = self._add_coords(3)

    def _add_coords(self, fiducial: int) -> List[float]:
        """When 'Add' is selected, the selected point is added to the corresponding text box"""

        selected_points = self.parent._get_selected_points(
            "Points_Stereoshift"
        )

        # Forcing only 1 points
        if len(selected_points) != 1:
            print("Select (only) one point.")
            return [-1.0e6, -1.0e6]

        textbox = self.txboxes[fiducial]
        textbox.setText(str(selected_points[0]))

        return selected_points[0]

    def _on_click_stereoshift(self) -> None:
        """When 'Calculate stereoshift' button is clicked, calculate stereoshift and populate table"""

        # Need something like this but a bit better
        if not (
            self.f1.name and self.f2.name and self.b1.name and self.b2.name
        ):
            print(
                "Add a fiducial and the point in two views to calcuate the magnification"
            )
            return

        self.table.setItem(
            0, 0, QTableWidgetItem(str(length(self.f1.xy, self.f2.xy)))
        )
        self.table.setItem(
            0, 1, QTableWidgetItem(str(length(self.b1.xy, self.b2.xy)))
        )
        self.table.setItem(
            0,
            2,
            QTableWidgetItem(
                str(
                    stereoshift(self.f1.xy, self.f2.xy, self.b1.xy, self.b2.xy)
                )
            ),
        )
        self.table.setItem(
            0,
            3,
            QTableWidgetItem(str(depth(self.f1, self.f2, self.b1, self.b2))),
        )

    def _setup_stereoshift_layer(self):
        # add the points
        points = np.array(
            [[100, 100], [200, 300], [333, 111], [400, 350], [500, 150]]
        )

        labels = [
            "Reference (Front)",
            "Back fiducial view1",
            "Back fiducial view2",
            "Point view1",
            "Point view2",
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

    def accept(self) -> None:
        """On accept propagate the depth information to the main window and remove the points_Stereoshift layer"""

        print("Propagating stereoshift to table.")
        # self.parent._apply_stereoshift()
        # TODO: this is a problem, the layer still exists... not sure how to remove it
        self.parent.viewer.layers.select_previous()
        self.parent.viewer.layers.remove(self.cal_layer)
        return super().accept()

    def reject(self) -> None:
        """On reject remove the points_Stereoshift layer"""

        # This is a problem, the layer still exists... not sure how to remove it
        self.parent.viewer.layers.select_previous()
        self.parent.viewer.layers.remove(self.cal_layer)
        return super().reject()
