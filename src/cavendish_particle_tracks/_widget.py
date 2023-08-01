"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""

import napari
import numpy as np
from qtpy.QtWidgets import QPushButton, QTableWidget, QVBoxLayout, QWidget, QTableWidgetItem


class ParticleTracksWidget(QWidget):
    """Widget containing a simple table of points and track radii per image."""

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__()
        self.viewer = napari_viewer

        # define QtWidgets
        cal = QPushButton("Calculate radius")
        ptc = QPushButton("New particle")
        self.table = self._set_up_table()

        # connect callbacks
        cal.clicked.connect(self._on_click_calculate)
        ptc.clicked.connect(self._on_click_new_particle)
        # TODO: find which of thsese works
        # https://napari.org/stable/gallery/custom_mouse_functions.html
        # self.viewer.mouse_press.callbacks.connect(self._on_mouse_press)
        # self.viewer.events.mouse_press(self._on_mouse_click)

        # layout
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.table)
        self.layout().addWidget(cal)
        self.layout().addWidget(ptc)

    def _set_up_table(self) -> QTableWidget:
        """Initial setup of the QTableWidget with one row and columns for each
        point and the calculated radius.
        """
        out = QTableWidget(0, 4)
        out.setHorizontalHeaderLabels(["1", "2", "3", "radius"])
        return out

    def _on_mouse_press(self) -> None:
        """When the mouse is clicked, record the cursor position."""
        print("clicked!")
        # layer.world_to_data(viewer.cursor.position)

    def _on_click_calculate(self) -> None:
        """When the 'Calculate radius' button is clicked, calculate the radius
        for the currently selected table row.
        """
        print("calculating radius!")

    def _on_click_new_particle(self) -> None:
        """When the 'New particle' button is clicked, append a new blank row to
        the table and select the first cell ready to recieve the first point.
        """
        print("napari has", len(self.viewer.layers), "layers")

        #Filtering selected points
        points_layers = [layer for layer in self.viewer.layers if layer.name=="Points"]
        selected_points = np.array([points_layers[0].data[i] for i in points_layers[0].selected_data])
        print("Adding points to the table: ", selected_points)

        #Forcing only 3 points for the moment
        if not len(selected_points)==3:
            print("Can only process 3-point particles, try again.")
            return 

        #Adding points to the table
        self.table.insertRow(self.table.rowCount())

        for i in range(3):
            # This is not optimal for the radius calculation
            point = selected_points[i]
            point_text = "["+str(point[0])+", "+str(point[1])+"]"
            self.table.setItem(self.table.rowCount()-1 , i, QTableWidgetItem(point_text)) 
