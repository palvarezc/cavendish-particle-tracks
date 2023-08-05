"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""

from typing import List

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

from cavendish_particle_tracks._analysis import (
    EXPECTED_PARTICLES,
    FIDUCIAL_BACK,
    FIDUCIAL_FRONT,
    Fiducial,
    NewParticle,
)
from cavendish_particle_tracks._calculate import (
    length,
    magnification,
    radius,
)


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
        cal.clicked.connect(self._on_click_radius)
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

        # Data analysis
        # pre-commit told me to do this and it broke the tests!
        # self.data: List[NewParticle]
        self.data: List[NewParticle] = []
        # might not need this eventually
        self.mag_a = 1.0
        self.mag_b = 0.0

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

    def _on_click_radius(self) -> None:
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

        self.data[selected_rows[0].row()].rpoints = selected_points

        print("calculating radius!")

        # Calculate radius
        rad = radius(*selected_points)

        self.table.setItem(
            selected_rows[0].row(), 4, QTableWidgetItem(str(rad))
        )

        self.data[selected_rows[0].row()].radius = rad

        print("Modified particle ", selected_rows[0].row())
        print(self.data[selected_rows[0].row()])

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
        self.data[selected_rows[0].row()].dpoints = selected_points

        self.table.setItem(
            selected_rows[0].row(), 5, QTableWidgetItem(str(declen))
        )

        self.data[selected_rows[0].row()].decay_length = declen

        print("Modified particle ", selected_rows[0].row())
        print(self.data[selected_rows[0].row()])

    def _on_click_stereoshift(self) -> None:
        """When the 'Calculate stereoshift' button is clicked, calculate the stereoshift
        for the currently selected table row.
        """
        print("calculating stereoshift!")

    def _on_click_new_particle(self) -> None:
        """When the 'New particle' button is clicked, append a new blank row to
        the table and select the first cell ready to recieve the first point.
        """
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

        # add new particle to data
        np = NewParticle()
        np.Type = self.cb.currentText()
        self.data += [np]
        print(self.data[-1])
        self.cb.setCurrentIndex(0)

        # # napari notifications
        # napari.utils.notifications.show_info("I created a new particle")

    def _on_click_magnification(self) -> None:
        """When the 'Calculate magnification' button is clicked, open the magnification dialog"""

        dlg = MagnificationDialog(self)
        dlg.show()
        point = QPoint(self.pos().x() + self.width(), self.pos().y())
        dlg.move(point)

    def _apply_magnification(self, a: float, b: float) -> None:
        self.mag_a = a
        self.mag_b = b
        for particle in self.data:
            particle.mag_a = a
            particle.mag_b = b


class MagnificationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent

        self.setWindowTitle("Magnification")

        self.f1 = Fiducial()
        self.f2 = Fiducial()
        self.b1 = Fiducial()
        self.b2 = Fiducial()

        # drop-down lists of fiducials
        self.cbf1 = self._setup_dropdown_fiducials_combobox()
        self.cbf2 = self._setup_dropdown_fiducials_combobox()
        self.cbb1 = self._setup_dropdown_fiducials_combobox(back=True)
        self.cbb2 = self._setup_dropdown_fiducials_combobox(back=True)

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

        self.bmag = QPushButton("Calculate magnification")
        self.bmag.clicked.connect(self._on_click_magnification)

        self.table = QTableWidget(1, 2)
        self.table.setHorizontalHeaderLabels(["a", "b"])

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # layout
        self.setLayout(QGridLayout())
        self.layout().addWidget(
            QLabel("Select front fiducial marks"), 0, 0, 1, 3
        )
        for i, widget in enumerate(
            [self.cbf1, self.txf1, self.cof1, self.cbf2, self.txf2, self.cof2]
        ):
            self.layout().addWidget(widget, i // 3 + 1, i % 3)
        self.layout().addWidget(
            QLabel("Select back fiducial marks"), 3, 0, 1, 3
        )
        for i, widget in enumerate(
            [self.cbb1, self.txb1, self.cob1, self.cbb2, self.txb2, self.cob2]
        ):
            self.layout().addWidget(widget, i // 3 + 4, i % 3)

        self.layout().addWidget(self.bmag, 6, 0, 1, 3)

        self.layout().addWidget(
            QLabel("Magnification parameters (M = a + b z)"), 7, 0, 1, 3
        )
        self.layout().addWidget(self.table, 8, 0, 1, 3)

        self.layout().addWidget(self.buttonBox, 9, 0, 1, 3)

        self.cal_layer = self.parent.viewer.add_points(
            name="Points_Calibration"
        )

    def _setup_dropdown_fiducials_combobox(self, back=False):
        """Sets up a drop-down list of fiducials for the `back` or front (`back=False`)."""
        combobox = QComboBox()
        if back:
            combobox.addItems(FIDUCIAL_BACK.keys())
        else:
            combobox.addItems(FIDUCIAL_FRONT.keys())
        combobox.currentIndexChanged.connect(self._on_click_fiducial)
        return combobox

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
        self.f1.name = self.cbf1.currentText()
        self.f1.x, self.f2.y = self._add_coords(0)

    def _on_click_add_coords_f2(self) -> None:
        """Add first front fiducial"""
        self.f2.name = self.cbf2.currentText()
        self.f2.x, self.f2.y = self._add_coords(1)

    def _on_click_add_coords_b1(self) -> None:
        """Add first front fiducial"""
        self.b1.name = self.cbb1.currentText()
        self.b1.x, self.b1.y = self._add_coords(2)

    def _on_click_add_coords_b2(self) -> None:
        """Add first front fiducial"""
        self.b2.name = self.cbb2.currentText()
        self.b2.x, self.b2.y = self._add_coords(3)

    def _add_coords(self, fiducial: int) -> List[float]:
        """When 'Add' is selected, the selected point is added to the corresponding fiducial text box"""

        selected_points = self.parent._get_selected_points(
            "Points_Calibration"
        )

        # Forcing only 1 points
        if len(selected_points) != 1:
            print("Select (only) one point to add fiducial.")
            return [-1.0e6, -1.0e6]

        textbox = self.txboxes[fiducial]
        textbox.setText(str(selected_points[0]))

        return selected_points[0]

    def _on_click_magnification(self) -> None:
        """When 'Calculate magnification' button is clicked, calculate magnification and populate table"""

        # Need something like this but a bit better
        if not (
            self.f1.name and self.f2.name and self.b1.name and self.b2.name
        ):
            print("Select fiducials to calcuate the magnification")
            return

        self.a, self.b = magnification(self.f1, self.f2, self.b1, self.b2)

        self.table.setItem(0, 0, QTableWidgetItem(str(self.a)))
        self.table.setItem(0, 1, QTableWidgetItem(str(self.b)))

    def accept(self) -> None:
        """On accept propagate the calibration information to the main window and remove the points_Calibration layer"""

        print("Propagating magnification to table.")
        self.parent._apply_magnification(self.a, self.b)
        # This is a problem, the layer still exists... not sure how to remove it
        self.parent.viewer.layers.select_previous()
        self.parent.viewer.layers.remove(self.cal_layer)
        return super().accept()

    def reject(self) -> None:
        """On reject remove the points_Calibration layer"""

        # This is a problem, the layer still exists... not sure how to remove it
        self.parent.viewer.layers.select_previous()
        self.parent.viewer.layers.remove(self.cal_layer)
        return super().reject()
