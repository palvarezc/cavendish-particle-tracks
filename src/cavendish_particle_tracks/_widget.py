"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""

import napari
import numpy as np
from qtpy.QtWidgets import (
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cavendish_particle_tracks._calculate import radius


class ParticleTracksWidget(QWidget):
    """Widget containing a simple table of points and track radii per image."""

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__()
        self.viewer = napari_viewer

        # define QtWidgets
        cal = QPushButton("Calculate radius")
        lgth = QPushButton("Calculate length")
        stsh = QPushButton("Calculate stereoshift")
        ptc = QPushButton("New particle")
        self.table = self._set_up_table()

        # connect callbacks
        cal.clicked.connect(self._on_click_calculate)
        lgth.clicked.connect(self._on_click_length)
        stsh.clicked.connect(self._on_click_stereoshift)
        ptc.clicked.connect(self._on_click_new_particle)
        # TODO: find which of thsese works
        # https://napari.org/stable/gallery/custom_mouse_functions.html
        # self.viewer.mouse_press.callbacks.connect(self._on_mouse_press)
        # self.viewer.events.mouse_press(self._on_mouse_click)

        # layout
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(ptc)
        self.layout().addWidget(cal)
        self.layout().addWidget(lgth)
        self.layout().addWidget(stsh)
        self.layout().addWidget(self.table)

    def _set_up_table(self) -> QTableWidget:
        """Initial setup of the QTableWidget with one row and columns for each
        point and the calculated radius.
        """
        out = QTableWidget(0, 5)
        out.setHorizontalHeaderLabels(["Type", "1", "2", "3", "radius"])
        return out

    def _on_mouse_press(self) -> None:
        """When the mouse is clicked, record the cursor position."""
        print("clicked!")
        # layer.world_to_data(viewer.cursor.position)

    def _on_click_calculate(self) -> None:
        """When the 'Calculate radius' button is clicked, calculate the radius
        for the currently selected points and assign it to the currently selected table row.
        """

        # Filtering selected points
        points_layers = [
            layer for layer in self.viewer.layers if layer.name == "Points"
        ]
        selected_points = np.array(
            [points_layers[0].data[i] for i in points_layers[0].selected_data]
        )
        print("Adding points to the table: ", selected_points)

        # Forcing only 3 points for the moment
        if len(selected_points) != 3:
            print("Can only process 3-point particles, try again.")
            return

        print("calculating radius!")

        # Calculate radius
        rad = radius(*selected_points)

        # Assigns the points and radius to the (first) selected row
        select = self.table.selectionModel()
        rows = select.selectedRows()
        if len(rows) != 1:
            print(
                "Select (only) one particle from the table to calculate the radius."
            )

        for i in range(3):
            point = selected_points[i]
            "[" + str(point[0]) + ", " + str(point[1]) + "]"
            self.table.setItem(
                rows[0].row(), i + 1, QTableWidgetItem(str(point))
            )

        self.table.setItem(rows[0].row(), 4, QTableWidgetItem(str(rad)))

    def _on_click_length(self) -> None:
        """When the 'Calculate length' button is clicked, calculate the length
        for the currently selected table row.
        """
        print("calculating legth!")

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

        # add particle (== new row) to the table and select it (for the moment all Sigma+)
        self.table.insertRow(self.table.rowCount())
        self.table.selectRow(self.table.rowCount() - 1)
        self.table.setItem(
            self.table.rowCount() - 1, 0, QTableWidgetItem("Sigma+")
        )
