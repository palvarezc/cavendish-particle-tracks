"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""

import napari
import numpy as np
from qtpy.QtWidgets import (
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cavendish_particle_tracks._calculate import length, radius

EXPECTED_PARTICLES = ["New particle", "Σ+", "Σ-", "Λ0"]


class ParticleTracksWidget(QWidget):
    """Widget containing a simple table of points and track radii per image."""

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__()
        self.viewer = napari_viewer

        self.cb = QComboBox()
        self.cb.addItems(EXPECTED_PARTICLES)
        self.cb.setCurrentIndex(0)
        self.cb.currentIndexChanged.connect(self._on_click_new_particle)

        # define QtWidgets
        cal = QPushButton("Calculate radius")
        lgth = QPushButton("Calculate length")
        stsh = QPushButton("Calculate stereoshift")
        self.table = self._set_up_table()

        # connect callbacks
        cal.clicked.connect(self._on_click_calculate)
        lgth.clicked.connect(self._on_click_length)
        stsh.clicked.connect(self._on_click_stereoshift)
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

    def _get_selected_points(self) -> np.array:
        """Returns array of selected points in the viewer"""

        # Filtering selected points
        points_layers = [
            layer for layer in self.viewer.layers if layer.name == "Points"
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
