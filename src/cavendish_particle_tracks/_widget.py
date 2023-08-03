"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""

import napari
import numpy as np
from qtpy.QtCore import QPoint
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cavendish_particle_tracks._calculate import length, radius

EXPECTED_PARTICLES = ["New particle", "Σ+", "Σ-", "Λ0"]
FIDUCIAL_FRONT = {
    "C’": [0.0, 0.0, 0.0],
    "F’": [14.97, -8.67, 0.0],
    "B’": [15.00, 8.66, 0.0],
    "D’": [29.91, -0.07, 0.0],
}  # cm
FIDUCIAL_BACK = {
    "C": [-0.02, 0.01, 31.6],
    "F": [14.95, -8.63, 31.6],
    "B": [14.92, 8.67, 31.6],
    "D": [29.90, 0.02, 31.6],
    "E": [-14.96, -8.62, 31.6],
    "A": [-15.00, 8.68, 31.6],
}  # cm


class ParticleTracksWidget(QWidget):
    """Widget containing a simple table of points and track radii per image."""

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__()
        self.viewer = napari_viewer

        # define QtWidgets
        self.cb = QComboBox()
        self.cb.addItems(EXPECTED_PARTICLES)
        self.cb.setCurrentIndex(0)
        self.cb.currentIndexChanged.connect(self._on_click_new_particle)
        cal = QPushButton("Calculate radius")
        lgth = QPushButton("Calculate length")
        stsh = QPushButton("Calculate stereoshift")
        self.table = self._set_up_table()
        mag = QPushButton("Calculate magnification")

        # connect callbacks
        cal.clicked.connect(self._on_click_calculate)
        lgth.clicked.connect(self._on_click_length)
        stsh.clicked.connect(self._on_click_stereoshift)
        mag.clicked.connect(self._on_click_magnification)
        # TODO: find which of thsese works
        # https://napari.org/stable/gallery/custom_mouse_functions.html
        # self.viewer.mouse_press.callbacks.connect(self._on_mouse_press)
        # self.viewer.events.mouse_press(self._on_mouse_click)

        # layout
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.cb)
        self.layout().addWidget(cal)
        self.layout().addWidget(lgth)
        self.layout().addWidget(stsh)
        self.layout().addWidget(self.table)
        self.layout().addWidget(mag)

    def _get_selected_points(self, layer_name="Points") -> np.array:
        """Returns array of selected points in the viewer"""

        # Filtering selected points
        points_layers = [
            layer for layer in self.viewer.layers if layer.name == layer_name
        ]
        selected_points = np.array(
            [points_layers[0].data[i] for i in points_layers[0].selected_data]
        )

        return selected_points

    def _get_selected_row(self) -> np.array:
        """Returns index of the (first) selected row in the table"""

        select = self.table.selectionModel()
        rows = select.selectedRows()

        return rows

    def _set_up_table(self) -> QTableWidget:
        """Initial setup of the QTableWidget with one row and columns for each
        point and the calculated radius.
        """
        out = QTableWidget(0, 6)
        out.setHorizontalHeaderLabels(
            ["Type", "1", "2", "3", "radius", "decay length"]
        )
        return out

    def _on_mouse_press(self) -> None:
        """When the mouse is clicked, record the cursor position."""
        print("clicked!")
        # layer.world_to_data(viewer.cursor.position)

    def _on_click_calculate(self) -> None:
        """When the 'Calculate radius' button is clicked, calculate the radius
        for the currently selected points and assign it to the currently selected table row.
        """

        selected_points = self._get_selected_points()

        # Forcing only 3 points
        if len(selected_points) != 3:
            print("Select (only) three points to calculate the decay radius.")
            return

        selected_rows = self._get_selected_row()

        if len(selected_rows) != 1:
            print(
                "Select (only) one particle from the table to calculate the radius."
            )

        print("Adding points to the table: ", selected_points)

        # Assigns the points and radius to the (first) selected row
        for i in range(3):
            point = selected_points[i]
            self.table.setItem(
                selected_rows[0].row(), i + 1, QTableWidgetItem(str(point))
            )

        print("calculating radius!")

        # Calculate radius
        rad = radius(*selected_points)

        self.table.setItem(
            selected_rows[0].row(), 4, QTableWidgetItem(str(rad))
        )

    def _on_click_length(self) -> None:
        """When the 'Calculate length' button is clicked, calculate the decay length
        for the currently selected table row.
        """

        selected_points = self._get_selected_points()

        # Forcing only 2 points
        if len(selected_points) != 2:
            print("Select (only) two points to calculate the decay length.")
            return

        selected_rows = self._get_selected_row()

        if len(selected_rows) != 1:
            print(
                "Select (only) one particle from the table to calculate the decay length."
            )

        print("calculating decay length!")
        declen = length(*selected_points)

        self.table.setItem(
            selected_rows[0].row(), 5, QTableWidgetItem(str(declen))
        )

    def _on_click_stereoshift(self) -> None:
        """When the 'Calculate stereoshift' button is clicked, calculate the stereoshift
        for the currently selected table row.
        """
        print("calculating stereoshift!")

    def _on_click_new_particle(self) -> None:
        """When the 'New particle' button is clicked, append a new blank row to
        the table and select the first cell ready to recieve the first point.
        """
        print("napari has", len(self.viewer.layers), "layers")

        if self.cb.currentIndex() < 1:
            return

        # add particle (== new row) to the table and select it
        self.table.insertRow(self.table.rowCount())
        self.table.selectRow(self.table.rowCount() - 1)
        self.table.setItem(
            self.table.rowCount() - 1,
            0,
            QTableWidgetItem(self.cb.currentText()),
        )
        self.cb.setCurrentIndex(0)

    def _on_click_magnification(self) -> None:
        """When the 'Calculate magnification' button is clicked, open the magnification dialog"""

        dlg = MagnificationDialog(self)
        dlg.show()
        point = QPoint(self.pos().x() + self.width(), self.pos().y())
        dlg.move(point)


class MagnificationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent

        self.setWindowTitle("Magnification")

        # drop-down lists of fiducials
        self.cbf1 = QComboBox()
        self.cbf2 = QComboBox()
        self.cbf1.addItems(FIDUCIAL_FRONT.keys())
        self.cbf2.addItems(FIDUCIAL_FRONT.keys())
        self.cbb1 = QComboBox()
        self.cbb2 = QComboBox()
        self.cbb1.addItems(FIDUCIAL_BACK.keys())
        self.cbb2.addItems(FIDUCIAL_BACK.keys())

        self.cbf1.currentIndexChanged.connect(self._on_click_fiducial)
        self.cbf2.currentIndexChanged.connect(self._on_click_fiducial)
        self.cbb1.currentIndexChanged.connect(self._on_click_fiducial)
        self.cbb2.currentIndexChanged.connect(self._on_click_fiducial)

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

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # layout
        self.setLayout(QGridLayout())
        self.layout().addWidget(
            QLabel("Select front fiducial marks"), 0, 0, 1, 3
        )
        self.layout().addWidget(self.cbf1, 1, 0)
        self.layout().addWidget(self.txf1, 1, 1)
        self.layout().addWidget(self.cof1, 1, 2)
        self.layout().addWidget(self.cbf2, 2, 0)
        self.layout().addWidget(self.txf2, 2, 1)
        self.layout().addWidget(self.cof2, 2, 2)
        self.layout().addWidget(
            QLabel("Select back fiducial marks"), 3, 0, 1, 3
        )
        self.layout().addWidget(self.cbb1, 4, 0)
        self.layout().addWidget(self.txb1, 4, 1)
        self.layout().addWidget(self.cob1, 4, 2)
        self.layout().addWidget(self.cbb2, 5, 0)
        self.layout().addWidget(self.txb2, 5, 1)
        self.layout().addWidget(self.cob2, 5, 2)
        self.layout().addWidget(self.buttonBox, 6, 0, 1, 3)

        self.cal_layer = self.parent.viewer.add_points(
            name="Points_Calibration"
        )

    def _on_click_fiducial(self) -> None:
        """When fiducial is selected, we locate ourselves in the Points_calibration layer and select option 'Add point'"""

        # Would be cool if we could wait for a click here and add that as the selected fiducial, but no clue how to do that yet
        # layers  = [
        #     layer for layer in self.parent.viewer.layers if layer.name == "Points_Calibration"
        # ]
        # layer = layers[0]
        # @layer.mouse_drag_callbacks.append
        # def callback(layer, event):  # (0,0) is the center of the upper left pixel
        #     print(self.parent.viewer.cursor.position)

        print("Add fiducial point")

    def _on_click_add_coords_f1(self) -> None:
        """Add first front fiducial"""
        return self._on_click_add_coords(0)

    def _on_click_add_coords_f2(self) -> None:
        """Add first front fiducial"""
        return self._on_click_add_coords(1)

    def _on_click_add_coords_b1(self) -> None:
        """Add first front fiducial"""
        return self._on_click_add_coords(2)

    def _on_click_add_coords_b2(self) -> None:
        """Add first front fiducial"""
        return self._on_click_add_coords(3)

    def _on_click_add_coords(self, fiducial: int) -> None:
        """When 'Add' is selected, the selected point is added to the corresponding fiducial text box"""
        textbox = self.txboxes[fiducial]

        selected_points = self.parent._get_selected_points(
            "Points_Calibration"
        )

        # Forcing only 1 points
        if len(selected_points) != 1:
            print("Select (only) one point to add fiducial.")
            return

        textbox.setText(str(selected_points[0]))

    def accept(self) -> None:
        """On accept propagate the calibration information to the main window and remove the points_Calibration layer"""

        # This is a problem, the layer still exists... not sure how to remove it
        self.parent.viewer.layers.remove(self.cal_layer)
        return super().accept()

    def reject(self) -> None:
        """On reject remove the points_Calibration layer"""

        # This is a problem, the layer still exists... not sure how to remove it
        self.parent.viewer.layers.remove(self.cal_layer)
        return super().reject()
