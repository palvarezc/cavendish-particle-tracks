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
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cavendish_particle_tracks._analysis import (
    EXPECTED_PARTICLES,
    NewParticle,
)
from cavendish_particle_tracks._calculate import (
    length,
    radius,
)
from cavendish_particle_tracks._magnification_dialog import MagnificationDialog


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
        self.mag = QPushButton("Calculate magnification")

        # connect callbacks
        cal.clicked.connect(self._on_click_radius)
        lgth.clicked.connect(self._on_click_length)
        stsh.clicked.connect(self._on_click_stereoshift)
        self.mag.clicked.connect(self._on_click_magnification)
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
        self.layout().addWidget(self.mag)

        # Data analysis
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
        np = NewParticle()
        columns = np.__dict__.keys()
        out = QTableWidget(0, len(columns))
        out.setHorizontalHeaderLabels(
            # ["Type", "1", "2", "3", "radius", "decay length"]
            columns
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
        np.Name = self.cb.currentText()
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
            particle.magnification_a = a
            particle.magnification_b = b
